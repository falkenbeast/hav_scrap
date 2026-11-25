from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class ScrapingSessionBase(BaseModel):
    status: str = Field("IDLE", max_length=50, description="Session status: IDLE, PENDING, RUNNING, COMPLETED, FAILED, TERMINATED")
    records_discovered: int = Field(0, ge=0, description="Total notices / listings found")
    records_processed: int = Field(0, ge=0, description="Total listings parsed and committed")
    error_message: Optional[str] = Field(None, description="Diagnostic error log or abort reason")


class ScrapingSessionCreate(BaseModel):
    status: Optional[str] = "RUNNING"


class ScrapingSessionUpdate(BaseModel):
    status: Optional[str] = None
    records_discovered: Optional[int] = None
    records_processed: Optional[int] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None


class ScrapingSessionResponse(ScrapingSessionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    started_at: datetime
    completed_at: Optional[datetime] = None


class SessionPaginationResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[ScrapingSessionResponse]
