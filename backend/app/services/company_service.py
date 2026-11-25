from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from app.models.company import Company
from app.models.job import JobOpportunity
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyDetailResponse
from app.schemas.job import JobOpportunityResponse


class CompanyService:
    @staticmethod
    def get_companies(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        sort_by: str = "name",
        sort_order: str = "asc"
    ) -> Tuple[List[CompanyResponse], int]:
        """
        Retrieves companies with aggregated metrics (total jobs, max CTC, avg CTC),
        supporting search, sorting, and pagination.
        """
        query = db.query(
            Company.id,
            Company.company_name,
            Company.website,
            Company.source_url,
            Company.created_at,
            Company.updated_at,
            func.count(JobOpportunity.id).label("total_jobs"),
            func.max(func.coalesce(JobOpportunity.maximum_ctc, JobOpportunity.salary_lpa)).label("max_ctc"),
            func.avg(func.coalesce(JobOpportunity.salary_lpa, JobOpportunity.maximum_ctc)).label("avg_ctc")
        ).outerjoin(JobOpportunity, Company.id == JobOpportunity.company_id)

        if search:
            query = query.filter(Company.company_name.ilike(f"%{search.strip()}%"))

        query = query.group_by(Company.id)

        # Sorting logic
        order_fn = desc if sort_order.lower() == "desc" else asc
        if sort_by == "jobs":
            query = query.order_by(order_fn("total_jobs"), Company.company_name.asc())
        elif sort_by == "max_ctc":
            query = query.order_by(order_fn("max_ctc"), Company.company_name.asc())
        elif sort_by == "created_at":
            query = query.order_by(order_fn(Company.created_at))
        else:  # default by name
            query = query.order_by(order_fn(Company.company_name))

        # Total count for pagination
        count_query = db.query(func.count(Company.id))
        if search:
            count_query = count_query.filter(Company.company_name.ilike(f"%{search.strip()}%"))
        total = count_query.scalar() or 0

        results = query.offset(skip).limit(limit).all()

        comp_ids = [r.id for r in results]
        jobs = db.query(JobOpportunity).filter(JobOpportunity.company_id.in_(comp_ids)).all() if comp_ids else []
        comp_job_map = {}
        comp_roles_map = {}
        comp_locations_map = {}
        for j in jobs:
            cid = j.company_id
            if cid not in comp_job_map:
                comp_job_map[cid] = j
            if cid not in comp_roles_map:
                comp_roles_map[cid] = []
            if j.job_title and j.job_title not in comp_roles_map[cid]:
                comp_roles_map[cid].append(j.job_title)
            if cid not in comp_locations_map:
                comp_locations_map[cid] = []
            if j.location and j.location not in comp_locations_map[cid]:
                comp_locations_map[cid].append(j.location)

        companies = []
        for r in results:
            primary_job = comp_job_map.get(r.id)
            roles = comp_roles_map.get(r.id, [])
            locs = comp_locations_map.get(r.id, [])
            p_date_str = primary_job.posted_date.strftime("%Y-%m-%d") if primary_job and primary_job.posted_date else None
            companies.append(
                CompanyResponse(
                    id=r.id,
                    company_name=r.company_name,
                    website=r.website,
                    source_url=r.source_url,
                    created_at=r.created_at,
                    updated_at=r.updated_at,
                    total_jobs=r.total_jobs or 0,
                    max_ctc=round(r.max_ctc, 2) if r.max_ctc is not None else None,
                    avg_ctc=round(r.avg_ctc, 2) if r.avg_ctc is not None else None,
                    job_role=primary_job.job_title if primary_job else None,
                    job_roles=roles,
                    location=primary_job.location if primary_job else None,
                    locations=locs,
                    job_type=primary_job.job_type if primary_job else None,
                    job_status=primary_job.job_status if primary_job and primary_job.job_status else "Discovered",
                    posted_date=p_date_str or (r.created_at.strftime("%Y-%m-%d") if r.created_at else None)
                )
            )
        return companies, total

    @staticmethod
    def get_company_by_id(db: Session, company_id: int) -> Optional[CompanyDetailResponse]:
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            return None

        # Aggregate metrics
        metrics = db.query(
            func.count(JobOpportunity.id).label("total_jobs"),
            func.max(JobOpportunity.salary_lpa).label("max_ctc"),
            func.avg(JobOpportunity.salary_lpa).label("avg_ctc")
        ).filter(JobOpportunity.company_id == company_id).first()

        job_responses = []
        for j in company.jobs:
            item = JobOpportunityResponse.model_validate(j)
            item.company_name = company.company_name
            job_responses.append(item)

        return CompanyDetailResponse(
            id=company.id,
            company_name=company.company_name,
            website=company.website,
            source_url=company.source_url,
            created_at=company.created_at,
            updated_at=company.updated_at,
            total_jobs=metrics.total_jobs if metrics else 0,
            max_ctc=round(metrics.max_ctc, 2) if (metrics and metrics.max_ctc is not None) else None,
            avg_ctc=round(metrics.avg_ctc, 2) if (metrics and metrics.avg_ctc is not None) else None,
            jobs=job_responses
        )

    @staticmethod
    def create_company(db: Session, company_data: CompanyCreate) -> Company:
        existing = db.query(Company).filter(Company.company_name == company_data.company_name.strip()).first()
        if existing:
            return existing

        new_company = Company(
            company_name=company_data.company_name.strip(),
            website=company_data.website,
            source_url=company_data.source_url
        )
        db.add(new_company)
        db.commit()
        db.refresh(new_company)
        return new_company
