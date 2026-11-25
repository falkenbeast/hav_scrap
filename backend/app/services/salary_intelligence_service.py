"""
Salary Intelligence Service.
Powers granular company rankings, compensation tier benchmarks,
fixed vs variable CTC audits, and undisclosed package diagnostics.
"""
import logging
from typing import List, Dict, Any, Optional

try:
    from sqlalchemy.orm import Session
    from sqlalchemy import select, func, and_, or_, desc, asc
except ImportError:
    Session = Any
    select = None
    func = None
    and_ = None
    or_ = None
    desc = None
    asc = None

try:
    from app.models.company import Company
    from app.models.job import JobOpportunity
except ImportError:
    Company = Any
    JobOpportunity = Any
from app.schemas.analytics import (
    CompanyRankingItem,
    CompanyRankingsResponse,
    SalaryIntelligenceRecord,
    SalaryIntelligenceResponse,
)

logger = logging.getLogger("hav_scrap")


class SalaryIntelligenceService:
    """
    Analyzes compensation data from SQLite database.
    Excludes internship stipends from CTC calculations and strictly handles missing salaries.
    """

    @classmethod
    def get_company_rankings(
        cls,
        db: Session,
        sort_by: str = "highest_ctc",
        order: str = "desc",
        page: int = 1,
        page_size: int = 20,
        company: Optional[str] = None,
        job_type: Optional[str] = None,
    ) -> CompanyRankingsResponse:
        """
        Ranks companies by verified CTC metrics, job volume, or internship availability.
        Never ranks companies using ambiguous, missing, or stipend values.
        """
        page = max(1, page)
        page_size = max(1, min(page_size, 100))

        # Query all companies with their jobs
        stmt = select(Company).order_by(Company.company_name.asc())
        if company:
            stmt = stmt.where(Company.company_name.ilike(f"%{company}%"))

        companies = db.execute(stmt).scalars().all()

        ranking_items: List[CompanyRankingItem] = []

        for comp in companies:
            # Filter opportunities if job_type specified
            comp_jobs = comp.jobs
            if job_type:
                comp_jobs = [j for j in comp_jobs if j.job_type and job_type.lower() in j.job_type.lower()]

            if not comp_jobs and job_type:
                continue

            opp_count = len(comp_jobs)

            # Separate full-time verified CTC vs internships
            valid_ctcs: List[float] = []
            intern_count = 0

            for j in comp_jobs:
                is_intern = (
                    j.salary_type == "INTERNSHIP_STIPEND" or
                    j.stipend_amount is not None or
                    (j.job_type and "intern" in j.job_type.lower())
                )
                if is_intern:
                    intern_count += 1
                else:
                    # Valid full-time salary check
                    is_valid = (
                        j.validation_status != "INVALID" and
                        j.validation_status != "NEEDS_REVIEW" and
                        j.salary_type != "NEEDS_REVIEW" and
                        j.salary_lpa is not None and
                        j.salary_lpa > 0
                    )
                    if is_valid:
                        valid_ctcs.append(float(j.salary_lpa))

            highest_ctc = round(max(valid_ctcs), 2) if valid_ctcs else None
            lowest_ctc = round(min(valid_ctcs), 2) if valid_ctcs else None
            avg_ctc = round(sum(valid_ctcs) / len(valid_ctcs), 2) if valid_ctcs else None

            ranking_items.append(
                CompanyRankingItem(
                    company_name=comp.company_name,
                    company_id=comp.id,
                    opportunities_count=opp_count,
                    highest_ctc_lpa=highest_ctc,
                    average_ctc_lpa=avg_ctc,
                    lowest_ctc_lpa=lowest_ctc,
                    offers_internships=(intern_count > 0),
                    internships_count=intern_count,
                    disclosed_salary_records=len(valid_ctcs)
                )
            )

        # Sorting logic
        is_reverse = (order.lower() == "desc")

        if sort_by == "highest_ctc":
            # Companies with disclosed salaries prioritized first
            ranking_items.sort(
                key=lambda x: (
                    x.highest_ctc_lpa is not None,
                    x.highest_ctc_lpa or 0.0,
                    x.opportunities_count
                ),
                reverse=is_reverse
            )
        elif sort_by == "average_ctc":
            ranking_items.sort(
                key=lambda x: (
                    x.average_ctc_lpa is not None,
                    x.average_ctc_lpa or 0.0,
                    x.opportunities_count
                ),
                reverse=is_reverse
            )
        elif sort_by == "internship_count":
            ranking_items.sort(
                key=lambda x: (
                    x.internships_count,
                    x.opportunities_count,
                    x.highest_ctc_lpa or 0.0
                ),
                reverse=is_reverse
            )
        else:  # "opportunities_count"
            ranking_items.sort(
                key=lambda x: (
                    x.opportunities_count,
                    x.highest_ctc_lpa or 0.0
                ),
                reverse=is_reverse
            )

        total = len(ranking_items)
        offset = (page - 1) * page_size
        paged_items = ranking_items[offset:offset + page_size]

        return CompanyRankingsResponse(
            items=paged_items,
            total=total,
            page=page,
            page_size=page_size
        )

    @classmethod
    def get_salary_records(
        cls,
        db: Session,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "salary_lpa",
        sort_order: str = "desc",
        company: Optional[str] = None,
        role: Optional[str] = None,
        salary_type: Optional[str] = None,
        search: Optional[str] = None,
        job_type: Optional[str] = None,
        location: Optional[str] = None,
    ) -> SalaryIntelligenceResponse:
        """
        Fetches granular job opportunities for the salary comparison table,
        with multi-column sorting, search filters, and disclosure health indicators.
        """
        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        offset = (page - 1) * page_size

        stmt = select(JobOpportunity).join(Company)
        conditions = []

        if company:
            conditions.append(
                or_(
                    Company.company_name.ilike(f"%{company}%"),
                    JobOpportunity.cleaned_company_name.ilike(f"%{company}%")
                )
            )

        if role:
            conditions.append(
                or_(
                    JobOpportunity.job_title.ilike(f"%{role}%"),
                    JobOpportunity.cleaned_job_title.ilike(f"%{role}%")
                )
            )

        if salary_type:
            conditions.append(JobOpportunity.salary_type == salary_type)

        if job_type:
            conditions.append(JobOpportunity.job_type.ilike(f"%{job_type}%"))

        if location:
            conditions.append(JobOpportunity.location.ilike(f"%{location}%"))

        if search:
            q = f"%{search.strip()}%"
            conditions.append(
                or_(
                    Company.company_name.ilike(q),
                    JobOpportunity.job_title.ilike(q),
                    JobOpportunity.cleaned_job_title.ilike(q),
                    JobOpportunity.original_salary_text.ilike(q)
                )
            )

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Total count before pagination
        total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0

        # Overall corpus disclosure stats
        disclosed_count = db.execute(
            select(func.count(JobOpportunity.id)).where(
                JobOpportunity.salary_lpa.is_not(None),
                JobOpportunity.salary_lpa > 0
            )
        ).scalar() or 0

        review_count = db.execute(
            select(func.count(JobOpportunity.id)).where(
                or_(
                    JobOpportunity.validation_status == "NEEDS_REVIEW",
                    JobOpportunity.salary_type == "NEEDS_REVIEW"
                )
            )
        ).scalar() or 0

        total_corpus_jobs = db.execute(select(func.count(JobOpportunity.id))).scalar() or 1
        disclosure_pct = round((disclosed_count / total_corpus_jobs * 100), 1)

        # Apply sorting
        order_col = JobOpportunity.salary_lpa
        if sort_by == "company_name":
            order_col = Company.company_name
        elif sort_by == "minimum_ctc":
            order_col = JobOpportunity.minimum_ctc
        elif sort_by == "maximum_ctc":
            order_col = JobOpportunity.maximum_ctc
        elif sort_by == "fixed_ctc":
            order_col = JobOpportunity.fixed_ctc
        elif sort_by == "job_title":
            order_col = JobOpportunity.job_title

        if sort_order.lower() == "asc":
            stmt = stmt.order_by(order_col.asc().nulls_last())
        else:
            stmt = stmt.order_by(order_col.desc().nulls_last())

        jobs = db.execute(stmt.offset(offset).limit(page_size)).scalars().all()

        items = []
        for j in jobs:
            cname = j.cleaned_company_name or (j.company.company_name if j.company else "Unknown")
            jtitle = j.cleaned_job_title or j.job_title

            items.append(
                SalaryIntelligenceRecord(
                    id=j.id,
                    company_name=cname,
                    job_role=j.job_role or jtitle,
                    job_title=jtitle,
                    minimum_ctc=j.minimum_ctc,
                    maximum_ctc=j.maximum_ctc,
                    fixed_ctc=j.fixed_ctc,
                    variable_ctc=j.variable_ctc,
                    normalized_salary_lpa=j.salary_lpa,
                    original_salary_text=j.original_salary_text,
                    salary_type=j.salary_type,
                    job_type=j.job_type,
                    work_mode=j.work_mode,
                    location=j.location,
                    validation_status=j.validation_status
                )
            )

        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return SalaryIntelligenceResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            salary_disclosure_percentage=disclosure_pct,
            records_needing_review_count=review_count
        )
