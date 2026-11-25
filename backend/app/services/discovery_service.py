import logging
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import func, select, or_

from app.models.company import Company
from app.models.job import JobOpportunity
from app.processors.salary_processor import SalaryProcessor

logger = logging.getLogger("hav_scrap")


def parse_date_value(date_val: Any) -> Optional[datetime]:
    if not date_val:
        return None
    if isinstance(date_val, datetime):
        return date_val if date_val.tzinfo is not None else date_val.replace(tzinfo=timezone.utc)
    s = str(date_val).strip()
    if not s or s in {"—", "-", "N/A"}:
        return None
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%d %b %Y",
        "%d %B %Y",
    ):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return None


class DiscoveryService:
    """
    Business service managing company discovery persistence,
    safe deduplication algorithms, and catalog queries.
    """

    @staticmethod
    def normalize_company_name(name: str) -> str:
        """
        Normalizes company name for accurate identity lookup while preserving original branding.
        """
        if not name:
            return ""
        return " ".join(name.strip().split())

    @staticmethod
    def save_discovered_listing(
        db: Session,
        listing_data: Dict[str, Any]
    ) -> Tuple[Company, JobOpportunity, bool, bool]:
        """
        Persists or updates a discovered company and its associated job opportunity.
        Returns:
            (Company, JobOpportunity, is_new_company, is_new_job)
        """
        raw_company_name = listing_data.get("company_name", "").strip()
        if not raw_company_name:
            raise ValueError("Company name is required for discovery persistence.")

        norm_name = DiscoveryService.normalize_company_name(raw_company_name)
        website = listing_data.get("company_website") or listing_data.get("website")
        source_url = listing_data.get("job_url") or listing_data.get("source_url")
        job_title = (listing_data.get("job_title") or listing_data.get("job_role") or "General Placement Opportunity").strip()
        job_role = listing_data.get("job_role") or job_title
        job_type = listing_data.get("job_type")
        location = listing_data.get("location")
        batch = listing_data.get("target_batch") or listing_data.get("batch")
        job_status = listing_data.get("job_status")
        apply_before = parse_date_value(listing_data.get("apply_before") or listing_data.get("application_deadline"))
        date_of_visit = parse_date_value(listing_data.get("date_of_visit"))
        posted_date = parse_date_value(listing_data.get("job_posted_date") or listing_data.get("posted_date"))

        # Process Salary (strictly independent from stipend)
        sal = SalaryProcessor.normalize_salary(
            raw_text=listing_data.get("salary_original"),
            min_ctc_lpa=listing_data.get("salary_min_lpa"),
            max_ctc_lpa=listing_data.get("salary_max_lpa")
        )

        # Process Stipend (strictly independent from salary)
        stip = SalaryProcessor.normalize_stipend(
            raw_text=listing_data.get("stipend_original"),
            stipend_period=listing_data.get("stipend_period"),
            min_val=listing_data.get("stipend_min"),
            max_val=listing_data.get("stipend_max")
        )

        # 1. Company Identity & Deduplication
        company = db.execute(
            select(Company).where(func.lower(Company.company_name) == norm_name.lower())
        ).scalar_one_or_none()

        is_new_company = False
        if not company:
            # Check for legacy concatenated record (e.g. starts with clean name and length > clean name)
            legacy_company = db.execute(
                select(Company).where(
                    Company.company_name.ilike(f"{norm_name}%"),
                    func.length(Company.company_name) > len(norm_name)
                )
            ).scalars().first()

            if legacy_company:
                logger.info(f"Repairing legacy company name '{legacy_company.company_name}' -> '{norm_name}'")
                legacy_company.company_name = norm_name
                if website and not legacy_company.website:
                    legacy_company.website = website
                if source_url and not legacy_company.source_url:
                    legacy_company.source_url = source_url
                legacy_company.updated_at = datetime.now(timezone.utc)
                company = legacy_company
            else:
                company = Company(
                    company_name=norm_name,
                    website=website,
                    source_url=source_url,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                db.add(company)
                db.flush()
                is_new_company = True
                logger.info(f"Discovered new company: '{norm_name}' (ID: {company.id})")
        else:
            if website and not company.website:
                company.website = website
            if source_url and not company.source_url:
                company.source_url = source_url
            company.updated_at = datetime.now(timezone.utc)

        # 2. Job Opportunity Identity & Deduplication
        job = None
        if source_url:
            job = db.execute(
                select(JobOpportunity).where(JobOpportunity.source_url == source_url)
            ).scalar_one_or_none()

        if not job:
            job = db.execute(
                select(JobOpportunity).where(
                    JobOpportunity.company_id == company.id,
                    func.lower(JobOpportunity.job_title) == job_title.lower()
                )
            ).scalar_one_or_none()

        if not job:
            # Check for legacy corrupt job title (e.g. contained "Full Time" or salary numbers)
            legacy_job = db.execute(
                select(JobOpportunity).where(
                    JobOpportunity.company_id == company.id,
                    or_(
                        JobOpportunity.job_title.ilike("%Full Time%"),
                        JobOpportunity.job_title.ilike("%Intern%"),
                        JobOpportunity.job_title.ilike("%LPA%"),
                        JobOpportunity.job_title.ilike("%L%")
                    )
                )
            ).scalars().first()
            if legacy_job:
                logger.info(f"Repairing legacy job title '{legacy_job.job_title}' -> '{job_title}'")
                job = legacy_job

        is_new_job = False
        if not job:
            job = JobOpportunity(
                company_id=company.id,
                job_title=job_title,
                job_role=job_role,
                original_salary_text=sal["original_salary_text"],
                minimum_ctc=sal["minimum_ctc"],
                maximum_ctc=sal["maximum_ctc"],
                salary_lpa=sal["salary_lpa"],
                salary_unit=sal["salary_unit"],
                original_stipend_text=stip["original_stipend_text"],
                stipend_min=stip["stipend_min"],
                stipend_max=stip["stipend_max"],
                stipend_amount=stip["stipend_amount"],
                stipend_period=stip["stipend_period"],
                job_type=job_type,
                job_status=job_status,
                location=location,
                batch=batch,
                source_url=source_url,
                application_deadline=apply_before,
                date_of_visit=date_of_visit,
                posted_date=posted_date,
                extraction_status="COMPLETED",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(job)
            db.flush()
            is_new_job = True
            logger.info(f"Discovered new job opportunity: '{job_title}' for '{company.company_name}'")
        else:
            # Update and enrich attributes cleanly
            job.job_title = job_title
            job.job_role = job_role
            if sal["original_salary_text"] is not None:
                job.original_salary_text = sal["original_salary_text"]
            if sal["minimum_ctc"] is not None:
                job.minimum_ctc = sal["minimum_ctc"]
            if sal["maximum_ctc"] is not None:
                job.maximum_ctc = sal["maximum_ctc"]
            if sal["salary_lpa"] is not None:
                job.salary_lpa = sal["salary_lpa"]
            if sal["salary_unit"] is not None:
                job.salary_unit = sal["salary_unit"]

            if stip["original_stipend_text"] is not None:
                job.original_stipend_text = stip["original_stipend_text"]
            if stip["stipend_min"] is not None:
                job.stipend_min = stip["stipend_min"]
            if stip["stipend_max"] is not None:
                job.stipend_max = stip["stipend_max"]
            if stip["stipend_amount"] is not None:
                job.stipend_amount = stip["stipend_amount"]
            if stip["stipend_period"] is not None:
                job.stipend_period = stip["stipend_period"]

            if job_type:
                job.job_type = job_type
            if job_status:
                job.job_status = job_status
            if location:
                job.location = location
            if batch:
                job.batch = batch
            if apply_before:
                job.application_deadline = apply_before
            if date_of_visit:
                job.date_of_visit = date_of_visit
            if posted_date:
                job.posted_date = posted_date
            if source_url:
                job.source_url = source_url

            job.extraction_status = "COMPLETED"
            job.updated_at = datetime.now(timezone.utc)

        db.commit()
        return company, job, is_new_company, is_new_job

    @staticmethod
    def get_discovery_stats(db: Session) -> Dict[str, Any]:
        """
        Retrieves aggregate statistics for discovered companies and jobs.
        """
        total_companies = db.execute(select(func.count(Company.id))).scalar() or 0
        total_jobs = db.execute(select(func.count(JobOpportunity.id))).scalar() or 0
        
        active_companies = db.execute(
            select(func.count(func.distinct(JobOpportunity.company_id)))
        ).scalar() or 0

        batches = db.execute(
            select(JobOpportunity.batch).where(JobOpportunity.batch.is_not(None)).distinct()
        ).scalars().all()

        return {
            "total_companies": total_companies,
            "total_jobs": total_jobs,
            "active_companies": active_companies,
            "batches_tracked": [b for b in batches if b],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

    @staticmethod
    def get_discovered_companies(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None
    ) -> Tuple[List[Company], int]:
        query = select(Company)
        if search:
            query = query.where(Company.company_name.ilike(f"%{search.strip()}%"))
        
        count_query = select(func.count(Company.id))
        if search:
            count_query = count_query.where(Company.company_name.ilike(f"%{search.strip()}%"))
        
        total = db.execute(count_query).scalar() or 0
        items = db.execute(query.order_by(Company.created_at.desc()).offset(skip).limit(limit)).scalars().all()
        return items, total

    @staticmethod
    def get_discovered_jobs(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        company_id: Optional[int] = None
    ) -> Tuple[List[JobOpportunity], int]:
        query = select(JobOpportunity)
        if company_id:
            query = query.where(JobOpportunity.company_id == company_id)
        
        count_query = select(func.count(JobOpportunity.id))
        if company_id:
            count_query = count_query.where(JobOpportunity.company_id == company_id)
        
        total = db.execute(count_query).scalar() or 0
        items = db.execute(query.order_by(JobOpportunity.created_at.desc()).offset(skip).limit(limit)).scalars().all()
        return items, total


discovery_service = DiscoveryService()
