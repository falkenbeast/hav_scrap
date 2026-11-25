import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.extraction_service import extraction_service

logger = logging.getLogger("hav_scrap")

router = APIRouter(prefix="/extraction/details", tags=["Deep Job Details & Salary Extraction"])


@router.post("/start", summary="Start detailed extraction on discovered job postings")
async def start_deep_extraction(
    force_reextract: bool = Query(False, description="Re-extract even if already marked EXTRACTED"),
    limit: Optional[int] = Query(None, ge=1, le=500, description="Optional cap on number of postings to process")
):
    """
    Launches background runner to visit individual posting URLs,
    extract detailed salary, stipend, and eligibility requirements.
    """
    try:
        res = await extraction_service.start(force_reextract=force_reextract, limit=limit)
        return res
    except Exception as e:
        logger.error(f"Error starting detailed extraction: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/stop", summary="Stop active detailed extraction")
async def stop_deep_extraction():
    """
    Gracefully halts detailed extraction runner at the next safe posting checkpoint.
    """
    try:
        return await extraction_service.stop()
    except Exception as e:
        logger.error(f"Error stopping detailed extraction: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/status", summary="Get detailed extraction status and counters")
async def get_extraction_status():
    """
    Returns progress metrics including extracted, failed, pending postings,
    and salary/stipend detection statistics.
    """
    try:
        return extraction_service.get_status()
    except Exception as e:
        logger.error(f"Error fetching extraction status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/results", summary="Get paginated list of deep extraction results")
async def get_extraction_results(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status: EXTRACTED, PENDING, FAILED"),
    db: Session = Depends(get_db)
):
    """
    Retrieves extracted job details with structured salary breakdowns and eligibility criteria.
    """
    try:
        return extraction_service.get_results(db, page=page, page_size=page_size, status=status)
    except Exception as e:
        logger.error(f"Error fetching extraction results: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

