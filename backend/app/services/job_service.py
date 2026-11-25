from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from app.models.job import JobOpportunity
from app.models.company import Company
from app.schemas.job import JobOpportunityCreate, JobOpportunityResponse


class JobService:
    @staticmethod
    def get_jobs(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        company_id: Optional[int] = None,
        job_type: Optional[str] = None,
        location: Optional[str] = None,
        min_salary: Optional[float] = None,
        max_salary: Optional[float] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[JobOpportunityResponse], int]:
        """
        Retrieves job opportunities matching filter criteria, with pagination and sorting.
        """
        query = db.query(JobOpportunity, Company.company_name).join(
            Company, JobOpportunity.company_id == Company.id
        )

        if company_id:
            query = query.filter(JobOpportunity.company_id == company_id)
        if job_type:
            query = query.filter(JobOpportunity.job_type.ilike(f"%{job_type.strip()}%"))
        if location:
            query = query.filter(JobOpportunity.location.ilike(f"%{location.strip()}%"))
        if min_salary is not None:
            query = query.filter(JobOpportunity.salary_lpa >= min_salary)
        if max_salary is not None:
            query = query.filter(JobOpportunity.salary_lpa <= max_salary)
        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.filter(
                (JobOpportunity.job_title.ilike(search_pattern)) |
                (Company.company_name.ilike(search_pattern)) |
                (JobOpportunity.job_role.ilike(search_pattern)) |
                (JobOpportunity.location.ilike(search_pattern))
            )

        # Count total matches
        count_query = db.query(func.count(JobOpportunity.id)).join(
            Company, JobOpportunity.company_id == Company.id
        )
        if company_id:
            count_query = count_query.filter(JobOpportunity.company_id == company_id)
        if job_type:
            count_query = count_query.filter(JobOpportunity.job_type.ilike(f"%{job_type.strip()}%"))
        if location:
            count_query = count_query.filter(JobOpportunity.location.ilike(f"%{location.strip()}%"))
        if min_salary is not None:
            count_query = count_query.filter(JobOpportunity.salary_lpa >= min_salary)
        if max_salary is not None:
            count_query = count_query.filter(JobOpportunity.salary_lpa <= max_salary)
        if search:
            search_pattern = f"%{search.strip()}%"
            count_query = count_query.filter(
                (JobOpportunity.job_title.ilike(search_pattern)) |
                (Company.company_name.ilike(search_pattern)) |
                (JobOpportunity.job_role.ilike(search_pattern)) |
                (JobOpportunity.location.ilike(search_pattern))
            )
        total = count_query.scalar() or 0

        # Sorting logic
        order_fn = desc if sort_order.lower() == "desc" else asc
        if sort_by == "salary":
            query = query.order_by(order_fn(JobOpportunity.salary_lpa))
        elif sort_by == "title":
            query = query.order_by(order_fn(JobOpportunity.job_title))
        elif sort_by == "company":
            query = query.order_by(order_fn(Company.company_name))
        else:  # default by created_at
            query = query.order_by(order_fn(JobOpportunity.created_at))

        results = query.offset(skip).limit(limit).all()

        job_list = []
        for job, company_name in results:
            item = JobOpportunityResponse.model_validate(job)
            item.company_name = company_name
            job_list.append(item)

        return job_list, total

    @staticmethod
    def get_job_by_id(db: Session, job_id: int) -> Optional[JobOpportunityResponse]:
        result = db.query(JobOpportunity, Company.company_name).join(
            Company, JobOpportunity.company_id == Company.id
        ).filter(JobOpportunity.id == job_id).first()

        if not result:
            return None
        job, company_name = result
        item = JobOpportunityResponse.model_validate(job)
        item.company_name = company_name
        return item

    @staticmethod
    def create_or_update_job(db: Session, job_data: JobOpportunityCreate) -> JobOpportunity:
        """
        Idempotent insertion / update ensuring duplicate records are prevented
        by checking matching source_url or (company_id, job_title, batch).
        """
        existing = None
        if job_data.source_url:
            existing = db.query(JobOpportunity).filter(
                JobOpportunity.source_url == job_data.source_url
            ).first()

        if not existing and job_data.batch:
            existing = db.query(JobOpportunity).filter(
                JobOpportunity.company_id == job_data.company_id,
                JobOpportunity.job_title == job_data.job_title,
                JobOpportunity.batch == job_data.batch
            ).first()

        if existing:
            # Update fields
            for key, value in job_data.model_dump(exclude_unset=True).items():
                setattr(existing, key, value)
            db.commit()
            db.refresh(existing)
            return existing

        new_job = JobOpportunity(**job_data.model_dump())
        db.add(new_job)
        db.commit()
        db.refresh(new_job)
        return new_job
