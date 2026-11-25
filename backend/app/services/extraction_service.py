import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.job import JobOpportunity
from app.models.company import Company
from app.database.session import SessionLocal
from app.scraper.detail_extractor import DetailExtractor
from app.scraper.event_manager import EventManager

logger = logging.getLogger("hav_scrap")


class ExtractionService:
    """
    Coordinates deep job detail and salary extraction background tasks,
    telemetry state, and persistent queries.
    """

    def __init__(self):
        self.is_running: bool = False
        self._current_task: Optional[asyncio.Task] = None
        self._extractor: Optional[DetailExtractor] = None
        self._pause_event = asyncio.Event()
        self._pause_event.set()
        self._stop_requested = False
        self._status = "IDLE"
        self._last_error = None
        self._started_at = None
        self._completed_at = None

    def get_status(self) -> Dict[str, Any]:
        """
        Returns live extraction progress metrics.
        """
        with SessionLocal() as db:
            total_jobs = db.execute(select(func.count(JobOpportunity.id))).scalar() or 0
            extracted_jobs = db.execute(
                select(func.count(JobOpportunity.id)).where(JobOpportunity.extraction_status == "EXTRACTED")
            ).scalar() or 0
            failed_jobs = db.execute(
                select(func.count(JobOpportunity.id)).where(JobOpportunity.extraction_status == "FAILED")
            ).scalar() or 0
            pending_jobs = total_jobs - (extracted_jobs + failed_jobs)
            with_salary = db.execute(
                select(func.count(JobOpportunity.id)).where(JobOpportunity.salary_lpa.is_not(None))
            ).scalar() or 0
            with_stipend = db.execute(
                select(func.count(JobOpportunity.id)).where(JobOpportunity.stipend_amount.is_not(None))
            ).scalar() or 0

        extractor_stats = self._extractor.get_summary() if self._extractor else {}

        return {
            "status": self._status,
            "is_running": self.is_running,
            "total_postings": total_jobs,
            "postings_extracted": extracted_jobs,
            "postings_failed": failed_jobs,
            "postings_pending": max(0, pending_jobs),
            "salary_records_found": with_salary,
            "stipend_records_found": with_stipend,
            "current_run_summary": extractor_stats,
            "started_at": self._started_at,
            "completed_at": self._completed_at,
            "last_error": self._last_error,
        }

    async def start(
        self,
        force_reextract: bool = False,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Commences detailed extraction in the background.
        """
        if self.is_running:
            return {"success": False, "message": "Extraction task is already running."}

        self.is_running = True
        self._status = "RUNNING"
        self._stop_requested = False
        self._pause_event.set()
        self._last_error = None
        self._started_at = datetime.utcnow().isoformat() + "Z"
        self._completed_at = None

        self._extractor = DetailExtractor(
            checkpoint_fn=self._checkpoint,
            event_publisher=self._publish_event,
        )

        self._current_task = asyncio.create_task(
            self._run_extraction_task(force_reextract, limit)
        )

        return {"success": True, "message": "Detailed extraction task started."}

    async def stop(self) -> Dict[str, Any]:
        """
        Signals the active extraction runner to stop safely.
        """
        if not self.is_running:
            return {"success": False, "message": "No active extraction task to stop."}

        self._stop_requested = True
        self._pause_event.set()  # Unpause if holding
        self._status = "STOPPING"
        return {"success": True, "message": "Extraction stop instruction delivered."}

    async def _checkpoint(self, stage: str):
        if self._stop_requested:
            raise asyncio.CancelledError("Detailed extraction stopped by operator.")
        if not self._pause_event.is_set():
            await self._pause_event.wait()
        if self._stop_requested:
            raise asyncio.CancelledError("Detailed extraction stopped by operator.")

    async def _publish_event(self, event_type: str, data: Dict[str, Any]):
        logger.debug(f"Extraction SSE Event: {event_type} - {data}")

    async def _run_extraction_task(self, force_reextract: bool, limit: Optional[int]):
        try:
            logger.info("Background extraction loop running...")
            summary = await self._extractor.execute_extraction(
                force_reextract=force_reextract,
                limit=limit
            )
            self._status = "COMPLETED"
            self._completed_at = datetime.utcnow().isoformat() + "Z"
            logger.info(f"Detailed extraction task completed: {summary}")
        except asyncio.CancelledError:
            self._status = "CANCELLED"
            logger.warning("Detailed extraction task cancelled.")
        except Exception as e:
            self._status = "ERROR"
            self._last_error = str(e)
            logger.error(f"Error during deep extraction run: {str(e)}", exc_info=True)
        finally:
            self.is_running = False

    @staticmethod
    def get_results(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Queries extracted job details with compensation breakdowns.
        """
        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        offset = (page - 1) * page_size

        query = select(JobOpportunity).join(Company)
        if status:
            query = query.where(JobOpportunity.extraction_status == status.upper())

        total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0
        jobs = db.execute(
            query.order_by(JobOpportunity.updated_at.desc()).offset(offset).limit(page_size)
        ).scalars().all()

        items = []
        for j in jobs:
            items.append({
                "id": j.id,
                "company_name": j.company.company_name if j.company else "Unknown",
                "job_title": j.job_title,
                "job_role": j.job_role,
                "job_description": (j.job_description[:200] + "...") if j.job_description else None,
                "original_salary_text": j.original_salary_text,
                "salary_lpa": j.salary_lpa,
                "minimum_ctc": j.minimum_ctc,
                "maximum_ctc": j.maximum_ctc,
                "fixed_ctc": j.fixed_ctc,
                "variable_ctc": j.variable_ctc,
                "joining_bonus": j.joining_bonus,
                "stipend_amount": j.stipend_amount,
                "stipend_period": j.stipend_period,
                "annualized_equivalent": j.annualized_equivalent,
                "work_mode": j.work_mode,
                "location": j.location,
                "minimum_cgpa": j.minimum_cgpa,
                "eligible_branches": j.eligible_branches,
                "backlog_criteria": j.backlog_criteria,
                "batch": j.batch,
                "application_deadline": j.application_deadline.isoformat() if j.application_deadline else None,
                "source_url": j.source_url,
                "extraction_status": j.extraction_status or "PENDING",
                "last_verified_at": j.last_verified_at.isoformat() if j.last_verified_at else None,
            })

        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        }


extraction_service = ExtractionService()

