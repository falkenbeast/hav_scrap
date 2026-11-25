import re
from typing import Dict, Any, Optional
from app.processors.data_cleaner import DataCleaner


class SalaryType:
    FIXED_CTC = "FIXED_CTC"
    CTC_RANGE = "CTC_RANGE"
    FIXED_PLUS_VARIABLE = "FIXED_PLUS_VARIABLE"
    MONTHLY_SALARY = "MONTHLY_SALARY"
    INTERNSHIP_STIPEND = "INTERNSHIP_STIPEND"
    NOT_DISCLOSED = "NOT_DISCLOSED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class SalaryConverter:
    """
    Robust salary parsing and normalization engine for Phase 8.
    Accurately categorizes salary into standardized SalaryType classes,
    maintaining strict separation between full-time CTC and internship stipends.
    """

    UNDISCLOSED_PATTERNS = [
        r'\b(?:not\s*disclosed|not\s*specified|confidential|tbd|to\s*be\s*discussed)\b',
        r'\b(?:as\s*per\s*industry|best\s*in\s*industry|competitive|negotiable)\b',
        r'^\s*(?:n/?a|-|--|\.)\s*$',
    ]

    AMBIGUOUS_PATTERNS = [
        r'\b(?:depends\s*on|performance\s*based\s*only|incentives?\s*only)\b',
        r'^\s*[0-9]+\s*$',  # Bare number with zero currency or period context
    ]

    @classmethod
    def convert(
        cls,
        raw_text: Optional[str],
        job_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parses raw compensation text into a fully qualified, validated salary record.
        """
        cleaned_raw = DataCleaner.clean_text(raw_text)

        result: Dict[str, Any] = {
            "original_salary_text": cleaned_raw,
            "minimum_ctc": None,
            "maximum_ctc": None,
            "fixed_ctc": None,
            "variable_ctc": None,
            "salary_lpa": None,
            "annualized_equivalent_lpa": None,
            "stipend_amount": None,
            "stipend_period": None,
            "joining_bonus": None,
            "salary_unit": "LPA",
            "salary_type": SalaryType.NOT_DISCLOSED,
        }

        if not cleaned_raw:
            return result

        lower = cleaned_raw.lower()

        # 1. Undisclosed detection
        for pat in cls.UNDISCLOSED_PATTERNS:
            if re.search(pat, lower):
                result["salary_type"] = SalaryType.NOT_DISCLOSED
                return result

        # 2. Ambiguous detection
        for pat in cls.AMBIGUOUS_PATTERNS:
            if re.search(pat, lower):
                result["salary_type"] = SalaryType.NEEDS_REVIEW
                return result

        is_internship = (
            (job_type and "intern" in job_type.lower()) or
            "stipend" in lower or
            "intern" in lower
        )

        # 3. Parse Internship Stipend
        # e.g., "₹35,000/month", "Stipend: 35000 pm", "35k/month"
        if is_internship and ("stipend" in lower or "/month" in lower or "pm" in lower or "per month" in lower):
            stipend_info = cls._extract_stipend(cleaned_raw)
            if stipend_info:
                amt, period = stipend_info
                result["stipend_amount"] = amt
                result["stipend_period"] = period
                result["salary_unit"] = f"INR/{period} (Stipend)"
                result["salary_type"] = SalaryType.INTERNSHIP_STIPEND
                # Strictly DO NOT convert internship stipends into full-time CTC
                return result

        # 4. Parse Explicit Fixed + Variable Breakdown
        # e.g., "Fixed: 12 LPA, Variable: 3 LPA", "10 LPA + performance bonus"
        fixed_match = re.search(r'fixed(?:\s*(?:pay|salary|ctc))?\s*[:=-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:lpa|lakhs?|l)?', lower)
        var_match = re.search(r'variable(?:\s*(?:pay|bonus|component))?\s*[:=-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:lpa|lakhs?|l)?', lower)
        joining_match = re.search(r'(?:joining|sign[- ]?on)\s*(?:bonus)?\s*[:=-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:lpa|lakhs?|l)?', lower)

        if fixed_match and var_match:
            fixed_val = float(fixed_match.group(1))
            var_val = float(var_match.group(1))
            bonus_val = float(joining_match.group(1)) if joining_match else None

            result["fixed_ctc"] = fixed_val
            result["variable_ctc"] = var_val
            result["joining_bonus"] = bonus_val
            total_ctc = round(fixed_val + var_val, 2)
            result["minimum_ctc"] = total_ctc
            result["maximum_ctc"] = total_ctc
            result["salary_lpa"] = total_ctc
            result["salary_type"] = SalaryType.FIXED_PLUS_VARIABLE
            return result

        # Single Base + Bonus clause without stated variable amount
        single_with_bonus = re.search(
            r'([0-9]+(?:\.[0-9]+)?)\s*(?:lpa|lakhs?|l)\s*\+\s*(?:performance|bonus|variable|incentives?)',
            cleaned_raw,
            re.IGNORECASE
        )
        if single_with_bonus:
            base_val = float(single_with_bonus.group(1))
            result["fixed_ctc"] = base_val
            result["minimum_ctc"] = base_val
            result["maximum_ctc"] = base_val
            result["salary_lpa"] = base_val
            result["variable_ctc"] = None  # Do not invent variable figure
            result["salary_type"] = SalaryType.FIXED_PLUS_VARIABLE
            return result

        # 5. Monthly Salary (Full-time monthly salary e.g. "₹50,000/month", "50000 per month")
        monthly_match = re.search(
            r'(?:₹|rs\.?|inr)?\s*([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)\s*(?:/month|per\s*month|/\s*pm|\s*pm\b)',
            cleaned_raw,
            re.IGNORECASE
        )
        if monthly_match and not is_internship:
            raw_monthly = monthly_match.group(1).replace(",", "")
            try:
                monthly_amt = float(raw_monthly)
                annual_eq = round((monthly_amt * 12.0) / 100000.0, 2)
                result["fixed_ctc"] = monthly_amt
                result["salary_unit"] = "INR/month"
                result["annualized_equivalent_lpa"] = annual_eq
                result["minimum_ctc"] = annual_eq
                result["maximum_ctc"] = annual_eq
                result["salary_lpa"] = annual_eq
                result["salary_type"] = SalaryType.MONTHLY_SALARY
                return result
            except ValueError:
                pass

        # 6. Salary Ranges (e.g. "15–20 LPA", "15 - 20 LPA", "15 to 20 LPA", "15L - 20L")
        range_match = re.search(
            r'([0-9]+(?:\.[0-9]+)?)\s*(?:lpa|lakhs?|l)?\s*(?:-|–|—|to)\s*([0-9]+(?:\.[0-9]+)?)\s*(?:lpa|lakhs?|l)',
            cleaned_raw,
            re.IGNORECASE
        )
        if range_match:
            min_val = float(range_match.group(1))
            max_val = float(range_match.group(2))
            if min_val <= max_val:
                result["minimum_ctc"] = min_val
                result["maximum_ctc"] = max_val
                result["salary_lpa"] = round((min_val + max_val) / 2.0, 2)
                result["salary_type"] = SalaryType.CTC_RANGE
                return result
            else:
                result["salary_type"] = SalaryType.NEEDS_REVIEW
                return result

        # 7. Crores Notation (e.g. "1.2 Cr", "1.5 Crore")
        cr_match = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(?:cr|crores?)', cleaned_raw, re.IGNORECASE)
        if cr_match:
            cr_val = float(cr_match.group(1))
            lpa_val = round(cr_val * 100.0, 2)
            result["minimum_ctc"] = lpa_val
            result["maximum_ctc"] = lpa_val
            result["salary_lpa"] = lpa_val
            result["salary_type"] = SalaryType.FIXED_CTC
            return result

        # 8. Standard Single Annual Package (e.g. "12 LPA", "8.5 LPA", "12 Lakhs", "12 L")
        single_lpa = re.search(
            r'(?:₹|rs\.?|inr)?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:lpa|lakhs?\s*(?:per\s*annum)?|l\b)',
            cleaned_raw,
            re.IGNORECASE
        )
        if single_lpa:
            val = float(single_lpa.group(1))
            result["minimum_ctc"] = val
            result["maximum_ctc"] = val
            result["salary_lpa"] = val
            result["salary_type"] = SalaryType.FIXED_CTC
            return result

        # 9. Indian Raw Currency Notations (e.g., "12,00,000", "₹12,00,000/year", "INR 12,00,000 annually")
        raw_currency = re.search(
            r'(?:₹|rs\.?|inr)?\s*([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]+)?|[0-9]{6,8})\s*(?:annually|/year|per\s*annum)?',
            cleaned_raw,
            re.IGNORECASE
        )
        if raw_currency:
            cleaned_num = raw_currency.group(1).replace(",", "")
            try:
                amt = float(cleaned_num)
                if amt >= 100000:
                    lpa_val = round(amt / 100000.0, 2)
                    result["minimum_ctc"] = lpa_val
                    result["maximum_ctc"] = lpa_val
                    result["salary_lpa"] = lpa_val
                    result["salary_type"] = SalaryType.FIXED_CTC
                    return result
            except ValueError:
                pass

        # If text was present but could not be confidently categorized:
        result["salary_type"] = SalaryType.NEEDS_REVIEW
        return result

    @classmethod
    def _extract_stipend(cls, text: str) -> Optional[tuple]:
        k_match = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*k\s*(?:/|\s*per\s*)?\s*(month|week|pm)?', text, re.IGNORECASE)
        if k_match:
            amount = float(k_match.group(1)) * 1000.0
            period = "weekly" if k_match.group(2) and "week" in k_match.group(2).lower() else "monthly"
            return amount, period

        num_match = re.search(
            r'(?:₹|rs\.?|inr)?\s*([0-9]{1,3}(?:,[0-9]{2,3})*|[0-9]{4,6})\s*(?:/|\s*per\s*)?\s*(month|week|pm)?',
            text,
            re.IGNORECASE
        )
        if num_match:
            raw_str = num_match.group(1).replace(",", "")
            try:
                amount = float(raw_str)
                period_str = num_match.group(2)
                period = "weekly" if period_str and "week" in period_str.lower() else "monthly"
                return amount, period
            except ValueError:
                return None
        return None

