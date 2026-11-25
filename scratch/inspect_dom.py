import asyncio
import sys
from pathlib import Path

# Setup paths
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.loop import setup_windows_event_loop
setup_windows_event_loop()

from playwright.async_api import async_playwright
from app.core.config import settings


async def inspect_dom():
    chromium_path = "C:\\Program Files\\Chromium\\Application\\chrome.exe"
    profile_dir = Path(settings.BROWSER_PROFILE_DIR).resolve()

    print(f"Connecting to persistent context at {profile_dir}...")
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            executable_path=chromium_path,
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ],
            viewport={"width": 1280, "height": 800},
        )

        page = context.pages[0] if context.pages else await context.new_page()
        target_url = "https://placements.haveloc.com/jobs?sort=jobApplyBy%2Cdesc&jobView=eligible"
        print(f"Navigating to {target_url}...")
        try:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(4.0)

            print(f"Current Page URL: {page.url}")
            print(f"Current Page Title: {await page.title()}")

            # Check table headers
            headers = await page.evaluate("""() => {
                const ths = document.querySelectorAll('th, [role="columnheader"]');
                return Array.from(ths).map(th => th.innerText.trim());
            }""")
            print(f"Table Headers: {headers}")

            # Extract first 3 rows details
            rows_data = await page.evaluate("""() => {
                const rows = document.querySelectorAll('table tbody tr, [role="row"]');
                const out = [];
                for (let i = 0; i < Math.min(rows.length, 5); i++) {
                    const r = rows[i];
                    const cells = r.querySelectorAll('td, [role="cell"]');
                    const cellInfo = [];
                    for (const c of cells) {
                        cellInfo.push({
                            innerText: c.innerText.trim(),
                            innerHTML: c.innerHTML.trim()
                        });
                    }
                    out.push({
                        rowHTML: r.outerHTML.substring(0, 500),
                        cells: cellInfo
                    });
                }
                return out;
            }""")

            print(f"Found {len(rows_data)} rows.")
            for idx, r in enumerate(rows_data):
                print(f"\n--- ROW {idx+1} ---")
                for c_idx, c in enumerate(r["cells"]):
                    print(f"  Cell {c_idx}: {repr(c['innerText'])}")
                    # print snippet of innerHTML if interesting
                    if c_idx < 3:
                        print(f"    HTML {c_idx}: {c['innerHTML'][:200]}")

            # Save full sample HTML of the table or page to a scratch file
            table_html = await page.evaluate("""() => {
                const t = document.querySelector('table') || document.querySelector('[role="table"]');
                return t ? t.outerHTML : document.body.innerHTML;
            }""")
            out_file = Path(__file__).resolve().parent / "sample_portal_table.html"
            out_file.write_text(table_html, encoding="utf-8")
            print(f"\nSaved sample table HTML to {out_file} ({len(table_html)} chars)")

        except Exception as e:
            print(f"Error inspecting DOM: {e}")
        finally:
            await context.close()


if __name__ == "__main__":
    asyncio.run(inspect_dom())

