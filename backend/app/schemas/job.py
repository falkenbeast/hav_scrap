from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class JobOpportunityBase(BaseModel):
    job_title: str = Field(..., min_length=1, max_length=255, description="Role title / designation")
    job_role: Optional[str] = Field(None, max_length=255, description="Profile domain or specialization")
    job_description: Optional[str] = Field(None, description="Detailed job description and responsibilities")
    
    # Salary Attributes
    original_salary_text: Optional[str] = Field(None, max_length=500, description="Raw compensation clause string")
    minimum_ctc: Optional[float] = Field(None, ge=0, description="Minimum CTC in LPA")
    maximum_ctc: Optional[float] = Field(None, ge=0, description="Maximum CTC in LPA")
    fixed_ctc: Optional[float] = Field(None, ge=0, description="Fixed base compensation component")
    variable_ctc: Optional[float] = Field(None, ge=0, description="Variable / performance / stock bonus")
    joining_bonus: Optional[float] = Field(None, ge=0, description="Joining or sign-on bonus")
    salary_lpa: Optional[float] = Field(None, ge=0, description="Normalized total annual CTC in LPA")
    salary_unit: Optional[str] = Field("LPA", max_length=50, description="Currency and period unit")
    stipend_amount: Optional[float] = Field(None, ge=0, description="Internship stipend amount")
    stipend_min: Optional[float] = Field(None, ge=0, description="Minimum internship stipend amount")
    stipend_max: Optional[float] = Field(None, ge=0, description="Maximum internship stipend amount")
    original_stipend_text: Optional[str] = Field(None, max_length=255, description="Raw stipend string")
    stipend_period: Optional[str] = Field(None, max_length=50, description="Stipend interval: monthly, weekly")
    annualized_equivalent: Optional[float] = Field(None, ge=0, description="Computed annualized CTC for monthly salary")
    
    # Opportunity & Eligibility Details
    job_type: Optional[str] = Field(None, max_length=100, description="Classification: Full-Time, Internship, 6M+FTE")
    job_status: Optional[str] = Field(None, max_length=100, description="Portal status: Closed For Applications, etc.")
    work_mode: Optional[str] = Field(None, max_length=50, description="Work mode: Remote, Hybrid, Onsite")
    location: Optional[str] = Field(None, max_length=255, description="Office posting location or cities")
    eligibility: Optional[str] = Field(None, description="Degree and departmental eligibility guidelines")
    minimum_cgpa: Optional[float] = Field(None, ge=0, le=10.0, description="Cutoff CGPA threshold")
    eligible_branches: Optional[str] = Field(None, description="Comma-separated or JSON list of eligible branches")
    backlog_criteria: Optional[str] = Field(None, max_length=255, description="Allowed active/dead backlog policy")
    academic_criteria: Optional[str] = Field(None, description="Secondary/Higher secondary cutoff percentages")
    batch: Optional[str] = Field(None, max_length=50, description="Target graduating academic year")
    
    # Metadata & Tracking
    application_deadline: Optional[datetime] = Field(None, description="Application closing timestamp")
    date_of_visit: Optional[datetime] = Field(None, description="Date of company visit")
    posted_date: Optional[datetime] = Field(None, description="Original notice timestamp on portal")
    source_url: Optional[str] = Field(None, max_length=1024, description="Direct URL to posting on portal")
    extraction_status: Optional[str] = Field("PENDING", max_length=50, description="Details extraction state")
    last_verified_at: Optional[datetime] = Field(None, description="Timestamp of last successful extraction")


class JobOpportunityCreate(JobOpportunityBase):
    company_id: int = Field(..., description="Foreign key reference to parent Company")


class JobOpportunityUpdate(BaseModel):
    job_title: Optional[str] = None
    job_role: Optional[str] = None
    job_description: Optional[str] = None
    original_salary_text: Optional[str] = None
    minimum_ctc: Optional[float] = None
    maximum_ctc: Optional[float] = None
    fixed_ctc: Optional[float] = None
    variable_ctc: Optional[float] = None
    joining_bonus: Optional[float] = None
    salary_lpa: Optional[float] = None
    salary_unit: Optional[str] = None
    stipend_amount: Optional[float] = None
    stipend_period: Optional[str] = None
    annualized_equivalent: Optional[float] = None
    job_type: Optional[str] = None
    work_mode: Optional[str] = None
    location: Optional[str] = None
    eligibility: Optional[str] = None
    minimum_cgpa: Optional[float] = None
    eligible_branches: Optional[str] = None
    backlog_criteria: Optional[str] = None
    academic_criteria: Optional[str] = None
    batch: Optional[str] = None
    application_deadline: Optional[datetime] = None
    posted_date: Optional[datetime] = None
    source_url: Optional[str] = None
    extraction_status: Optional[str] = None
    last_verified_at: Optional[datetime] = None


class JobOpportunityResponse(JobOpportunityBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    company_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class JobSalaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    company_name: Optional[str] = None
    job_title: str
    original_salary_text: Optional[str] = None
    minimum_ctc: Optional[float] = None
    maximum_ctc: Optional[float] = None
    fixed_ctc: Optional[float] = None
    variable_ctc: Optional[float] = None
    joining_bonus: Optional[float] = None
    salary_lpa: Optional[float] = None
    salary_unit: Optional[str] = "LPA"
    stipend_amount: Optional[float] = None
    stipend_period: Optional[str] = None
    annualized_equivalent: Optional[float] = None
    job_type: Optional[str] = None
    last_verified_at: Optional[datetime] = None


class JobPaginationResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[JobOpportunityResponse]
