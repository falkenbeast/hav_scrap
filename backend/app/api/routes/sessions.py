from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.session import ScrapingSessionResponse, SessionPaginationResponse
from app.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["Scraping Sessions"])


@router.get("", response_model=SessionPaginationResponse)
def list_sessions(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Returns paginated scraping session audit history with status, records processed, and timestamps.
    """
    skip = (page - 1) * page_size
    items, total = SessionService.get_sessions(db, skip=skip, limit=page_size)
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items
    }


@router.get("/{session_id}", response_model=ScrapingSessionResponse)
def get_session_detail(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    Returns individual scraping session details, timestamps, and error messages.
    """
    session = SessionService.get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"ScrapingSession with ID #{session_id} not found."
        )
    return session
