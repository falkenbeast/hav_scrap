from typing import Tuple, List, Dict, Any, Optional
from datetime import datetime


class ValidationStatus:
    VALID = "VALID"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    INVALID = "INVALID"


class DataValidator:
    """
    Validates company and job opportunity data integrity,
    flagging inconsistencies and returning actionable audit trails.
    Never silently deletes or drops invalid records.
    """

    @classmethod
    def validate_job_record(cls, job_data: Dict[str, Any]) -> Tuple[str, List[str]]:
        """
        Runs comprehensive validation rules against a job opportunity payload.
        Returns:
            (validation_status: str, validation_notes: List[str])
        """
        notes: List[str] = []
        is_invalid = False
        needs_review = False

        # 1. Company Name Validation
        company_name = job_data.get("company_name") or job_data.get("cleaned_company_name")
        if not company_name or not str(company_name).strip():
            notes.append("Company name is missing or empty.")
            is_invalid = True

        # 2. Job Title Validation
        job_title = job_data.get("job_title") or job_data.get("cleaned_job_title")
        if not job_title or not str(job_title).strip():
            notes.append("Job designation title is missing.")
            is_invalid = True

        # 3. Source URL Validation
        source_url = job_data.get("source_url")
        if source_url:
            if not (source_url.startswith("http://") or source_url.startswith("https://") or source_url.startswith("/")):
                notes.append("Source URL format is malformed.")
                needs_review = True
        else:
            notes.append("Source URL is absent.")
            needs_review = True

        # 4. Salary Integrity Rules
        min_ctc = job_data.get("minimum_ctc")
        max_ctc = job_data.get("maximum_ctc")
        salary_lpa = job_data.get("salary_lpa")
        stipend_amt = job_data.get("stipend_amount")
        salary_type = job_data.get("salary_type")

        # Negative checks
        if min_ctc is not None and min_ctc < 0:
            notes.append("Minimum CTC cannot be negative.")
            is_invalid = True
        if max_ctc is not None and max_ctc < 0:
            notes.append("Maximum CTC cannot be negative.")
            is_invalid = True
        if stipend_amt is not None and stipend_amt < 0:
            notes.append("Stipend amount cannot be negative.")
            is_invalid = True

        # Range ordering check
        if min_ctc is not None and max_ctc is not None:
            if min_ctc > max_ctc:
                notes.append(f"Minimum CTC ({min_ctc} LPA) exceeds maximum CTC ({max_ctc} LPA).")
                is_invalid = True

        # Stipend separation check
        if stipend_amt is not None:
            if salary_lpa is not None:
                notes.append("Internship stipend is improperly combined with full-time CTC.")
                is_invalid = True

        if salary_type == "NEEDS_REVIEW":
            notes.append("Compensation clause is ambiguous and requires operator inspection.")
            needs_review = True

        # 5. CGPA Threshold Validation
        min_cgpa = job_data.get("minimum_cgpa")
        if min_cgpa is not None:
            if min_cgpa < 0.0 or min_cgpa > 10.0:
                notes.append(f"CGPA threshold ({min_cgpa}) falls outside standard 0.0–10.0 scale.")
                is_invalid = True
            elif min_cgpa < 4.0:
                notes.append(f"Unusually low CGPA requirement ({min_cgpa}).")
                needs_review = True

        # 6. Dates Consistency Check
        posted_date = job_data.get("posted_date")
        deadline = job_data.get("application_deadline")
        if posted_date and deadline and isinstance(posted_date, datetime) and isinstance(deadline, datetime):
            if deadline < posted_date:
                notes.append("Application deadline occurs prior to posting timestamp.")
                needs_review = True

        # Determine aggregate status
        if is_invalid:
            status = ValidationStatus.INVALID
        elif needs_review:
            status = ValidationStatus.NEEDS_REVIEW
        else:
            status = ValidationStatus.VALID

        return status, notes

