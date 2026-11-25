import re
import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from urllib.parse import urljoin
from sqlalchemy import select

from app.models.company import Company
from app.models.job import JobOpportunity
from app.database.session import SessionLocal
from app.processors.salary_processor import SalaryProcessor
from app.scraper.exceptions import AuthenticationRequiredError

logger = logging.getLogger("hav_scrap")


class DetailExtractor:
    """
    Haveloc Job Notice Deep Extraction Engine.
    Visits individual job posting URLs, inspects detailed compensation and eligibility DOM
    structures, normalizes CTC and stipend metrics, and updates persistent SQLite records.
    """

    def __init__(
        self,
        checkpoint_fn: Optional[Callable[[str], Any]] = None,
        event_publisher: Optional[Callable[[str, Dict[str, Any]], Any]] = None,
        progress_updater: Optional[Callable[..., None]] = None,
    ):
        self.checkpoint = checkpoint_fn or self._dummy_checkpoint
        self.publish_event = event_publisher or self._dummy_publish
        self.update_progress = progress_updater or self._dummy_progress

        # Telemetry metrics
        self.total_postings: int = 0
        self.postings_processed: int = 0
        self.postings_remaining: int = 0
        self.successful_extractions: int = 0
        self.failed_extractions: int = 0
        self.salary_details_found: int = 0
        self.eligibility_details_found: int = 0

    async def _dummy_checkpoint(self, stage: str):
        pass

    async def _dummy_publish(self, event_type: str, data: Dict[str, Any]):
        pass

    def _dummy_progress(self, *args, **kwargs):
        pass

    async def execute_extraction(
        self,
        force_reextract: bool = False,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Executes deep extraction across discovered job opportunities.
        """
        logger.info("Initiating Haveloc job postings detailed extraction...")
        await self.checkpoint("PRE_FLIGHT_CHECK")

        # 1. Verify Browser & Authentication
        from app.services.portal_service import portal_service
        status = portal_service.get_status()
        if status.get("authentication_status") != "CONNECTED":
            logger.info("Portal session not active. Attempting reconnection...")
            reconn = await portal_service.reconnect()
            if reconn.get("authentication_status") != "CONNECTED":
                raise AuthenticationRequiredError(
                    "Haveloc portal authentication is not active. "
                    "Please connect via the Haveloc Portal Gateway first."
                )

        page = await portal_service.browser_manager.get_active_page()
        if not page or page.is_closed():
            raise RuntimeError("Could not acquire an active browser page from persistent context.")

        # 2. Query Target Job Postings
        with SessionLocal() as db:
            query = select(JobOpportunity).where(JobOpportunity.source_url.is_not(None))
            if not force_reextract:
                query = query.where(JobOpportunity.extraction_status != "EXTRACTED")
            query = query.order_by(JobOpportunity.id.asc())
            if limit:
                query = query.limit(limit)

            job_records = db.execute(query).scalars().all()
            target_jobs = [
                {"id": j.id, "title": j.job_title, "url": j.source_url, "company_id": j.company_id}
                for j in job_records
            ]

        self.total_postings = len(target_jobs)
        self.postings_remaining = self.total_postings
        logger.info(f"Target postings for detailed extraction: {self.total_postings} records.")

        if self.total_postings == 0:
            logger.info("No unextracted postings pending. Deep extraction finished.")
            return self.get_summary()

        # 3. Process Each Posting Sequentially
        for idx, job_info in enumerate(target_jobs, start=1):
            job_id = job_info["id"]
            job_url = job_info["url"]
            job_title = job_info["title"]

            await self.checkpoint(f"EXTRACTING_JOB_{job_id}")
            logger.info(f"[{idx}/{self.total_postings}] Visiting posting #{job_id}: '{job_title}' -> {job_url}")

            try:
                # Navigate to individual job posting URL
                await page.goto(job_url, wait_until="domcontentloaded", timeout=40000)
                await asyncio.sleep(1.5)  # Allow dynamic content rendering

                # Check if redirected to login
                if "login" in page.url.lower():
                    raise AuthenticationRequiredError("Session expired during posting navigation.")

                # Extract posting DOM content
                extracted_data = await self._extract_posting_dom(page)

                # Process & Normalize Salary Intelligence
                raw_salary = extracted_data.get("salary_text")
                job_type = extracted_data.get("job_type") or "Full-Time"
                salary_metrics = SalaryProcessor.normalize(raw_salary, job_type=job_type)

                if salary_metrics.get("salary_lpa") or salary_metrics.get("stipend_amount"):
                    self.salary_details_found += 1

                if extracted_data.get("eligibility_text") or extracted_data.get("min_cgpa"):
                    self.eligibility_details_found += 1

                # Persist Extracted Details to Database
                with SessionLocal() as db:
                    job = db.get(JobOpportunity, job_id)
                    if job:
                        # Update Job Information
                        if extracted_data.get("job_description"):
                            job.job_description = extracted_data["job_description"]
                        if extracted_data.get("work_mode"):
                            job.work_mode = extracted_data["work_mode"]
                        if extracted_data.get("location") and not job.location:
                            job.location = extracted_data["location"]
                        if extracted_data.get("job_role") and not job.job_role:
                            job.job_role = extracted_data["job_role"]
                        if extracted_data.get("deadline"):
                            job.application_deadline = extracted_data["deadline"]

                        # Update Salary Fields
                        if raw_salary:
                            job.original_salary_text = raw_salary
                        if salary_metrics.get("minimum_ctc") is not None:
                            job.minimum_ctc = salary_metrics["minimum_ctc"]
                        if salary_metrics.get("maximum_ctc") is not None:
                            job.maximum_ctc = salary_metrics["maximum_ctc"]
                        if salary_metrics.get("fixed_ctc") is not None:
                            job.fixed_ctc = salary_metrics["fixed_ctc"]
                        if salary_metrics.get("variable_ctc") is not None:
                            job.variable_ctc = salary_metrics["variable_ctc"]
                        if salary_metrics.get("joining_bonus") is not None:
                            job.joining_bonus = salary_metrics["joining_bonus"]
                        if salary_metrics.get("salary_lpa") is not None:
                            job.salary_lpa = salary_metrics["salary_lpa"]
                        if salary_metrics.get("salary_unit"):
                            job.salary_unit = salary_metrics["salary_unit"]
                        if salary_metrics.get("stipend_amount") is not None:
                            job.stipend_amount = salary_metrics["stipend_amount"]
                        if salary_metrics.get("stipend_period"):
                            job.stipend_period = salary_metrics["stipend_period"]
                        if salary_metrics.get("annualized_equivalent") is not None:
                            job.annualized_equivalent = salary_metrics["annualized_equivalent"]

                        # Update Eligibility Fields
                        if extracted_data.get("eligibility_text"):
                            job.eligibility = extracted_data["eligibility_text"]
                        if extracted_data.get("min_cgpa") is not None:
                            job.minimum_cgpa = extracted_data["min_cgpa"]
                        if extracted_data.get("branches"):
                            job.eligible_branches = extracted_data["branches"]
                        if extracted_data.get("backlog_criteria"):
                            job.backlog_criteria = extracted_data["backlog_criteria"]
                        if extracted_data.get("batch"):
                            job.batch = extracted_data["batch"]

                        job.extraction_status = "EXTRACTED"
                        job.last_verified_at = datetime.utcnow()

                        # Update Parent Company Details if available
                        company = db.get(Company, job.company_id)
                        if company:
                            if extracted_data.get("company_desc") and not company.description:
                                company.description = extracted_data["company_desc"]
                            if extracted_data.get("industry") and not company.industry:
                                company.industry = extracted_data["industry"]
                            if extracted_data.get("company_website") and not company.website:
                                company.website = extracted_data["company_website"]

                        db.commit()

                self.successful_extractions += 1
                logger.info(f"Successfully extracted details for #{job_id}: CTC={salary_metrics.get('salary_lpa')} LPA")

                # Publish real-time event
                await self.publish_event("JOB_DETAILS_EXTRACTED", {
                    "job_id": job_id,
                    "job_title": job_title,
                    "salary_lpa": salary_metrics.get("salary_lpa"),
                    "stipend_amount": salary_metrics.get("stipend_amount"),
                    "eligibility_found": bool(extracted_data.get("min_cgpa") or extracted_data.get("branches")),
                    "postings_processed": idx,
                    "total_postings": self.total_postings,
                })

            except AuthenticationRequiredError:
                raise
            except Exception as extract_err:
                self.failed_extractions += 1
                logger.warning(f"Failed extraction on posting #{job_id} ({job_url}): {extract_err}")
                with SessionLocal() as db:
                    job = db.get(JobOpportunity, job_id)
                    if job:
                        job.extraction_status = "FAILED"
                        job.last_verified_at = datetime.utcnow()
                        db.commit()

                await self.publish_event("JOB_DETAILS_FAILED", {
                    "job_id": job_id,
                    "job_title": job_title,
                    "error": str(extract_err)
                })

            finally:
                self.postings_processed = idx
                self.postings_remaining = self.total_postings - self.postings_processed

                self.update_progress(
                    records_discovered=self.total_postings,
                    records_processed=self.successful_extractions,
                    stage=f"JOB_{idx}_OF_{self.total_postings}"
                )

        return self.get_summary()

    async def _extract_posting_dom(self, page) -> Dict[str, Any]:
        """
        Executes in-page DOM extraction script to harvest job details,
        salary breakdowns, and eligibility sections.
        """
        script = """
        () => {
            const clean = (t) => t ? t.trim().replace(/\\s+/g, ' ') : '';
            const data = {};

            // 1. Job Description & Overview
            const descEl = document.querySelector(
                '[data-testid*="job-description"], .job-description, .description, #job-description, article'
            );
            data.job_description = descEl ? clean(descEl.textContent).substring(0, 5000) : null;

            // 2. Salary / Compensation text
            const salaryEl = document.querySelector(
                '[data-testid*="salary"], [data-testid*="ctc"], .salary, .ctc, .package, .compensation'
            );
            if (salaryEl) {
                data.salary_text = clean(salaryEl.textContent);
            } else {
                // Search for label "CTC" or "Salary" in headers / dt / th / spans
                const allNodes = Array.from(document.querySelectorAll('span, p, dt, h4, div'));
                for (const node of allNodes) {
                    const text = clean(node.textContent);
                    if (/^(ctc|salary|package|stipend)\\s*[:=-]/i.test(text) && text.length < 100) {
                        data.salary_text = text;
                        break;
                    }
                }
            }

            // 3. Work Mode & Location
            const modeEl = document.querySelector('[data-testid*="work-mode"], .work-mode');
            if (modeEl) {
                data.work_mode = clean(modeEl.textContent);
            } else {
                const bodyText = document.body.innerText;
                if (/\\b(remote|work from home|wfh)\\b/i.test(bodyText)) data.work_mode = 'Remote';
                else if (/\\b(hybrid)\\b/i.test(bodyText)) data.work_mode = 'Hybrid';
                else if (/\\b(on-?site|in-?office)\\b/i.test(bodyText)) data.work_mode = 'Onsite';
            }

            // 4. Eligibility Text & Criteria
            const eligEl = document.querySelector(
                '[data-testid*="eligibility"], .eligibility, #eligibility, .requirements'
            );
            data.eligibility_text = eligEl ? clean(eligEl.textContent).substring(0, 3000) : null;

            // 5. Company Details (Description, Website)
            const compDescEl = document.querySelector('[data-testid*="company-description"], .company-description');
            data.company_desc = compDescEl ? clean(compDescEl.textContent).substring(0, 2000) : null;

            const compWebEl = document.querySelector('a[href^="http"]:not([href*="haveloc.com"])');
            if (compWebEl && compWebEl.href) {
                data.company_website = compWebEl.href;
            }

            return data;
        }
        """
        raw_dom = await page.evaluate(script)

        # Post-process eligibility: regex for CGPA, branches, and backlogs
        body_text = await page.inner_text("body")
        eligibility_info = self._parse_eligibility_heuristics(
            raw_dom.get("eligibility_text") or body_text
        )

        raw_dom.update(eligibility_info)
        return raw_dom

    def _parse_eligibility_heuristics(self, text: str) -> Dict[str, Any]:
        """
        Parses CGPA thresholds, eligible branches, and backlog policies via regex heuristics.
        """
        result = {
            "min_cgpa": None,
            "branches": None,
            "backlog_criteria": None,
            "batch": None,
            "deadline": None,
        }
        if not text:
            return result

        # 1. CGPA Cutoff (e.g., "CGPA >= 7.5", "Minimum CGPA: 8.0", "CGPA 7.0 & above")
        cgpa_match = re.search(
            r'(?:minimum\s*)?(?:cgpa|gpa|pointer)\s*(?:criteria|cutoff|required|>=|:|of)?\s*([0-9](?:\.[0-9]{1,2})?)',
            text,
            re.IGNORECASE
        )
        if cgpa_match:
            try:
                cgpa_val = float(cgpa_match.group(1))
                if 4.0 <= cgpa_val <= 10.0:
                    result["min_cgpa"] = cgpa_val
            except ValueError:
                pass

        # 2. Backlog criteria (e.g. "No active backlogs", "Up to 1 backlog allowed", "No standing arrears")
        backlog_match = re.search(
            r'(no\s*(?:active\s*)?backlogs?|no\s*standing\s*arrears?|[0-9]\s*(?:active\s*)?backlogs?\s*allowed)',
            text,
            re.IGNORECASE
        )
        if backlog_match:
            result["backlog_criteria"] = backlog_match.group(1).strip()

        # 3. Eligible Branches (e.g. "CSE, IT, ECE, EEE", "Computer Science", etc.)
        branches_found = []
        branch_patterns = [
            (r'\b(CSE|Computer Science|CS)\b', 'CSE'),
            (r'\b(IT|Information Technology)\b', 'IT'),
            (r'\b(ECE|Electronics and Communication|Electronics & Communication)\b', 'ECE'),
            (r'\b(EEE|Electrical and Electronics|Electrical & Electronics)\b', 'EEE'),
            (r'\b(ME|Mechanical Engineering|Mechanical)\b', 'ME'),
            (r'\b(CE|Civil Engineering|Civil)\b', 'Civil'),
            (r'\b(AI|Artificial Intelligence|Data Science|DS)\b', 'AI/DS'),
        ]
        for pat, norm in branch_patterns:
            if re.search(pat, text, re.IGNORECASE):
                branches_found.append(norm)

        if branches_found:
            result["branches"] = ", ".join(sorted(set(branches_found)))

        # 4. Graduating Batch (e.g. "2025 batch", "Batch: 2026")
        batch_match = re.search(r'\b(202[4-9])\s*(?:batch|passout)?\b', text, re.IGNORECASE)
        if batch_match:
            result["batch"] = batch_match.group(1)

        return result

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_postings": self.total_postings,
            "postings_processed": self.postings_processed,
            "postings_remaining": self.postings_remaining,
            "successful_extractions": self.successful_extractions,
            "failed_extractions": self.failed_extractions,
            "salary_details_found": self.salary_details_found,
            "eligibility_details_found": self.eligibility_details_found,
        }

