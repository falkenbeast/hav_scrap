from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query, status
from fastapi.responses import StreamingResponse
from app.services.scraper_service import ScraperService

router = APIRouter(prefix="/scraper", tags=["Scraper Telemetry & Control"])


@router.post("/start", status_code=status.HTTP_200_OK)
async def start_scraping_session():
    """
    Starts a new background scraping session.
    Prevents duplicate simultaneous executions.
    """
    return await ScraperService.start_session()


@router.post("/pause", status_code=status.HTTP_200_OK)
async def pause_scraping_session():
    """
    Pauses the currently running scraping session at the next safe checkpoint.
    """
    return await ScraperService.pause_session()


@router.post("/resume", status_code=status.HTTP_200_OK)
async def resume_scraping_session():
    """
    Resumes execution of a paused scraping session.
    """
    return await ScraperService.resume_session()


@router.post("/stop", status_code=status.HTTP_200_OK)
async def stop_scraping_session():
    """
    Safely cancels and terminates the active scraping session.
    """
    return await ScraperService.stop_session()


@router.get("/status")
def get_scraper_status():
    """
    Returns real-time session progress percentage, records counters, and engine state.
    """
    return ScraperService.get_status()


@router.get("/logs")
def get_scraper_logs(limit: int = Query(50, ge=1, le=200)):
    """
    Returns recent activity telemetry logs from the in-memory buffer.
    """
    return ScraperService.get_logs(limit=limit)


@router.get("/events")
async def stream_scraper_events():
    """
    Server-Sent Events (SSE) streaming endpoint delivering real-time lifecycle updates
    (SESSION_STARTED, PROGRESS_UPDATED, RECORD_DISCOVERED, RECORD_PROCESSED,
     SESSION_PAUSED, SESSION_RESUMED, SESSION_STOPPED, SESSION_COMPLETED, ERROR).
    """
    return StreamingResponse(
        ScraperService.event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
