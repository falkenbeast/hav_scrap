from datetime import datetime
from typing import Dict, Any
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.job import JobOpportunity
from app.processors.duplicate_remover import DuplicateDetector


class QualityAnalyzer:
    """
    Computes system-wide data quality audits, validation health metrics,
    and completeness percentages across processed placement intelligence records.
    """

    @classmethod
    def generate_report(cls, db: Session) -> Dict[str, Any]:
        """
        Generates comprehensive quality report covering cleaning, validation,
        salary completeness, and duplicate detection.
        """
        # 1. Total Counts
        total_companies = db.execute(select(func.count(Company.id))).scalar() or 0
        total_jobs = db.execute(select(func.count(JobOpportunity.id))).scalar() or 0

        if total_jobs == 0:
            return {
                "total_companies": total_companies,
                "total_jobs": 0,
                "cleaned_records": 0,
                "records_needing_review": 0,
                "duplicate_companies_detected": 0,
                "duplicate_jobs_detected": 0,
                "records_without_salary": 0,
                "records_with_incomplete_eligibility": 0,
                "invalid_salary_entries": 0,
                "records_with_missing_source_urls": 0,
                "data_quality_percentage": 100.0,
                "generated_at": datetime.utcnow().isoformat() + "Z",
            }

        # 2. Validation Statuses
        cleaned_records = db.execute(
            select(func.count(JobOpportunity.id)).where(JobOpportunity.cleaned_job_title.is_not(None))
        ).scalar() or 0

        valid_records = db.execute(
            select(func.count(JobOpportunity.id)).where(JobOpportunity.validation_status == "VALID")
        ).scalar() or 0

        records_needing_review = db.execute(
            select(func.count(JobOpportunity.id)).where(
                or_(
                    JobOpportunity.validation_status == "NEEDS_REVIEW",
                    JobOpportunity.salary_type == "NEEDS_REVIEW"
                )
            )
        ).scalar() or 0

        invalid_records = db.execute(
            select(func.count(JobOpportunity.id)).where(JobOpportunity.validation_status == "INVALID")
        ).scalar() or 0

        # 3. Completeness & Gaps
        records_without_salary = db.execute(
            select(func.count(JobOpportunity.id)).where(
                JobOpportunity.salary_lpa.is_(None),
                JobOpportunity.stipend_amount.is_(None)
            )
        ).scalar() or 0

        records_incomplete_eligibility = db.execute(
            select(func.count(JobOpportunity.id)).where(
                JobOpportunity.minimum_cgpa.is_(None),
                JobOpportunity.eligible_branches.is_(None)
            )
        ).scalar() or 0

        records_missing_urls = db.execute(
            select(func.count(JobOpportunity.id)).where(
                or_(JobOpportunity.source_url.is_(None), JobOpportunity.source_url == "")
            )
        ).scalar() or 0

        # 4. Duplicate Auditing
        company_dups = DuplicateDetector.analyze_company_duplicates(db)
        job_dups = DuplicateDetector.analyze_job_duplicates(db)

        # 5. Composite Quality Score Calculation
        # Weighted factors: validity (40%), salary completeness (30%), eligibility (20%), uniqueness (10%)
        valid_ratio = valid_records / total_jobs
        salary_ratio = (total_jobs - records_without_salary) / total_jobs
        elig_ratio = (total_jobs - records_incomplete_eligibility) / total_jobs
        dup_job_count = job_dups.get("total_duplicates_detected", 0)
        unique_ratio = max(0.0, 1.0 - (dup_job_count / total_jobs)) if total_jobs > 0 else 1.0

        quality_score = (
            (valid_ratio * 40.0) +
            (salary_ratio * 30.0) +
            (elig_ratio * 20.0) +
            (unique_ratio * 10.0)
        )
        quality_percentage = round(min(100.0, max(0.0, quality_score)), 1)

        return {
            "total_companies": total_companies,
            "total_jobs": total_jobs,
            "cleaned_records": cleaned_records,
            "records_valid": valid_records,
            "records_needing_review": records_needing_review,
            "invalid_salary_entries": invalid_records,
            "duplicate_companies_detected": company_dups.get("duplicate_records_count", 0),
            "duplicate_jobs_detected": dup_job_count,
            "records_without_salary": records_without_salary,
            "records_with_incomplete_eligibility": records_incomplete_eligibility,
            "records_with_missing_source_urls": records_missing_urls,
            "data_quality_percentage": quality_percentage,
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }

