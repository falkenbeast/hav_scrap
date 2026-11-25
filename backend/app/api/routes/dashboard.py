from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.dashboard_service import DashboardService
from app.schemas.stats import DashboardStatsResponse, ActivityItem

router = APIRouter(prefix="/dashboard", tags=["Dashboard Intelligence"])


@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_statistics(db: Session = Depends(get_db)):
    """
    Returns actual placement KPIs and aggregated metrics directly from SQLite database.
    """
    return DashboardService.get_dashboard_stats(db)


@router.get("/activity", response_model=List[ActivityItem])
def get_dashboard_activity(
    limit: int = Query(10, ge=1, le=50, description="Maximum activity items to retrieve"),
    db: Session = Depends(get_db)
):
    """
    Returns genuine chronological intelligence activity from the database
    (scraping sessions, company discoveries, job indexing, and export records).
    Returns an empty list when no activity exists.
    """
    return DashboardService.get_recent_activity(db, limit=limit)


