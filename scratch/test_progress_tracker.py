import sys
print("STEP 0: Starting python script", flush=True)
from pathlib import Path
root_path = Path(__file__).resolve().parent.parent
backend_path = root_path / "backend"
sys.path.insert(0, str(backend_path))

import asyncio
from app.core.loop import setup_windows_event_loop
setup_windows_event_loop()

from app.scraper.progress_tracker import ProgressTracker
from app.scraper.event_manager import EventManager
from app.scraper.discovery_engine import DiscoveryEngine
from app.scraper.engine import ScraperEngine
from app.scraper.session_manager import SessionManager
from app.scraper.browser_manager import BrowserManager

async def main():
    print("STEP 1: Starting async tests", flush=True)
    tracker = ProgressTracker()
    assert hasattr(tracker, "update")
    print("STEP 2: tracker has update", flush=True)

    tracker.start_session(session_id=101)
    tracker.update(records_discovered=15, records_processed=12, stage="PAGE_2_PROCESSED")
    snap = tracker.get_snapshot()
    assert snap["records_discovered"] == 15
    assert snap["records_processed"] == 12
    assert snap["stage"] == "PAGE_2_PROCESSED"
    print("STEP 3: update(records_discovered, records_processed, stage) passed", flush=True)

    tracker.update(records_discovered=50, records_processed=20, stage="JOB_20_OF_50", percentage=40.0)
    snap2 = tracker.get_snapshot()
    assert snap2["records_discovered"] == 50
    assert snap2["records_processed"] == 20
    assert snap2["stage"] == "JOB_20_OF_50"
    assert snap2["progress_percentage"] == 40.0
    print("STEP 4: DetailExtractor args and percentage passed", flush=True)

    # SSE Event Test
    print("STEP 5: Testing SSE event dispatch", flush=True)
    em = EventManager()
    q = await em.subscribe()
    tracker_sse = ProgressTracker(event_manager=em)
    tracker_sse.start_session(session_id=202)
    tracker_sse.update(records_discovered=30, records_processed=25, stage="DISCOVERY_PAGE_1")
    # Yield control to allow event task to run
    await asyncio.sleep(0.01)
    
    event_payload = await asyncio.wait_for(q.get(), timeout=2.0)
    assert event_payload["event"] == "PROGRESS_UPDATED"
    assert event_payload["data"]["records_discovered"] == 30
    assert event_payload["data"]["stage"] == "DISCOVERY_PAGE_1"
    print("STEP 6: SSE event received correctly", flush=True)

    # DiscoveryEngine wiring test
    print("STEP 7: Testing DiscoveryEngine callback wiring", flush=True)
    discovery = DiscoveryEngine(
        checkpoint_fn=None,
        event_publisher=em.publish,
        progress_updater=tracker.update
    )
    discovery.update_progress(records_discovered=99, records_processed=88, stage="PAGE_5_PROCESSED")
    snap3 = tracker.get_snapshot()
    assert snap3["records_discovered"] == 99
    assert snap3["records_processed"] == 88
    print("STEP 8: DiscoveryEngine callback executed successfully", flush=True)

    # ScraperEngine wiring test
    print("STEP 9: Testing ScraperEngine constructor and DiscoveryEngine setup", flush=True)
    session_mgr = SessionManager()
    browser_mgr = BrowserManager()
    scraper_engine = ScraperEngine(
        session_id=303,
        session_manager=session_mgr,
        progress_tracker=tracker,
        event_manager=em,
        browser_manager=browser_mgr
    )
    de = DiscoveryEngine(
        checkpoint_fn=scraper_engine.checkpoint,
        event_publisher=scraper_engine.event_manager.publish,
        progress_updater=scraper_engine.progress_tracker.update,
    )
    assert de.update_progress == scraper_engine.progress_tracker.update
    print("STEP 10: ScraperEngine wiring verified without AttributeError", flush=True)
    print("\nALL TESTS COMPLETED SUCCESSFULLY!", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
