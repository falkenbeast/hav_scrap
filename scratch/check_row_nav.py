import asyncio
import sys
from pathlib import Path

backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.loop import setup_windows_event_loop
setup_windows_event_loop()

from playwright.async_api import async_playwright
from app.core.config import settings


async def check_row_navigation():
    chromium_path = "C:\\Program Files\\Chromium\\Application\\chrome.exe"
    profile_dir = Path(settings.BROWSER_PROFILE_DIR).resolve()

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            executable_path=chromium_path,
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        page = context.pages[0] if context.pages else await context.new_page()
        target_url = "https://placements.haveloc.com/jobs?sort=jobApplyBy%2Cdesc&jobView=eligible"
        await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3.0)

        # Inspect row attributes, react/angular props, or listeners
        info = await page.evaluate("""() => {
            const rows = document.querySelectorAll('table tbody tr');
            if (rows.length === 0) return null;
            const r = rows[0];
            const dataset = Object.assign({}, r.dataset);
            const reactKey = Object.keys(r).find(k => k.startsWith('__reactFiber') || k.startsWith('__reactInternalInstance'));
            let reactProps = null;
            if (reactKey && r[reactKey] && r[reactKey].memoizedProps) {
                reactProps = Object.keys(r[reactKey].memoizedProps);
            }
            return {
                id: r.id,
                className: r.className,
                dataset: dataset,
                allKeys: Object.keys(r).filter(k => !k.startsWith('on')),
                reactProps: reactProps
            };
        }""")
        print("Row DOM info:", info)

        # Click first row and see where it navigates or if URL changes!
        prev_url = page.url
        first_row = page.locator("table tbody tr").first
        await first_row.click()
        await asyncio.sleep(3.0)
        print(f"Clicked first row. Prev URL: {prev_url} -> New URL: {page.url}")

        await context.close()

if __name__ == "__main__":
    asyncio.run(check_row_navigation())

