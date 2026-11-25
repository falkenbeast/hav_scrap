import re
from typing import Optional, Dict, Any
from app.processors.data_cleaner import DataCleaner


class DataNormalizer:
    """
    Standardization orchestrator for company profiles, designations,
    locations, and employment types.
    """

    JOB_TYPE_MAPPING = [
        (r'\b(full[- ]?time|fte|permanent|regular)\b', 'Full-Time'),
        (r'\b(6m\s*\+?\s*fte|intern\s*\+?\s*fte|internship\s*cum\s*placement)\b', '6M+FTE'),
        (r'\b(internship|intern|summer\s*intern)\b', 'Internship'),
        (r'\b(contract|contractual|freelance)\b', 'Contract'),
        (r'\b(part[- ]?time)\b', 'Part-Time'),
    ]

    WORK_MODE_MAPPING = [
        (r'\b(remote|work\s*from\s*home|wfh|telecommute)\b', 'Remote'),
        (r'\b(hybrid|flexible)\b', 'Hybrid'),
        (r'\b(on[- ]?site|in[- ]?office|office)\b', 'Onsite'),
    ]

    @classmethod
    def normalize_company_name(cls, raw_name: Optional[str]) -> Optional[str]:
        """
        Normalizes company names using DataCleaner, avoiding aggressive transforms.
        """
        return DataCleaner.clean_company_name(raw_name)

    @classmethod
    def normalize_job_type(cls, raw_type: Optional[str]) -> Optional[str]:
        """
        Standardizes employment classification into recognized canonical types.
        """
        cleaned = DataCleaner.clean_text(raw_type)
        if not cleaned:
            return "Full-Time"

        lower = cleaned.lower()
        for pat, norm in cls.JOB_TYPE_MAPPING:
            if re.search(pat, lower):
                return norm

        return cleaned.title()

    @classmethod
    def normalize_work_mode(cls, raw_mode: Optional[str]) -> Optional[str]:
        """
        Normalizes operational work modes (Remote, Hybrid, Onsite).
        """
        cleaned = DataCleaner.clean_text(raw_mode)
        if not cleaned:
            return None

        lower = cleaned.lower()
        for pat, norm in cls.WORK_MODE_MAPPING:
            if re.search(pat, lower):
                return norm

        return cleaned.title()

    @classmethod
    def normalize_location(cls, raw_location: Optional[str]) -> Optional[str]:
        """
        Cleans location strings and standardizes common Indian tech hubs.
        """
        cleaned = DataCleaner.clean_text(raw_location)
        if not cleaned:
            return None

        # Common city normalization
        replacements = [
            (r'\bBangalore\b', 'Bengaluru'),
            (r'\bGurgaon\b', 'Gurugram'),
            (r'\bBombay\b', 'Mumbai'),
            (r'\bCalcutta\b', 'Kolkata'),
            (r'\bMadras\b', 'Chennai'),
        ]
        norm = cleaned
        for pat, rep in replacements:
            norm = re.sub(pat, rep, norm, flags=re.IGNORECASE)

        # Standardize slashes and delimiters
        norm = re.sub(r'\s*[/,;|]\s*', ' / ', norm)
        return norm.strip(" /")

