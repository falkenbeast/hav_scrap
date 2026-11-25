import asyncio
import sys
import json
from pathlib import Path

backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.loop import setup_windows_event_loop
setup_windows_event_loop()

from playwright.async_api import async_playwright
from app.core.config import settings


async def test_extraction():
    profile_dir = Path("data/browser_profile").resolve()
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            executable_path="C:\\Program Files\\Chromium\\Application\\chrome.exe",
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        await page.goto("https://placements.haveloc.com/jobs?sort=jobApplyBy%2Cdesc&jobView=eligible", wait_until="networkidle")
        await page.wait_for_selector("table.jobs-table tbody tr", timeout=15000)

        results = await page.evaluate("""() => {
            const results = [];
            const clean = (txt) => txt ? txt.trim().replace(/\\s+/g, ' ') : null;

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

                // Fiber data matching
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
                });
            }
            return results;
        }""")

        print(f"Extracted {len(results)} listings successfully.")
        for r in results[:6]:
            print(json.dumps(r, indent=2))

        await ctx.close()

if __name__ == "__main__":
    asyncio.run(test_extraction())
