"""
Analytics Management Service.
Computes multi-dimensional placement statistics, salary distributions,
location analytics, temporal trends, and eligibility insights from SQLite.
"""
import logging
from datetime import datetime, date, timezone
from typing import Dict, Any, List, Optional
from collections import Counter

try:
    from sqlalchemy.orm import Session
    from sqlalchemy import select, func, and_, or_, desc, asc
except ImportError:
    Session = Any
    select = None
    func = None
    and_ = None
    or_ = None
    desc = None
    asc = None

try:
    from app.models.company import Company
    from app.models.job import JobOpportunity
    from app.models.session import ScrapingSession
except ImportError:
    Company = Any
    JobOpportunity = Any
    ScrapingSession = Any
from app.schemas.stats import DashboardStatsResponse, SalaryDistributionBracket, TopCompanyStat
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
    SalaryBracketItem,
    SalaryDistributionResponse,
    LocationDistributionItem,
    JobTypeDistributionItem,
    WorkModeDistributionItem,
    OpportunityDistributionResponse,
    TrendPoint,
    OpportunityTrendsResponse,
    BranchEligibilityItem,
    CgpaRequirementItem,
    BacklogRequirementItem,
    BatchRequirementItem,
    EligibilityInsightsResponse,
    AnalyticsFiltersResponse,
)

logger = logging.getLogger("hav_scrap")


class AnalyticsService:
    """
    Central analytics calculation engine querying verified database records.
    Strictly avoids fabricated metrics, isolates stipends, and ignores NULL salaries.
    """

    @staticmethod
    def _apply_base_filters(
        stmt,
        company: Optional[str] = None,
        job_type: Optional[str] = None,
        location: Optional[str] = None,
        salary_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        is_internship: Optional[bool] = None,
    ):
        """
        Applies standardized filtering parameters to JobOpportunity queries.
        """
        conditions = []

        if company:
            conditions.append(
                or_(
                    Company.company_name.ilike(f"%{company}%"),
                    JobOpportunity.cleaned_company_name.ilike(f"%{company}%")
                )
            )

        if job_type:
            conditions.append(JobOpportunity.job_type.ilike(f"%{job_type}%"))

        if location:
            conditions.append(JobOpportunity.location.ilike(f"%{location}%"))

        if salary_type:
            conditions.append(JobOpportunity.salary_type == salary_type)

        if start_date:
            try:
                dt_start = datetime.fromisoformat(start_date.replace("Z", ""))
                conditions.append(
                    or_(
                        JobOpportunity.posted_date >= dt_start,
                        JobOpportunity.created_at >= dt_start
                    )
                )
            except Exception as ex:
                logger.warning(f"Invalid start_date filter '{start_date}': {ex}")

        if end_date:
            try:
                dt_end = datetime.fromisoformat(end_date.replace("Z", ""))
                conditions.append(
                    or_(
                        JobOpportunity.posted_date <= dt_end,
                        JobOpportunity.created_at <= dt_end
                    )
                )
            except Exception as ex:
                logger.warning(f"Invalid end_date filter '{end_date}': {ex}")

        if is_internship is True:
            conditions.append(
                or_(
                    JobOpportunity.salary_type == "INTERNSHIP_STIPEND",
                    JobOpportunity.stipend_amount.is_not(None),
                    JobOpportunity.job_type.ilike("%intern%")
                )
            )
        elif is_internship is False:
            conditions.append(
                and_(
                    or_(JobOpportunity.salary_type.is_(None), JobOpportunity.salary_type != "INTERNSHIP_STIPEND"),
                    JobOpportunity.stipend_amount.is_(None),
                    or_(JobOpportunity.job_type.is_(None), ~JobOpportunity.job_type.ilike("%intern%"))
                )
            )

        if conditions:
            stmt = stmt.where(and_(*conditions))

        return stmt

    # ==========================================================================
    # 1. Overview KPIs
    # ==========================================================================
    @classmethod
    def get_overview(
        cls,
        db: Session,
        company: Optional[str] = None,
        job_type: Optional[str] = None,
        location: Optional[str] = None,
        salary_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        is_internship: Optional[bool] = None,
    ) -> AnalyticsOverviewResponse:
        """
        Calculates high-level placement KPIs, accurate averages/medians,
        and data transparency telemetry.
        """
        base_stmt = select(JobOpportunity).join(Company)
        base_stmt = cls._apply_base_filters(
            base_stmt,
            company=company,
            job_type=job_type,
            location=location,
            salary_type=salary_type,
            start_date=start_date,
            end_date=end_date,
            is_internship=is_internship,
        )

        jobs = db.execute(base_stmt).scalars().all()
        total_jobs = len(jobs)

        company_ids = {j.company_id for j in jobs if j.company_id}
        total_companies = len(company_ids)

        if total_jobs == 0:
            return AnalyticsOverviewResponse(
                total_companies=0,
                total_jobs=0,
                total_fulltime=0,
                total_internships=0,
                disclosed_salaries=0,
                undisclosed_salaries=0,
                highest_ctc_lpa=None,
                average_ctc_lpa=None,
                median_ctc_lpa=None,
                lowest_ctc_lpa=None,
                companies_offering_internships=0,
                data_transparency={
                    "disclosed_salary_count": 0,
                    "undisclosed_salary_count": 0,
                    "records_needing_review": 0,
                    "invalid_salary_count": 0,
                    "last_processing_timestamp": None,
                }
            )

        internship_jobs = []
        fulltime_jobs = []

        for j in jobs:
            is_intern = (
                j.salary_type == "INTERNSHIP_STIPEND" or
                j.stipend_amount is not None or
                (j.job_type and "intern" in j.job_type.lower())
            )
            if is_intern:
                internship_jobs.append(j)
            else:
                fulltime_jobs.append(j)

        total_internships = len(internship_jobs)
        total_fulltime = len(fulltime_jobs)

        intern_comp_ids = {j.company_id for j in internship_jobs if j.company_id}
        companies_offering_internships = len(intern_comp_ids)

        valid_salaries: List[float] = []
        undisclosed_count = 0
        records_needing_review = 0
        invalid_count = 0

        for j in fulltime_jobs:
            if j.validation_status == "INVALID":
                invalid_count += 1
                continue
            if j.validation_status == "NEEDS_REVIEW" or j.salary_type == "NEEDS_REVIEW":
                records_needing_review += 1
                continue

            if j.salary_lpa is not None and j.salary_lpa > 0:
                valid_salaries.append(float(j.salary_lpa))
            else:
                undisclosed_count += 1

        disclosed_salaries = len(valid_salaries)

        if valid_salaries:
            valid_salaries.sort()
            lowest_ctc = round(valid_salaries[0], 2)
            highest_ctc = round(valid_salaries[-1], 2)
            avg_ctc = round(sum(valid_salaries) / len(valid_salaries), 2)

            n = len(valid_salaries)
            if n % 2 == 1:
                median_ctc = round(valid_salaries[n // 2], 2)
            else:
                median_ctc = round((valid_salaries[n // 2 - 1] + valid_salaries[n // 2]) / 2.0, 2)
        else:
            lowest_ctc = None
            highest_ctc = None
            avg_ctc = None
            median_ctc = None

        min_utc = datetime.min.replace(tzinfo=timezone.utc)
        latest_update = max(
            [j.updated_at for j in jobs if j.updated_at] + [min_utc]
        )
        last_ts = latest_update.isoformat() if latest_update != min_utc else None

        return AnalyticsOverviewResponse(
            total_companies=total_companies,
            total_jobs=total_jobs,
            total_fulltime=total_fulltime,
            total_internships=total_internships,
            disclosed_salaries=disclosed_salaries,
            undisclosed_salaries=undisclosed_count,
            highest_ctc_lpa=highest_ctc,
            average_ctc_lpa=avg_ctc,
            median_ctc_lpa=median_ctc,
            lowest_ctc_lpa=lowest_ctc,
            companies_offering_internships=companies_offering_internships,
            data_transparency={
                "disclosed_salary_count": disclosed_salaries,
                "undisclosed_salary_count": undisclosed_count,
                "records_needing_review": records_needing_review,
                "invalid_salary_count": invalid_count,
                "last_processing_timestamp": last_ts,
            }
        )

    # ==========================================================================
    # 2. Salary Distribution Brackets
    # ==========================================================================
    @classmethod
    def get_salary_distribution(
        cls,
        db: Session,
        company: Optional[str] = None,
        job_type: Optional[str] = None,
        location: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> SalaryDistributionResponse:
        """
        Classifies full-time disclosed CTC into 7 designated LPA tiers:
        Below 3 LPA, 3–5 LPA, 5–8 LPA, 8–12 LPA, 12–20 LPA, 20–30 LPA, Above 30 LPA.
        """
        base_stmt = select(JobOpportunity).join(Company).where(
            and_(
                JobOpportunity.salary_lpa.is_not(None),
                JobOpportunity.salary_lpa > 0,
                or_(JobOpportunity.salary_type.is_(None), JobOpportunity.salary_type != "INTERNSHIP_STIPEND"),
                JobOpportunity.stipend_amount.is_(None),
                or_(JobOpportunity.validation_status.is_(None), JobOpportunity.validation_status == "VALID")
            )
        )
        base_stmt = cls._apply_base_filters(
            base_stmt,
            company=company,
            job_type=job_type,
            location=location,
            start_date=start_date,
            end_date=end_date,
            is_internship=False
        )

        jobs = db.execute(base_stmt).scalars().all()

        # Defense-in-depth: enforce strict full-time and valid status filtering
        valid_jobs = [
            j for j in jobs
            if (
                j.salary_lpa is not None
                and j.salary_lpa > 0
                and j.salary_type != "INTERNSHIP_STIPEND"
                and j.stipend_amount is None
                and (not j.job_type or "intern" not in j.job_type.lower())
                and (j.validation_status is None or j.validation_status == "VALID")
                and (j.salary_type != "NEEDS_REVIEW")
            )
        ]
        total_disclosed = len(valid_jobs)

        bracket_defs = [
            ("Below 3 LPA", 0.0, 3.0),
            ("3–5 LPA", 3.0, 5.0),
            ("5–8 LPA", 5.0, 8.0),
            ("8–12 LPA", 8.0, 12.0),
            ("12–20 LPA", 12.0, 20.0),
            ("20–30 LPA", 20.0, 30.0),
            ("Above 30 LPA", 30.0, 9999.0),
        ]

        bracket_items: List[SalaryBracketItem] = []
        all_salaries = []

        for label, lower, upper in bracket_defs:
            in_tier = [
                j for j in valid_jobs
                if lower <= (j.salary_lpa or 0.0) < upper
            ]
            count = len(in_tier)
            pct = round((count / total_disclosed * 100), 1) if total_disclosed > 0 else 0.0

            salaries_in_tier = [j.salary_lpa for j in in_tier if j.salary_lpa is not None]
            fixed_in_tier = [j.fixed_ctc for j in in_tier if j.fixed_ctc is not None]
            max_in_tier = [j.maximum_ctc for j in in_tier if j.maximum_ctc is not None]

            avg_salary = round(sum(salaries_in_tier) / count, 2) if count > 0 else None
            avg_fixed = round(sum(fixed_in_tier) / len(fixed_in_tier), 2) if fixed_in_tier else None
            avg_max = round(sum(max_in_tier) / len(max_in_tier), 2) if max_in_tier else None

            all_salaries.extend(salaries_in_tier)

            bracket_items.append(
                SalaryBracketItem(
                    bracket=label,
                    count=count,
                    percentage=pct,
                    average_salary=avg_salary,
                    fixed_ctc_average=avg_fixed,
                    max_ctc_average=avg_max,
                )
            )

        if all_salaries:
            all_salaries.sort()
            lowest_s = round(all_salaries[0], 2)
            highest_s = round(all_salaries[-1], 2)
            n = len(all_salaries)
            if n % 2 == 1:
                median_s = round(all_salaries[n // 2], 2)
            else:
                median_s = round((all_salaries[n // 2 - 1] + all_salaries[n // 2]) / 2.0, 2)
        else:
            lowest_s = None
            highest_s = None
            median_s = None

        return SalaryDistributionResponse(
            brackets=bracket_items,
            median_salary=median_s,
            highest_salary=highest_s,
            lowest_salary=lowest_s,
            total_disclosed=total_disclosed,
        )

    # ==========================================================================
    # 3. Location Distribution
    # ==========================================================================
    @classmethod
    def get_location_distribution(
        cls,
        db: Session,
        limit: int = 10,
        company: Optional[str] = None,
        job_type: Optional[str] = None,
    ) -> List[LocationDistributionItem]:
        """
        Aggregates opportunity count per verified operating work location.
        """
        stmt = select(JobOpportunity).join(Company)
        stmt = cls._apply_base_filters(stmt, company=company, job_type=job_type)
        jobs = db.execute(stmt).scalars().all()

        total = len(jobs)
        if total == 0:
            return []

        counts = Counter()
        for j in jobs:
            loc = (j.location or "Undisclosed").strip()
            cities = [c.strip() for c in loc.replace("/", ",").split(",") if c.strip()]
            if not cities:
                counts["Undisclosed"] += 1
            else:
                for c in cities:
                    counts[c] += 1

        top_locs = counts.most_common(limit)
        return [
            LocationDistributionItem(
                location=loc,
                count=cnt,
                percentage=round((cnt / total * 100), 1)
            )
            for loc, cnt in top_locs
        ]

    # ==========================================================================
    # 4. Job Type & Work Mode Distribution
    # ==========================================================================
    @classmethod
    def get_job_type_distribution(
        cls,
        db: Session,
        company: Optional[str] = None,
    ) -> OpportunityDistributionResponse:
        """
        Calculates employment type (FTE vs Internship) and work mode breakdown.
        """
        stmt = select(JobOpportunity).join(Company)
        stmt = cls._apply_base_filters(stmt, company=company)
        jobs = db.execute(stmt).scalars().all()

        total = len(jobs)
        if total == 0:
            return OpportunityDistributionResponse(job_types=[], work_modes=[])

        type_counter = Counter()
        mode_counter = Counter()

        for j in jobs:
            if j.salary_type == "INTERNSHIP_STIPEND" or j.stipend_amount is not None:
                type_counter["Internship"] += 1
            elif j.job_type:
                j_lower = j.job_type.lower()
                if "intern" in j_lower and "fte" in j_lower:
                    type_counter["6M Intern + FTE"] += 1
                elif "intern" in j_lower:
                    type_counter["Internship"] += 1
                else:
                    type_counter[j.job_type] += 1
            else:
                type_counter["Full-Time"] += 1

            mode = (j.work_mode or "Onsite").strip()
            mode_counter[mode] += 1

        job_types = [
            JobTypeDistributionItem(
                job_type=k,
                count=v,
                percentage=round((v / total * 100), 1)
            )
            for k, v in type_counter.most_common()
        ]

        work_modes = [
            WorkModeDistributionItem(
                work_mode=k,
                count=v,
                percentage=round((v / total * 100), 1)
            )
            for k, v in mode_counter.most_common()
        ]

        return OpportunityDistributionResponse(job_types=job_types, work_modes=work_modes)

    # ==========================================================================
    # 5. Opportunity Trends (Monthly & Deadlines)
    # ==========================================================================
    @classmethod
    def get_opportunity_trends(
        cls,
        db: Session,
        company: Optional[str] = None,
    ) -> OpportunityTrendsResponse:
        """
        Aggregates monthly discovery volumes and upcoming deadline timelines.
        """
        stmt = select(JobOpportunity).join(Company)
        stmt = cls._apply_base_filters(stmt, company=company)
        jobs = db.execute(stmt).scalars().all()

        discovery_counter = Counter()
        deadline_counter = Counter()

        for j in jobs:
            d = j.posted_date or j.created_at
            if d:
                period_str = d.strftime("%Y-%m")
                discovery_counter[period_str] += 1

            if j.application_deadline:
                dl_str = j.application_deadline.strftime("%Y-%m")
                deadline_counter[dl_str] += 1

        disc_sorted = [
            TrendPoint(period=k, count=discovery_counter[k])
            for k in sorted(discovery_counter.keys())
        ]

        dead_sorted = [
            TrendPoint(period=k, count=deadline_counter[k])
            for k in sorted(deadline_counter.keys())
        ]

        return OpportunityTrendsResponse(
            discovery_trends=disc_sorted,
            deadline_trends=dead_sorted
        )

    # ==========================================================================
    # 6. Eligibility Insights
    # ==========================================================================
    @classmethod
    def get_eligibility_insights(
        cls,
        db: Session,
        company: Optional[str] = None,
    ) -> EligibilityInsightsResponse:
        """
        Analyzes academic requirements, branch criteria, and CGPA thresholds.
        """
        stmt = select(JobOpportunity).join(Company)
        stmt = cls._apply_base_filters(stmt, company=company)
        jobs = db.execute(stmt).scalars().all()

        total = len(jobs)
        if total == 0:
            return EligibilityInsightsResponse(
                branch_distribution=[],
                cgpa_distribution=[],
                backlog_requirements=[],
                batch_distribution=[],
                incomplete_eligibility_count=0,
                incomplete_eligibility_percentage=0.0
            )

        branch_counter = Counter()
        cgpa_counter = Counter()
        backlog_counter = Counter()
        batch_counter = Counter()
        incomplete_count = 0

        for j in jobs:
            has_branch = bool(j.eligible_branches and j.eligible_branches.strip())
            has_cgpa = bool(j.minimum_cgpa is not None and j.minimum_cgpa > 0)
            if not has_branch and not has_cgpa and not j.eligibility:
                incomplete_count += 1

            if j.eligible_branches:
                raw_branches = [b.strip() for b in j.eligible_branches.replace("/", ",").split(",") if b.strip()]
                for b in raw_branches:
                    branch_counter[b] += 1
            else:
                branch_counter["Unrestricted / All"] += 1

            cgpa = j.minimum_cgpa
            if cgpa is None or cgpa <= 0:
                cgpa_counter["No Minimum Specified"] += 1
            elif cgpa < 6.0:
                cgpa_counter["< 6.0 CGPA"] += 1
            elif cgpa < 6.5:
                cgpa_counter["6.0 – 6.5 CGPA"] += 1
            elif cgpa < 7.0:
                cgpa_counter["6.5 – 7.0 CGPA"] += 1
            elif cgpa < 7.5:
                cgpa_counter["7.0 – 7.5 CGPA"] += 1
            elif cgpa < 8.0:
                cgpa_counter["7.5 – 8.0 CGPA"] += 1
            else:
                cgpa_counter["8.0+ CGPA"] += 1

            bk = (j.backlog_criteria or "No Active Backlogs").strip()
            backlog_counter[bk] += 1

            bt = (j.batch or "Current Cohort").strip()
            batch_counter[bt] += 1

        cgpa_order = [
            "< 6.0 CGPA", "6.0 – 6.5 CGPA", "6.5 – 7.0 CGPA",
            "7.0 – 7.5 CGPA", "7.5 – 8.0 CGPA", "8.0+ CGPA", "No Minimum Specified"
        ]
        cgpa_items = [
            CgpaRequirementItem(bracket=k, count=cgpa_counter[k])
            for k in cgpa_order if cgpa_counter[k] > 0
        ]

        branch_items = [
            BranchEligibilityItem(branch=k, count=v)
            for k, v in branch_counter.most_common(12)
        ]

        backlog_items = [
            BacklogRequirementItem(criteria=k, count=v)
            for k, v in backlog_counter.most_common(6)
        ]

        batch_items = [
            BatchRequirementItem(batch=k, count=v)
            for k, v in batch_counter.most_common(6)
        ]

        incomplete_pct = round((incomplete_count / total * 100), 1)

        return EligibilityInsightsResponse(
            branch_distribution=branch_items,
            cgpa_distribution=cgpa_items,
            backlog_requirements=backlog_items,
            batch_distribution=batch_items,
            incomplete_eligibility_count=incomplete_count,
            incomplete_eligibility_percentage=incomplete_pct
        )

    # ==========================================================================
    # 7. Available Filter Values
    # ==========================================================================
    @classmethod
    def get_filters(cls, db: Session) -> AnalyticsFiltersResponse:
        """
        Retrieves available distinct filter values for the UI dropdowns.
        """
        comps = db.execute(select(Company.id, Company.company_name).order_by(Company.company_name.asc())).all()
        comp_list = [{"id": c[0], "name": c[1]} for c in comps]

        raw_locs = db.execute(select(JobOpportunity.location).where(JobOpportunity.location.is_not(None)).distinct()).scalars().all()
        loc_set = set()
        for loc in raw_locs:
            if loc:
                for part in loc.replace("/", ",").split(","):
                    p = part.strip()
                    if p:
                        loc_set.add(p)

        jtypes = db.execute(select(JobOpportunity.job_type).where(JobOpportunity.job_type.is_not(None)).distinct()).scalars().all()
        job_types = sorted(list({jt.strip() for jt in jtypes if jt and jt.strip()}))

        stypes = db.execute(select(JobOpportunity.salary_type).where(JobOpportunity.salary_type.is_not(None)).distinct()).scalars().all()
        salary_types = sorted(list({st.strip() for st in stypes if st and st.strip()}))

        batches_raw = db.execute(select(JobOpportunity.batch).where(JobOpportunity.batch.is_not(None)).distinct()).scalars().all()
        batches = sorted(list({b.strip() for b in batches_raw if b and b.strip()}))

        return AnalyticsFiltersResponse(
            companies=comp_list,
            locations=sorted(list(loc_set)),
            job_types=job_types,
            salary_types=salary_types,
            batches=batches
        )

    # ==========================================================================
    # Legacy helper preservation for Phase 1-3 compatibility
    # ==========================================================================
    @classmethod
    def get_dashboard_stats(cls, db: Session) -> DashboardStatsResponse:
        overview = cls.get_overview(db)
        sessions_total = db.query(func.count(ScrapingSession.id)).scalar() or 0
        latest_sess = db.query(ScrapingSession).order_by(ScrapingSession.started_at.desc()).first()

        return DashboardStatsResponse(
            total_companies=overview.total_companies,
            total_jobs=overview.total_jobs,
            average_ctc=overview.average_ctc_lpa or 0.0,
            highest_ctc=overview.highest_ctc_lpa or 0.0,
            lowest_ctc=overview.lowest_ctc_lpa or 0.0,
            full_time_jobs=overview.total_fulltime,
            internship_jobs=overview.total_internships,
            total_scraping_sessions=sessions_total,
            avg_salary_lpa=overview.average_ctc_lpa or 0.0,
            highest_salary_lpa=overview.highest_ctc_lpa or 0.0,
            last_scrape_time=latest_sess.started_at.strftime("%Y-%m-%d %H:%M") if latest_sess else None,
            active_sessions=0
        )

    @classmethod
    def get_top_companies(cls, db: Session, limit: int = 8) -> List[TopCompanyStat]:
        from app.services.salary_intelligence_service import SalaryIntelligenceService
        rankings = SalaryIntelligenceService.get_company_rankings(db, sort_by="highest_ctc", page=1, page_size=limit)
        return [
            TopCompanyStat(
                company_name=r.company_name,
                job_count=r.opportunities_count,
                max_ctc=r.highest_ctc_lpa or 0.0,
                avg_ctc=r.average_ctc_lpa or 0.0
            )
            for r in rankings.items
        ]
