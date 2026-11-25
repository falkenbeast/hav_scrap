"""
Analytics & Salary Intelligence API Routes.
Exposes multi-dimensional placement analytics, company rankings,
salary distributions, and eligibility criteria insights.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.analytics_service import AnalyticsService
from app.services.salary_intelligence_service import SalaryIntelligenceService
from app.schemas.stats import DashboardStatsResponse, SalaryDistributionBracket, TopCompanyStat
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
    CompanyRankingsResponse,
    SalaryDistributionResponse,
    OpportunityDistributionResponse,
    LocationDistributionItem,
    OpportunityTrendsResponse,
    EligibilityInsightsResponse,
    SalaryIntelligenceResponse,
    AnalyticsFiltersResponse,
)

router = APIRouter(prefix="/analytics", tags=["Analytics & Salary Intelligence"])


@router.get("/overview", response_model=AnalyticsOverviewResponse, summary="Get placement analytics overview & KPIs")
def get_analytics_overview(
    company: Optional[str] = Query(None, description="Filter by company name"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    location: Optional[str] = Query(None, description="Filter by location"),
    salary_type: Optional[str] = Query(None, description="Filter by salary type"),
    start_date: Optional[str] = Query(None, description="Filter posted start date (ISO)"),
    end_date: Optional[str] = Query(None, description="Filter posted end date (ISO)"),
    is_internship: Optional[bool] = Query(None, description="Filter internships vs full-time"),
    db: Session = Depends(get_db)
):
    """
    Computes placement statistics: total companies, jobs, full-time vs internship split,
    highest/lowest/average/median CTC (excluding stipends/invalid records), and data transparency health.
    """
    return AnalyticsService.get_overview(
        db,
        company=company,
        job_type=job_type,
        location=location,
        salary_type=salary_type,
        start_date=start_date,
        end_date=end_date,
        is_internship=is_internship
    )


@router.get("/company-rankings", response_model=CompanyRankingsResponse, summary="Get ranked recruiter league table")
def get_company_rankings(
    sort_by: str = Query("highest_ctc", description="Sort by: highest_ctc, average_ctc, opportunities_count, internship_count"),
    order: str = Query("desc", description="Sort order: desc or asc"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    company: Optional[str] = Query(None, description="Filter by company name"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    db: Session = Depends(get_db)
):
    """
    Returns ranked companies based on verified compensation or volume,
    excluding ambiguous and missing records from rankings.
    """
    return SalaryIntelligenceService.get_company_rankings(
        db,
        sort_by=sort_by,
        order=order,
        page=page,
        page_size=page_size,
        company=company,
        job_type=job_type
    )


@router.get("/salary-distribution", response_model=SalaryDistributionResponse, summary="Get LPA distribution brackets")
def get_salary_distribution(
    company: Optional[str] = Query(None, description="Filter by company name"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    location: Optional[str] = Query(None, description="Filter by location"),
    start_date: Optional[str] = Query(None, description="Filter start date"),
    end_date: Optional[str] = Query(None, description="Filter end date"),
    db: Session = Depends(get_db)
):
    """
    Classifies full-time packages into 7 standard LPA tiers:
    Below 3 LPA, 3–5 LPA, 5–8 LPA, 8–12 LPA, 12–20 LPA, 20–30 LPA, Above 30 LPA.
    """
    return AnalyticsService.get_salary_distribution(
        db,
        company=company,
        job_type=job_type,
        location=location,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/opportunity-trends", response_model=OpportunityTrendsResponse, summary="Get monthly discovery & deadline timelines")
def get_opportunity_trends(
    company: Optional[str] = Query(None, description="Filter by company name"),
    db: Session = Depends(get_db)
):
    """
    Returns monthly posting discovery volumes and upcoming deadline timelines.
    """
    return AnalyticsService.get_opportunity_trends(db, company=company)


@router.get("/location-distribution", response_model=List[LocationDistributionItem], summary="Get opportunities by tech hub location")
def get_location_distribution(
    limit: int = Query(10, ge=1, le=50, description="Maximum locations to return"),
    company: Optional[str] = Query(None, description="Filter by company name"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    db: Session = Depends(get_db)
):
    """
    Aggregates job density across operating corporate cities and tech hubs.
    """
    return AnalyticsService.get_location_distribution(
        db,
        limit=limit,
        company=company,
        job_type=job_type
    )


@router.get("/job-type-distribution", response_model=OpportunityDistributionResponse, summary="Get employment & work mode breakdown")
def get_job_type_distribution(
    company: Optional[str] = Query(None, description="Filter by company name"),
    db: Session = Depends(get_db)
):
    """
    Returns full-time vs internship split and work-mode distribution (Remote/Hybrid/Onsite).
    """
    return AnalyticsService.get_job_type_distribution(db, company=company)


@router.get("/eligibility-insights", response_model=EligibilityInsightsResponse, summary="Get academic & branch criteria breakdown")
def get_eligibility_insights(
    company: Optional[str] = Query(None, description="Filter by company name"),
    db: Session = Depends(get_db)
):
    """
    Analyzes branch distribution, CGPA cutoffs, backlog allowances, and batch targets.
    """
    return AnalyticsService.get_eligibility_insights(db, company=company)


@router.get("/salary-intelligence", response_model=SalaryIntelligenceResponse, summary="Granular salary comparison table")
def get_salary_intelligence_records(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("salary_lpa", description="Sort column: salary_lpa, company_name, minimum_ctc, maximum_ctc, fixed_ctc"),
    sort_order: str = Query("desc", description="Sort order: desc or asc"),
    company: Optional[str] = Query(None, description="Filter by company name"),
    role: Optional[str] = Query(None, description="Filter by role title"),
    salary_type: Optional[str] = Query(None, description="Filter by salary type"),
    search: Optional[str] = Query(None, description="Text search across recruiters and titles"),
    job_type: Optional[str] = Query(None, description="Filter by job classification"),
    location: Optional[str] = Query(None, description="Filter by work location"),
    db: Session = Depends(get_db)
):
    """
    Delivers detailed compensation listings with fixed vs variable split,
    normalized LPA packages, and original portal salary text.
    """
    return SalaryIntelligenceService.get_salary_records(
        db,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
        company=company,
        role=role,
        salary_type=salary_type,
        search=search,
        job_type=job_type,
        location=location
    )


@router.get("/filters", response_model=AnalyticsFiltersResponse, summary="Get distinct filter options for UI selectors")
def get_analytics_filters(db: Session = Depends(get_db)):
    """
    Provides dynamic filter values populated directly from SQLite database.
    """
    return AnalyticsService.get_filters(db)


# ==============================================================================
# Legacy routes preserved for Phase 1-3 compatibility
# ==============================================================================
@router.get("/dashboard-stats", response_model=DashboardStatsResponse)
def get_dashboard_kpis(db: Session = Depends(get_db)):
    return AnalyticsService.get_dashboard_stats(db)


@router.get("/top-companies", response_model=List[TopCompanyStat])
def get_top_companies(limit: int = 8, db: Session = Depends(get_db)):
    return AnalyticsService.get_top_companies(db, limit=limit)
