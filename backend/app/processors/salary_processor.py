import re
from typing import Dict, Any, Optional, Tuple


class SalaryProcessor:
    """
    Production-grade compensation processing and normalization engine.
    Extracts structured metrics from diverse Indian placement salary descriptions,
    strictly abiding by non-fabrication and precision rules.
    """

    # Unspecified / placeholder indicators
    UNDISCLOSED_TERMS = {
        "not disclosed", "not specified", "as per industry", "competitive",
        "best in industry", "to be discussed", "na", "n/a", "tbd", "confidential",
        "—", "-", "—", "none", "null"
    }

    @classmethod
    def normalize_salary(
        cls,
        raw_text: Optional[str],
        min_ctc_lpa: Optional[float] = None,
        max_ctc_lpa: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Parses dedicated salary column text (or explicit CTC metrics) into structured LPA figures.
        Stipends must NOT be included here.
        Missing or undisclosed values remain None (not 0.0).
        """
        result = {
            "original_salary_text": raw_text.strip() if raw_text else None,
            "minimum_ctc": None,
            "maximum_ctc": None,
            "salary_lpa": None,
            "salary_unit": "LPA",
        }

        # Check if raw text is genuinely empty or placeholder
        if not raw_text or raw_text.strip().lower() in cls.UNDISCLOSED_TERMS:
            # If explicit API values were provided, use them
            if max_ctc_lpa is not None and max_ctc_lpa > 0:
                result["maximum_ctc"] = round(float(max_ctc_lpa), 2)
                result["minimum_ctc"] = round(float(min_ctc_lpa), 2) if min_ctc_lpa is not None else result["maximum_ctc"]
                result["salary_lpa"] = result["maximum_ctc"]
            return result

        cleaned = raw_text.strip()
        # Normalize dashes
        norm = cleaned.replace("–", "-").replace("—", "-")

        # 1. Range Annual CTC: e.g. "4.5L - 6.5L", "6.4L - 8L", "15 - 20 LPA", "6L - 10L"
        range_match = re.search(
            r'([0-9]+(?:\.[0-9]+)?)\s*L?(?:PA)?\s*-\s*([0-9]+(?:\.[0-9]+)?)\s*L(?:PA)?',
            norm,
            re.IGNORECASE
        )
        if range_match:
            min_val = float(range_match.group(1))
            max_val = float(range_match.group(2))
            result["minimum_ctc"] = round(min_val, 2)
            result["maximum_ctc"] = round(max_val, 2)
            result["salary_lpa"] = round(max_val, 2)  # Peak package is max_val
            return result

        # 2. Single Annual CTC with L / LPA: e.g. "22.4L", "5L", "10L", "12 LPA", "6.5 LPA"
        single_lpa = re.search(
            r'(?:₹|rs\.?|inr)?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:lpa|lakhs?\s*(?:per\s*annum)?|l\b)',
            norm,
            re.IGNORECASE
        )
        if single_lpa:
            val = float(single_lpa.group(1))
            result["minimum_ctc"] = round(val, 2)
            result["maximum_ctc"] = round(val, 2)
            result["salary_lpa"] = round(val, 2)
            return result

        # 3. Crores representation: e.g. "1.2 Cr", "1.5 Crore"
        cr_match = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(?:cr|crores?)', norm, re.IGNORECASE)
        if cr_match:
            cr_val = float(cr_match.group(1))
            lpa_val = round(cr_val * 100.0, 2)
            result["minimum_ctc"] = lpa_val
            result["maximum_ctc"] = lpa_val
            result["salary_lpa"] = lpa_val
            return result

        # 4. If regex didn't match text, but explicit fiber/API values exist
        if max_ctc_lpa is not None and max_ctc_lpa > 0:
            result["maximum_ctc"] = round(float(max_ctc_lpa), 2)
            result["minimum_ctc"] = round(float(min_ctc_lpa), 2) if min_ctc_lpa is not None else result["maximum_ctc"]
            result["salary_lpa"] = result["maximum_ctc"]

        return result

    @classmethod
    def normalize_stipend(
        cls,
        raw_text: Optional[str],
        stipend_period: Optional[str] = "Per Month",
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Parses dedicated stipend column text into structured monthly/periodic figures.
        Never included in annual CTC calculations.
        """
        result = {
            "original_stipend_text": raw_text.strip() if raw_text else None,
            "stipend_min": None,
            "stipend_max": None,
            "stipend_amount": None,
            "stipend_period": stipend_period or "Per Month",
        }

        if not raw_text or raw_text.strip().lower() in cls.UNDISCLOSED_TERMS:
            # If explicit API stipend figures exist
            if max_val is not None and max_val > 0:
                result["stipend_max"] = float(max_val)
                result["stipend_min"] = float(min_val) if min_val is not None else float(max_val)
                result["stipend_amount"] = result["stipend_min"]
            return result

        cleaned = raw_text.strip()
        norm = cleaned.replace("–", "-").replace("—", "-")

        # Range K: e.g. "10K - 18K", "22K - 27K", "20K - 30K", "5K - 10K"
        range_k = re.search(
            r'([0-9]+(?:\.[0-9]+)?)\s*k?\s*-\s*([0-9]+(?:\.[0-9]+)?)\s*k',
            norm,
            re.IGNORECASE
        )
        if range_k:
            s_min = float(range_k.group(1)) * 1000.0
            s_max = float(range_k.group(2)) * 1000.0
            result["stipend_min"] = s_min
            result["stipend_max"] = s_max
            result["stipend_amount"] = s_min
            return result

        # Single K: e.g. "20K", "25K", "45K"
        single_k = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*k\b', norm, re.IGNORECASE)
        if single_k:
            val = float(single_k.group(1)) * 1000.0
            result["stipend_min"] = val
            result["stipend_max"] = val
            result["stipend_amount"] = val
            return result

        # Numeric with commas: e.g. "20,000", "25000"
        num_match = re.search(r'(?:₹|rs\.?|inr)?\s*([0-9]{1,3}(?:,[0-9]{2,3})*|[0-9]{4,6})', norm, re.IGNORECASE)
        if num_match:
            raw_str = num_match.group(1).replace(",", "")
            try:
                amt = float(raw_str)
                result["stipend_min"] = amt
                result["stipend_max"] = amt
                result["stipend_amount"] = amt
                return result
            except ValueError:
                pass

        if max_val is not None and max_val > 0:
            result["stipend_max"] = float(max_val)
            result["stipend_min"] = float(min_val) if min_val is not None else float(max_val)
            result["stipend_amount"] = result["stipend_min"]

        return result

    @classmethod
    def normalize(
        cls,
        raw_text: Optional[str],
        job_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Backward-compatible parser for generic or legacy compensation descriptions.
        """
        result = {
            "original_salary_text": raw_text.strip() if raw_text else None,
            "minimum_ctc": None,
            "maximum_ctc": None,
            "fixed_ctc": None,
            "variable_ctc": None,
            "joining_bonus": None,
            "salary_lpa": None,
            "salary_unit": "LPA",
            "stipend_amount": None,
            "stipend_period": None,
            "annualized_equivalent": None,
        }

        if not raw_text:
            return result

        cleaned = raw_text.strip()
        lower = cleaned.lower()

        if any(term in lower for term in cls.UNDISCLOSED_TERMS):
            return result

        is_internship = (
            (job_type and "intern" in job_type.lower()) or
            "stipend" in lower
        )

        # 1. Parse Internship Stipend if strictly internship text
        if is_internship and ("stipend" in lower or "/month" in lower or "pm" in lower or "per month" in lower):
            stip = cls.normalize_stipend(cleaned)
            if stip["stipend_amount"] is not None:
                result["stipend_amount"] = stip["stipend_amount"]
                result["stipend_period"] = stip["stipend_period"]
                result["salary_unit"] = f"INR/{stip['stipend_period']} (Stipend)"
                return result

        # 2. Extract Explicit Breakdown (Fixed + Variable + Joining Bonus)
        fixed_match = re.search(r'fixed(?:\s*(?:pay|salary|ctc))?\s*[:=-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:lpa|lakhs?|l)?', lower)
        var_match = re.search(r'variable(?:\s*(?:pay|bonus|component))?\s*[:=-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:lpa|lakhs?|l)?', lower)
        joining_match = re.search(r'(?:joining|sign[- ]?on)\s*(?:bonus)?\s*[:=-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:lpa|lakhs?|l)?', lower)

        if fixed_match or var_match or joining_match:
            fixed_val = float(fixed_match.group(1)) if fixed_match else None
            var_val = float(var_match.group(1)) if var_match else None
            bonus_val = float(joining_match.group(1)) if joining_match else None

            result["fixed_ctc"] = fixed_val
            result["variable_ctc"] = var_val
            result["joining_bonus"] = bonus_val

            total_calc = (fixed_val or 0.0) + (var_val or 0.0)
            if total_calc > 0:
                result["minimum_ctc"] = total_calc
                result["maximum_ctc"] = total_calc
                result["salary_lpa"] = round(total_calc, 2)
                return result

        # 3. Delegate to normalize_salary
        sal_data = cls.normalize_salary(cleaned)
        result["minimum_ctc"] = sal_data["minimum_ctc"]
        result["maximum_ctc"] = sal_data["maximum_ctc"]
        result["salary_lpa"] = sal_data["salary_lpa"]
        result["salary_unit"] = sal_data["salary_unit"]

        return result
