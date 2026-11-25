from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.system import SystemStatusResponse
from app.services.system_service import SystemService
from app.database.backup import create_database_backup, list_database_backups

router = APIRouter(prefix="/system", tags=["System Telemetry & Database Backups"])


@router.get("/status", response_model=SystemStatusResponse)
def get_system_status(db: Session = Depends(get_db)):
    """
    Returns actual backend service diagnostics, database file status,
    and reports scraper availability state without false claims.
    """
    return SystemService.get_system_status(db)


@router.post("/backup", summary="Trigger verified SQLite snapshot backup")
def trigger_database_backup(tag: Optional[str] = Query(None, description="Optional label tag for backup")):
    """
    Creates an atomic online snapshot of data/hav_scrap.db in data/backups/
    and verifies completion via PRAGMA integrity_check.
    """
    res = create_database_backup(tag=tag)
    if not res.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database backup failed: {res.get('error')}"
        )
    return res


@router.get("/backups", summary="List verified database backups")
def get_database_backups():
    """
    Lists all timestamped database backups stored in data/backups/.
    """
    return {"backups": list_database_backups()}
