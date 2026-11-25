from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class CompanyBase(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=255, description="Official company / recruiter name")
    website: Optional[str] = Field(None, max_length=512, description="Official corporate or portal website")
    source_url: Optional[str] = Field(None, max_length=1024, description="Haveloc portal origin link")


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    company_name: Optional[str] = Field(None, min_length=1, max_length=255)
    website: Optional[str] = None
    source_url: Optional[str] = None


class CompanyResponse(CompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    total_jobs: Optional[int] = 0
    max_ctc: Optional[float] = None
    avg_ctc: Optional[float] = None
    job_role: Optional[str] = None
    job_roles: Optional[List[str]] = []
    location: Optional[str] = None
    locations: Optional[List[str]] = []
    job_type: Optional[str] = None
    job_status: Optional[str] = None
    posted_date: Optional[str] = None


class CompanyDetailResponse(CompanyResponse):
    jobs: List["JobOpportunityResponse"] = []  # populated with associated job opportunities


class CompanyPaginationResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[CompanyResponse]


# Circular reference import support
from app.schemas.job import JobOpportunityResponse
CompanyDetailResponse.model_rebuild()
