from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DashboardStatsResponse(BaseModel):
    """
    Schema matching Section 5 required fields for GET /api/dashboard/stats
    with aliases for frontend compatibility.
    """
    total_companies: int = Field(0, description="Total unique corporate entities indexed")
    total_jobs: int = Field(0, description="Total verified job notices recorded")
    average_ctc: float = Field(0.0, description="Mean CTC in LPA across verified opportunities")
    highest_ctc: float = Field(0.0, description="Peak CTC recorded in LPA")
    lowest_ctc: float = Field(0.0, description="Floor CTC recorded in LPA")
    full_time_jobs: int = Field(0, description="Number of direct FTE opportunities")
    internship_jobs: int = Field(0, description="Number of internship opportunities (summer/6M)")
    total_scraping_sessions: int = Field(0, description="Total recorded scraping sessions")

    # Frontend-compatible aliases
    avg_salary_lpa: Optional[float] = None
    highest_salary_lpa: Optional[float] = None
    last_scrape_time: Optional[str] = None
    active_sessions: Optional[int] = 0

    model_config = ConfigDict(populate_by_name=True)


class SalaryDistributionBracket(BaseModel):
    bracket: str
    count: int
    percentage: float


class TopCompanyStat(BaseModel):
    company_name: str
    job_count: int
    max_ctc: float
    avg_ctc: float


class ActivityItem(BaseModel):
    id: str
    type: str
    title: str
    description: str
    timestamp: str
    badge: Optional[str] = None
    badgeVariant: Optional[str] = "cyan"

