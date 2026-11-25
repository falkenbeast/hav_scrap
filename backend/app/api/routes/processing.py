import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.processing_service import processing_service

logger = logging.getLogger("hav_scrap")

router = APIRouter(prefix="/processing", tags=["Data Cleaning, Normalization & Quality"])


@router.post("/start", summary="Start repeatable data processing & validation pipeline")
async def start_processing():
    """
    Triggers end-to-end data cleaning, company name normalization,
    structured salary categorization, duplicate auditing, and validation checks.
    """
    try:
        return await processing_service.start()
    except Exception as e:
        logger.error(f"Error starting processing pipeline: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/status", summary="Get data processing pipeline status & progress")
async def get_processing_status():
    """
    Returns pipeline execution state, percentage completed, and timestamps.
    """
    try:
        return processing_service.get_status()
    except Exception as e:
        logger.error(f"Error fetching processing status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/quality-report", summary="Generate comprehensive Data Quality Report")
async def get_quality_report(db: Session = Depends(get_db)):
    """
    Returns overall system data quality score, valid/invalid breakdown,
    duplicate detections, and missing salary/eligibility statistics.
    """
    try:
        return processing_service.get_quality_report(db)
    except Exception as e:
        logger.error(f"Error generating quality report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/review-records", summary="Get records requiring manual operator review")
async def get_review_records(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Retrieves job notices flagged as NEEDS_REVIEW or INVALID due to ambiguous
    compensation clauses or validation rule alerts.
    """
    try:
        return processing_service.get_review_records(db, page=page, page_size=page_size)
    except Exception as e:
        logger.error(f"Error fetching review records: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/statistics", summary="Get data processing summary metrics")
async def get_processing_statistics(db: Session = Depends(get_db)):
    """
    Returns high-level quality metrics for dashboard integration.
    """
    try:
        report = processing_service.get_quality_report(db)
        return {
            "total_records": report["total_jobs"],
            "cleaned_records": report["cleaned_records"],
            "records_valid": report["records_valid"],
            "records_needing_review": report["records_needing_review"],
            "data_quality_percentage": report["data_quality_percentage"],
            "duplicate_jobs_detected": report["duplicate_jobs_detected"],
        }
    except Exception as e:
        logger.error(f"Error fetching processing statistics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

