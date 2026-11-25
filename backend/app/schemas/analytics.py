"""
Analytics & Salary Intelligence Pydantic Schemas.
Defines structured responses for KPIs, distributions, company rankings,
and eligibility insights.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class AnalyticsOverviewResponse(BaseModel):
    """
    Core KPI telemetry across verified placement intelligence corpus.
    """
    total_companies: int
    total_jobs: int
    total_fulltime: int
    total_internships: int
    disclosed_salaries: int
    undisclosed_salaries: int
    highest_ctc_lpa: Optional[float] = None
    average_ctc_lpa: Optional[float] = None
    median_ctc_lpa: Optional[float] = None
    lowest_ctc_lpa: Optional[float] = None
    companies_offering_internships: int
    data_transparency: Dict[str, Any] = Field(default_factory=dict)


class CompanyRankingItem(BaseModel):
    """
    Aggregated corporate intelligence metrics for ranking tables.
    """
    company_name: str
    company_id: Optional[int] = None
    opportunities_count: int
    highest_ctc_lpa: Optional[float] = None
    average_ctc_lpa: Optional[float] = None
    lowest_ctc_lpa: Optional[float] = None
    offers_internships: bool
    internships_count: int
    disclosed_salary_records: int


class CompanyRankingsResponse(BaseModel):
    items: List[CompanyRankingItem]
    total: int
    page: int
    page_size: int


class SalaryBracketItem(BaseModel):
    bracket: str
    count: int
    percentage: float
    average_salary: Optional[float] = None
    fixed_ctc_average: Optional[float] = None
    max_ctc_average: Optional[float] = None


class SalaryDistributionResponse(BaseModel):
    brackets: List[SalaryBracketItem]
    median_salary: Optional[float] = None
    highest_salary: Optional[float] = None
    lowest_salary: Optional[float] = None
    total_disclosed: int


class SalaryIntelligenceRecord(BaseModel):
    id: int
    company_name: str
    job_role: str
    job_title: str
    minimum_ctc: Optional[float] = None
    maximum_ctc: Optional[float] = None
    fixed_ctc: Optional[float] = None
    variable_ctc: Optional[float] = None
    normalized_salary_lpa: Optional[float] = None
    original_salary_text: Optional[str] = None
    salary_type: Optional[str] = None
    job_type: Optional[str] = None
    work_mode: Optional[str] = None
    location: Optional[str] = None
    validation_status: Optional[str] = None


class SalaryIntelligenceResponse(BaseModel):
    items: List[SalaryIntelligenceRecord]
    total: int
    page: int
    page_size: int
    total_pages: int
    salary_disclosure_percentage: float
    records_needing_review_count: int


class LocationDistributionItem(BaseModel):
    location: str
    count: int
    percentage: float


class JobTypeDistributionItem(BaseModel):
    job_type: str
    count: int
    percentage: float


class WorkModeDistributionItem(BaseModel):
    work_mode: str
    count: int
    percentage: float


class OpportunityDistributionResponse(BaseModel):
    job_types: List[JobTypeDistributionItem]
    work_modes: List[WorkModeDistributionItem]


class TrendPoint(BaseModel):
    period: str
    count: int


class OpportunityTrendsResponse(BaseModel):
    discovery_trends: List[TrendPoint]
    deadline_trends: List[TrendPoint]


class BranchEligibilityItem(BaseModel):
    branch: str
    count: int


class CgpaRequirementItem(BaseModel):
    bracket: str
    count: int


class BacklogRequirementItem(BaseModel):
    criteria: str
    count: int


class BatchRequirementItem(BaseModel):
    batch: str
    count: int


class EligibilityInsightsResponse(BaseModel):
    branch_distribution: List[BranchEligibilityItem]
    cgpa_distribution: List[CgpaRequirementItem]
    backlog_requirements: List[BacklogRequirementItem]
    batch_distribution: List[BatchRequirementItem]
    incomplete_eligibility_count: int
    incomplete_eligibility_percentage: float


class AnalyticsFiltersResponse(BaseModel):
    companies: List[Dict[str, Any]]
    locations: List[str]
    job_types: List[str]
    salary_types: List[str]
    batches: List[str]

