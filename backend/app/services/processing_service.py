import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session

from app.models.job import JobOpportunity
from app.models.company import Company
from app.database.session import SessionLocal
from app.processors.data_cleaner import DataCleaner
from app.processors.data_normalizer import DataNormalizer
from app.processors.salary_converter import SalaryConverter
from app.processors.data_validator import DataValidator
from app.processors.quality_analyzer import QualityAnalyzer

logger = logging.getLogger("hav_scrap")


class ProcessingService:
    """
    Orchestrates the repeatable end-to-end data processing, normalization,
    validation, and quality auditing pipeline.
    """

    def __init__(self):
        self.is_running: bool = False
        self._current_task: Optional[asyncio.Task] = None
        self._status: str = "IDLE"
        self._progress: float = 0.0
        self._records_processed: int = 0
        self._total_records: int = 0
        self._last_error: Optional[str] = None
        self._started_at: Optional[str] = None
        self._completed_at: Optional[str] = None

    def get_status(self) -> Dict[str, Any]:
        """
        Retrieves current processing pipeline status and runtime metrics.
        """
        return {
            "status": self._status,
            "is_running": self.is_running,
            "progress_percentage": round(self._progress, 1),
            "records_processed": self._records_processed,
            "total_records": self._total_records,
            "started_at": self._started_at,
            "completed_at": self._completed_at,
            "last_error": self._last_error,
        }

    async def start(self) -> Dict[str, Any]:
        """
        Spawns the background data processing task.
        """
        if self.is_running:
            return {"success": False, "message": "Data processing pipeline is already running."}

        self.is_running = True
        self._status = "RUNNING"
        self._progress = 0.0
        self._records_processed = 0
        self._last_error = None
        self._started_at = datetime.utcnow().isoformat() + "Z"
        self._completed_at = None

        self._current_task = asyncio.create_task(self._execute_pipeline())
        return {"success": True, "message": "Data processing pipeline commenced successfully."}

    async def _execute_pipeline(self):
        """
        Iterates over all existing records in SQLite and applies
        cleaning, normalizer, salary converter, and validator.
        Guaranteed to be 100% idempotent and non-destructive.
        """
        logger.info("Commencing full data cleaning, normalization and validation pipeline...")
        try:
            with SessionLocal() as db:
                jobs = db.execute(select(JobOpportunity).order_by(JobOpportunity.id.asc())).scalars().all()
                self._total_records = len(jobs)

            if self._total_records == 0:
                self._status = "COMPLETED"
                self._progress = 100.0
                self._completed_at = datetime.utcnow().isoformat() + "Z"
                self.is_running = False
                logger.info("Pipeline completed: zero records pending.")
                return

            # Batch process in manageable transactions
            batch_size = 50
            for offset in range(0, self._total_records, batch_size):
                with SessionLocal() as db:
                    batch_jobs = db.execute(
                        select(JobOpportunity)
                        .order_by(JobOpportunity.id.asc())
                        .offset(offset)
                        .limit(batch_size)
                    ).scalars().all()

                    for job in batch_jobs:
                        # 1. Company Name Normalization (Preserving raw in company table)
                        raw_comp_name = job.company.company_name if job.company else "Unknown"
                        cleaned_comp_name = DataNormalizer.normalize_company_name(raw_comp_name)
                        job.cleaned_company_name = cleaned_comp_name

                        # 2. Text Cleaning on Job Title & Fields (Preserving raw job_title)
                        job.cleaned_job_title = DataCleaner.clean_text(job.job_title) or job.job_title

                        if job.location:
                            job.location = DataNormalizer.normalize_location(job.location)

                        if job.job_type:
                            job.job_type = DataNormalizer.normalize_job_type(job.job_type)

                        if job.work_mode:
                            job.work_mode = DataNormalizer.normalize_work_mode(job.work_mode)

                        # 3. Salary Normalization via SalaryConverter
                        salary_data = SalaryConverter.convert(
                            raw_text=job.original_salary_text,
                            job_type=job.job_type
                        )

                        job.salary_type = salary_data["salary_type"]
                        if salary_data["minimum_ctc"] is not None:
                            job.minimum_ctc = salary_data["minimum_ctc"]
                        if salary_data["maximum_ctc"] is not None:
                            job.maximum_ctc = salary_data["maximum_ctc"]
                        if salary_data["fixed_ctc"] is not None:
                            job.fixed_ctc = salary_data["fixed_ctc"]
                        if salary_data["variable_ctc"] is not None:
                            job.variable_ctc = salary_data["variable_ctc"]
                        if salary_data["salary_lpa"] is not None:
                            job.salary_lpa = salary_data["salary_lpa"]
                        if salary_data["annualized_equivalent_lpa"] is not None:
                            job.annualized_equivalent = salary_data["annualized_equivalent_lpa"]
                            job.annualized_equivalent_lpa = salary_data["annualized_equivalent_lpa"]
                        if salary_data["stipend_amount"] is not None:
                            job.stipend_amount = salary_data["stipend_amount"]
                        if salary_data["stipend_period"]:
                            job.stipend_period = salary_data["stipend_period"]
                        if salary_data["joining_bonus"] is not None:
                            job.joining_bonus = salary_data["joining_bonus"]
                        if salary_data["salary_unit"]:
                            job.salary_unit = salary_data["salary_unit"]

                        # 4. Data Validation Rules
                        val_payload = {
                            "company_name": raw_comp_name,
                            "cleaned_company_name": cleaned_comp_name,
                            "job_title": job.job_title,
                            "cleaned_job_title": job.cleaned_job_title,
                            "source_url": job.source_url,
                            "minimum_ctc": job.minimum_ctc,
                            "maximum_ctc": job.maximum_ctc,
                            "salary_lpa": job.salary_lpa,
                            "stipend_amount": job.stipend_amount,
                            "salary_type": job.salary_type,
                            "minimum_cgpa": job.minimum_cgpa,
                            "posted_date": job.posted_date,
                            "application_deadline": job.application_deadline,
                        }

                        val_status, val_notes = DataValidator.validate_job_record(val_payload)
                        job.validation_status = val_status
                        job.validation_notes = "; ".join(val_notes) if val_notes else None
                        job.updated_at = datetime.utcnow()

                    db.commit()

                self._records_processed = min(self._total_records, offset + batch_size)
                self._progress = (self._records_processed / self._total_records) * 100.0
                await asyncio.sleep(0.05)  # Yield control to event loop

            self._status = "COMPLETED"
            self._progress = 100.0
            self._completed_at = datetime.utcnow().isoformat() + "Z"
            logger.info(f"Data processing pipeline completed across {self._total_records} records.")

        except Exception as e:
            self._status = "ERROR"
            self._last_error = str(e)
            logger.error(f"Data processing pipeline encountered error: {str(e)}", exc_info=True)
        finally:
            self.is_running = False

    @staticmethod
    def get_quality_report(db: Session) -> Dict[str, Any]:
        """
        Retrieves live data quality audit report.
        """
        return QualityAnalyzer.generate_report(db)

    @staticmethod
    def get_review_records(
        db: Session,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Retrieves listings flagged for manual operator review.
        """
        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        offset = (page - 1) * page_size

        query = select(JobOpportunity).join(Company).where(
            or_(
                JobOpportunity.validation_status.in_(["NEEDS_REVIEW", "INVALID"]),
                JobOpportunity.salary_type == "NEEDS_REVIEW"
            )
        )

        total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0
        jobs = db.execute(
            query.order_by(JobOpportunity.id.desc()).offset(offset).limit(page_size)
        ).scalars().all()

        items = []
        for j in jobs:
            items.append({
                "id": j.id,
                "company_name": j.company.company_name if j.company else "Unknown",
                "cleaned_company_name": j.cleaned_company_name,
                "job_title": j.job_title,
                "cleaned_job_title": j.cleaned_job_title,
                "original_salary_text": j.original_salary_text,
                "salary_lpa": j.salary_lpa,
                "salary_type": j.salary_type or "NOT_DISCLOSED",
                "validation_status": j.validation_status or "VALID",
                "validation_notes": j.validation_notes,
                "source_url": j.source_url,
                "location": j.location,
                "updated_at": j.updated_at.isoformat() if j.updated_at else None,
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


processing_service = ProcessingService()

