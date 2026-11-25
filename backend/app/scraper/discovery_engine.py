import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from urllib.parse import urljoin

from app.core.config import settings
from app.services.discovery_service import DiscoveryService
from app.database.session import SessionLocal

logger = logging.getLogger("hav_scrap")


from app.scraper.exceptions import AuthenticationRequiredError


class DiscoveryEngine:
    """
    Haveloc Placement Portal Listing Discovery and Extraction Engine.
    Navigates the authenticated dashboard, inspects live DOM containers,
    handles pagination / dynamic scroll, and synchronizes with SQLite.
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

        self.portal_url: str = settings.HAVELOC_LOGIN_URL
        self.dashboard_url: str = settings.HAVELOC_TARGET_DASHBOARD_URL

        # Telemetry metrics
        self.pages_visited: int = 0
        self.total_pages_detected: Optional[int] = None
        self.companies_discovered: int = 0
        self.unique_companies_discovered: int = 0
        self.jobs_discovered: int = 0
        self.duplicates_skipped: int = 0
        self.records_saved: int = 0

    async def _dummy_checkpoint(self, stage: str):
        pass

    async def _dummy_publish(self, event_type: str, data: Dict[str, Any]):
        pass

    def _dummy_progress(self, *args, **kwargs):
        pass

    async def execute_discovery(self) -> Dict[str, Any]:
        """
        Executes the full company discovery pipeline across available pages.
        """
        logger.info("Commencing Haveloc Placement Portal listing discovery...")
        await self.checkpoint("PRE_FLIGHT_CHECK")

        # 1. Verify Browser & Authentication Status
        from app.services.portal_service import portal_service
        status = portal_service.get_status()
        if status.get("authentication_status") != "CONNECTED":
            logger.info("Portal session not connected. Attempting persistent session restoration...")
            reconn_result = await portal_service.reconnect()
            if reconn_result.get("authentication_status") != "CONNECTED":
                err_msg = (
                    "Haveloc portal authentication is not active. "
                    "Please launch and authenticate via the Haveloc Portal Gateway first."
                )
                logger.error(err_msg)
                raise AuthenticationRequiredError(err_msg)

        # 2. Acquire Active Authenticated Page
        page = await portal_service.browser_manager.get_active_page()
        if not page or page.is_closed():
            raise RuntimeError("Could not acquire an active browser page from the persistent context.")

        # 3. Navigate to Target Placement Dashboard
        logger.info(f"Navigating to authenticated dashboard: {self.dashboard_url}")
        await self.checkpoint("NAVIGATING_DASHBOARD")
        await page.goto(self.dashboard_url, wait_until="networkidle", timeout=45000)
        try:
            await page.wait_for_selector("table.jobs-table tbody tr", timeout=15000)
        except Exception:
            await asyncio.sleep(2.0)  # Fallback dynamic hydration wait

        # Check if redirected back to login
        current_url = page.url
        if "login" in current_url.lower() or current_url.rstrip("/") == self.portal_url.rstrip("/"):
            raise AuthenticationRequiredError(
                "Session expired upon accessing target dashboard. Redirected to login."
            )

        # 4. Process Listings Across Pages
        max_pages = 50
        current_page_num = 1
        has_more_pages = True

        while has_more_pages and current_page_num <= max_pages:
            await self.checkpoint(f"PROCESSING_PAGE_{current_page_num}")
            self.pages_visited += 1
            logger.info(f"Inspecting Haveloc Placement listings on Page #{current_page_num}...")

            # Extract listings from current DOM state
            page_listings = await self._extract_listings_from_dom(page)
            logger.info(f"Found {len(page_listings)} listing element(s) on Page #{current_page_num}")

            # Persist extracted listings into SQLite
            with SessionLocal() as db:
                for idx, listing in enumerate(page_listings, start=1):
                    await self.checkpoint(f"PERSISTING_PAGE_{current_page_num}_ITEM_{idx}")
                    try:
                        company, job, is_new_company, is_new_job = (
                            DiscoveryService.save_discovered_listing(db, listing)
                        )

                        self.companies_discovered += 1
                        if is_new_company:
                            self.unique_companies_discovered += 1
                        if is_new_job:
                            self.jobs_discovered += 1
                            self.records_saved += 1
                        else:
                            self.duplicates_skipped += 1

                        # Publish live record discovered event
                        await self.publish_event("RECORD_DISCOVERED", {
                            "company_name": company.company_name,
                            "job_title": job.job_title,
                            "job_role": job.job_role,
                            "location": job.location,
                            "is_new_company": is_new_company,
                            "is_new_job": is_new_job,
                            "records_discovered": self.companies_discovered,
                            "records_processed": self.records_saved,
                        })

                    except Exception as item_err:
                        logger.warning(f"Error persisting listing '{listing}': {item_err}")

            # Update real-time progress metrics
            self.update_progress(
                records_discovered=self.companies_discovered,
                records_processed=self.records_saved,
                stage=f"PAGE_{current_page_num}_PROCESSED"
            )

            # 5. Check and Navigate Pagination or Infinite Scroll
            await self.checkpoint(f"PAGINATION_CHECK_{current_page_num}")
            has_more_pages = await self._advance_to_next_page(page, current_page_num)
            if has_more_pages:
                current_page_num += 1
                await asyncio.sleep(2.0)  # Pacing between page transitions

        logger.info(
            f"Discovery completed. Visited {self.pages_visited} page(s). "
            f"Discovered {self.companies_discovered} listings, {self.unique_companies_discovered} unique companies, "
            f"{self.records_saved} new jobs saved, {self.duplicates_skipped} duplicates skipped."
        )

        return {
            "pages_visited": self.pages_visited,
            "companies_discovered": self.companies_discovered,
            "unique_companies_discovered": self.unique_companies_discovered,
            "jobs_discovered": self.jobs_discovered,
            "records_saved": self.records_saved,
            "duplicates_skipped": self.duplicates_skipped,
        }

    async def _extract_listings_from_dom(self, page) -> List[Dict[str, Any]]:
        """
        Inspects the rendered DOM using exact Haveloc table selectors and React fiber state.
        Discovers company name, job title, original salary, original stipend, dates, and metadata.
        """
        dom_script = """
        () => {
            const results = [];
            const clean = (txt) => txt ? txt.trim().replace(/\\s+/g, ' ') : null;

            // Strategy A: Haveloc Desktop Placement Table
            const rows = document.querySelectorAll('table.jobs-table tbody tr, table tbody tr');

            let reactJobsMap = null;
            try {
                const firstRow = rows[0];
                if (firstRow) {
                    const fiberKey = Object.keys(firstRow).find(k => k.startsWith('__reactFiber'));
                    let f = fiberKey ? firstRow[fiberKey] : null;
                    while (f) {
                        if (f.memoizedProps && f.memoizedProps.jobs && Array.isArray(f.memoizedProps.jobs)) {
                            reactJobsMap = f.memoizedProps.jobs;
                            break;
                        }
                        f = f.return;
                    }
                }
            } catch (e) {}

            for (let i = 0; i < rows.length; i++) {
                const row = rows[i];
                const cells = row.querySelectorAll('td');
                if (cells.length < 2) continue;

                // Column 0: Company & Title / Job Role
                const compEl = row.querySelector('.title-company-cell .company-text, .company-text') || cells[0].querySelector('div:first-child');
                const titleEl = row.querySelector('.title-company-cell .title-text, .title-text') || cells[0].querySelector('div:last-child');

                let companyName = clean(compEl ? compEl.textContent : cells[0].textContent);
                let jobTitle = clean(titleEl ? titleEl.textContent : '');

                // Column 1: Salary & Job Type
                let salaryText = null;
                let jobType = null;
                if (cells.length > 1) {
                    const salEl = cells[1].querySelector('.salary-text') || cells[1].querySelector('div:first-child');
                    const typeEl = cells[1].querySelector('.type-text') || cells[1].querySelector('div:last-child');
                    salaryText = clean(salEl ? salEl.textContent : cells[1].textContent);
                    jobType = clean(typeEl ? typeEl.textContent : '');
                    if (salaryText === '—' || salaryText === '-' || salaryText === 'N/A') salaryText = null;
                    if (jobType === '—' || jobType === '-') jobType = null;
                }

                // Column 2: Stipend & Period
                let stipendText = null;
                let stipendPeriod = null;
                if (cells.length > 2) {
                    const stipEl = cells[2].querySelector('.salary-text') || cells[2].querySelector('div:first-child');
                    const periodEl = cells[2].querySelector('.type-text') || cells[2].querySelector('div:last-child');
                    stipendText = clean(stipEl ? stipEl.textContent : cells[2].textContent);
                    stipendPeriod = clean(periodEl ? periodEl.textContent : '');
                    if (stipendText === '—' || stipendText === '-' || stipendText === 'N/A') stipendText = null;
                    if (stipendPeriod === '—' || stipendPeriod === '-') stipendPeriod = null;
                }

                // Column 3: Apply Before
                let applyBeforeDate = null;
                if (cells.length > 3) {
                    const applyEl = cells[3].querySelector('.applyby-date') || cells[3];
                    applyBeforeDate = clean(applyEl ? applyEl.textContent : '');
                    if (applyBeforeDate === '—' || applyBeforeDate === '-') applyBeforeDate = null;
                }

                // Column 4: Date Of Visit
                let dateOfVisit = null;
                if (cells.length > 4) {
                    const visitEl = cells[4].querySelector('.salary-text') || cells[4];
                    dateOfVisit = clean(visitEl ? visitEl.textContent : '');
                    if (dateOfVisit === '—' || dateOfVisit === '-') dateOfVisit = null;
                }

                // Column 5: Status
                let jobStatus = null;
                if (cells.length > 5) {
                    const statusEl = cells[5].querySelector('.status-badge-text, .status-badge') || cells[5];
                    jobStatus = clean(statusEl ? statusEl.textContent : '');
                    if (jobStatus === '—' || jobStatus === '-') jobStatus = null;
                }

                // Column 6: Batch
                let batch = null;
                if (cells.length > 6) {
                    batch = clean(cells[6].textContent);
                    if (batch === '—' || batch === '-') batch = null;
                }

                // Column 7: Job Posted Date
                let postedDate = null;
                if (cells.length > 7) {
                    postedDate = clean(cells[7].textContent);
                    if (postedDate === '—' || postedDate === '-') postedDate = null;
                }

                // Fiber / Component data matching
                let jobUrl = null;
                let location = null;
                let minCtc = null;
                let maxCtc = null;
                let stipendMin = null;
                let stipendMax = null;

                if (reactJobsMap && reactJobsMap[i]) {
                    const rj = reactJobsMap[i];
                    if (rj.jobId && rj.uuid && rj.companyId && rj.companyUuid) {
                        jobUrl = `https://placements.haveloc.com/jobs/details?jid=${rj.jobId}&juuid=${rj.uuid}&cId=${rj.companyId}&cuuid=${rj.companyUuid}`;
                    }
                    if (rj.location) location = clean(rj.location);
                    if (rj.companyName) companyName = clean(rj.companyName);
                    if (rj.jobTitle) jobTitle = clean(rj.jobTitle);
                    if (rj.jobStatus) jobStatus = clean(rj.jobStatus);
                    if (rj.jobApplyBy) applyBeforeDate = rj.jobApplyBy;
                    if (rj.dateOfVisit) dateOfVisit = rj.dateOfVisit;
                    if (rj.jobPostedDate) postedDate = rj.jobPostedDate;
                    if (rj.minCtc != null) minCtc = rj.minCtc;
                    if (rj.maxCtc != null) maxCtc = rj.maxCtc;
                    if (rj.internshipMinCtc != null) stipendMin = rj.internshipMinCtc;
                    if (rj.internshipMaxCtc != null) stipendMax = rj.internshipMaxCtc;
                    if (rj.stipend != null && stipendMin == null) stipendMin = rj.stipend;
                }

                if (companyName && jobTitle) {
                    results.push({
                        company_name: companyName,
                        job_title: jobTitle,
                        salary_original: salaryText,
                        salary_min_lpa: minCtc != null ? (minCtc / 100000.0) : null,
                        salary_max_lpa: maxCtc != null ? (maxCtc / 100000.0) : null,
                        stipend_original: stipendText,
                        stipend_min: stipendMin,
                        stipend_max: stipendMax,
                        stipend_period: stipendPeriod,
                        job_type: jobType,
                        apply_before: applyBeforeDate,
                        date_of_visit: dateOfVisit,
                        job_status: jobStatus,
                        target_batch: batch,
                        job_posted_date: postedDate,
                        location: location,
                        source_url: jobUrl,
                        source: 'haveloc_table'
                    });
                }
            }

            // Strategy B: Card/Grid Fallback if table not present
            if (results.length === 0) {
                const cardSelectors = [
                    '[data-testid*="job-card"]',
                    '.job-card',
                    'article[class*="job"]'
                ];
                let cards = [];
                for (const sel of cardSelectors) {
                    const matched = document.querySelectorAll(sel);
                    if (matched.length > 0) {
                        cards = matched;
                        break;
                    }
                }
                for (const card of cards) {
                    const compEl = card.querySelector('.company-name, [data-testid*="company"], h3, h4');
                    const titleEl = card.querySelector('.job-title, [data-testid*="title"], h2, a');
                    const cName = clean(compEl?.textContent);
                    const jTitle = clean(titleEl?.textContent);
                    if (cName && jTitle && cName !== jTitle) {
                        results.push({
                            company_name: cName,
                            job_title: jTitle,
                            source: 'card_container'
                        });
                    }
                }
            }

            return results;
        }
        """

        raw_results = await page.evaluate(dom_script)
        for r in raw_results:
            # Normalize full URLs
            url = r.get("job_url", "")
            if url and not url.startswith("http"):
                url = urljoin(self.dashboard_url, url)
                r["job_url"] = url
            listings.append(r)

        return listings

    async def _advance_to_next_page(self, page, current_page_num: int) -> bool:
        """
        Detects and executes pagination navigation or dynamic scroll loading.
        """
        # 1. Search for Next Button
        next_button_selectors = [
            'button[aria-label="Next"]',
            'a[aria-label="Next"]',
            'button[aria-label="next page"]',
            '.pagination-next:not(.disabled)',
            'li.next:not(.disabled) a',
            'button:has-text("Next")',
            'button:has-text(">")',
            'a:has-text("Next")',
        ]

        for selector in next_button_selectors:
            try:
                next_btn = await page.query_selector(selector)
                if next_btn:
                    is_visible = await next_btn.is_visible()
                    is_enabled = await next_btn.is_enabled()
                    if is_visible and is_enabled:
                        logger.info(f"Advancing to next page via selector: {selector}")
                        await next_btn.click()
                        await page.wait_for_load_state("domcontentloaded", timeout=15000)
                        return True
            except Exception as e:
                logger.debug(f"Selector {selector} check skipped: {e}")

        # 2. Check for dynamic infinite scrolling
        try:
            prev_height = await page.evaluate("document.body.scrollHeight")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2.0)
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height > prev_height:
                logger.info("Dynamic infinite scroll loaded additional DOM elements.")
                return True
        except Exception as scroll_err:
            logger.debug(f"Infinite scroll detection skipped: {scroll_err}")

        logger.info(f"No further pagination controls detected on Page #{current_page_num}. Ending discovery.")
        return False

