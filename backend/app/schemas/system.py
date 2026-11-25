from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class SystemStatusResponse(BaseModel):
    """
    Schema for GET /api/system/status
    Documents real-time backend health, SQLite database connectivity, and scraper engine status.
    """
    backend_status: str = Field("operational", description="Core FastAPI service state")
    database_connected: bool = Field(True, description="SQLite file connectivity status")
    database_path: str = Field(..., description="Absolute path to active SQLite database file")
    scraper_status: str = Field("IDLE", description="Current scraper controller state: IDLE, RUNNING, PAUSED, COMPLETED")
    scraper_availability: str = Field(
        "IDLE - Scraper engine ready for portal reconnaissance",
        description="Scraper engine availability description"
    )
    application_name: str = Field("hav_scrap", description="Application identifier")
    version: str = Field("1.0.0", description="Backend semantic version")
    timestamp: str = Field(..., description="Server ISO timestamp")
    metrics: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

