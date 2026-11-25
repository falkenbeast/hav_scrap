from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.company import CompanyDetailResponse, CompanyPaginationResponse
from app.services.company_service import CompanyService

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.get("", response_model=CompanyPaginationResponse)
def list_companies(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search company by name"),
    sort_by: str = Query("name", description="Sort field: name, jobs, max_ctc, created_at"),
    sort_order: str = Query("asc", description="Sort order: asc, desc"),
    db: Session = Depends(get_db)
):
    """
    List companies with pagination, search by name, and sorting options.
    """
    skip = (page - 1) * page_size
    items, total = CompanyService.get_companies(
        db,
        skip=skip,
        limit=page_size,
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


@router.get("/{company_id}", response_model=CompanyDetailResponse)
def get_company(
    company_id: int,
    db: Session = Depends(get_db)
):
    """
    Return individual company details and associated job opportunities.
    """
    company = CompanyService.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company with ID #{company_id} not found")
    return company
