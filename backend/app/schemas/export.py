from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class ExportGenerateRequest(BaseModel):
    """
    Request payload to initiate Excel workbook generation.
    """
    export_type: str = Field(
        default="ALL",
        description="Export preset type: ALL, COMPANIES, JOBS, SALARY, INTERNSHIPS"
    )
    include_sheets: Optional[List[str]] = Field(
        None,
        description="Optional list of specific sheets to include"
    )
    filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional filtering parameters (e.g., job_type, salary_type, batch)"
    )


class ExportHistoryResponse(BaseModel):
    """
    Metadata representation of an exported Excel workbook deliverable.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    export_type: str
    record_count: int
    file_size_bytes: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    download_url: Optional[str] = None


class ExportListResponse(BaseModel):
    """
    Paginated collection of past export history records.
    """
    items: List[ExportHistoryResponse]
    total: int

