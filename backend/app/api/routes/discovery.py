import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.discovery_service import discovery_service
from app.scraper.controller import scraper_controller

logger = logging.getLogger("hav_scrap")

router = APIRouter(prefix="/discovery", tags=["Haveloc Listing Discovery"])


@router.post("/start", summary="Start Haveloc company & job listing discovery")
async def start_discovery():
    """
    Triggers the managed background scraper engine to discover companies
    and placement notices from the authenticated Haveloc dashboard.
    """
    try:
        session_id = await scraper_controller.start()
        return {
            "success": True,
            "session_id": session_id,
            "message": f"Discovery session #{session_id} commenced successfully."
        }
    except Exception as e:
        logger.error(f"Error commencing discovery session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/stop", summary="Stop active listing discovery session")
async def stop_discovery():
    """
    Gracefully stops the active listing discovery session at the next safe checkpoint.
    """
    try:
        stopped = await scraper_controller.stop()
        return {
            "success": stopped,
            "message": "Discovery stop instruction issued." if stopped else "No active discovery session to stop."
        }
    except Exception as e:
        logger.error(f"Error stopping discovery: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/status", summary="Get active discovery status & live telemetry")
async def get_discovery_status():
    """
    Returns live progress, session phase, records discovered, and current stage.
    """
    try:
        return scraper_controller.get_status()
    except Exception as e:
        logger.error(f"Error fetching discovery status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/statistics", summary="Get aggregate discovery statistics")
async def get_discovery_statistics(db: Session = Depends(get_db)):
    """
    Returns total discovered companies, unique companies, active listings,
    and batch tags extracted.
    """
    try:
        return discovery_service.get_discovery_stats(db)
    except Exception as e:
        logger.error(f"Error fetching discovery statistics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/results", summary="Get paginated list of discovered job opportunities")
async def get_discovery_results(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by title, role, company, or location"),
    db: Session = Depends(get_db)
):
    """
    Retrieves discovered placement listings stored in SQLite with pagination and search.
    """
    try:
        return discovery_service.get_job_results(db, page=page, page_size=page_size, search=search)
    except Exception as e:
        logger.error(f"Error fetching discovery results: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

