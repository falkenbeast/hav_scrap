from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.job import JobOpportunityResponse, JobSalaryResponse, JobPaginationResponse
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["Job Opportunities"])


@router.get("", response_model=JobPaginationResponse)
def list_jobs(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    company_id: Optional[int] = Query(None, description="Filter by company ID"),
    job_type: Optional[str] = Query(None, description="Filter by job type (Full-Time, Internship, etc.)"),
    location: Optional[str] = Query(None, description="Filter by location city"),
    min_salary: Optional[float] = Query(None, ge=0, description="Minimum CTC in LPA"),
    max_salary: Optional[float] = Query(None, ge=0, description="Maximum CTC in LPA"),
    search: Optional[str] = Query(None, description="Keyword search across title, company, role, or location"),
    sort_by: str = Query("created_at", description="Sort field: created_at, salary, title, company"),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
    db: Session = Depends(get_db)
):
    """
    List job opportunities with filtering (company, job type, location, salary range),
    keyword search, pagination, and sorting.
    """
    skip = (page - 1) * page_size
    items, total = JobService.get_jobs(
        db,
        skip=skip,
        limit=page_size,
        company_id=company_id,
        job_type=job_type,
        location=location,
        min_salary=min_salary,
        max_salary=max_salary,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items
    }


@router.get("/{job_id}", response_model=JobOpportunityResponse)
def get_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Return individual job opportunity details.
    """
    job = JobService.get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job opportunity with ID #{job_id} not found")
    return job


@router.get("/{job_id}/salary", response_model=JobSalaryResponse)
def get_job_salary(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Return dedicated compensation breakdown for a specific job notice.
    """
    job = JobService.get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job opportunity with ID #{job_id} not found")
    return {
        "id": job.id,
        "company_id": job.company_id,
        "company_name": job.company.company_name if job.company else None,
        "job_title": job.job_title,
        "original_salary_text": job.original_salary_text,
        "minimum_ctc": job.minimum_ctc,
        "maximum_ctc": job.maximum_ctc,
        "fixed_ctc": job.fixed_ctc,
        "variable_ctc": job.variable_ctc,
        "joining_bonus": job.joining_bonus,
        "salary_lpa": job.salary_lpa,
        "salary_unit": job.salary_unit,
        "stipend_amount": job.stipend_amount,
        "stipend_period": job.stipend_period,
        "annualized_equivalent": job.annualized_equivalent,
        "job_type": job.job_type,
        "last_verified_at": job.last_verified_at,
    }
