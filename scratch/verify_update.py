import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.scraper.progress_tracker import ProgressTracker
from app.scraper.discovery_engine import DiscoveryEngine
from app.scraper.event_manager import EventManager
from app.scraper.engine import ScraperEngine
from app.scraper.session_manager import SessionManager
from app.scraper.browser_manager import BrowserManager

def test_tracker_sync():
    print("--- 1. Testing ProgressTracker instantiation & update method ---")
    tracker = ProgressTracker()
    assert hasattr(tracker, "update"), "Missing update method on ProgressTracker!"
    print("OK: ProgressTracker has 'update' method.")

    print("\n--- 2. Testing DiscoveryEngine argument compatibility ---")
    tracker.start_session(session_id=1)
    tracker.update(
        records_discovered=12,
        records_processed=10,
        stage="PAGE_1_PROCESSED"
    )
    snap = tracker.get_snapshot()
    assert snap["records_discovered"] == 12
    assert snap["records_processed"] == 10
    assert snap["stage"] == "PAGE_1_PROCESSED"
    print(f"OK: DiscoveryEngine update verified: {snap}")

    print("\n--- 3. Testing DetailExtractor argument compatibility ---")
    tracker.update(
        records_discovered=50,
        records_processed=25,
        stage="JOB_25_OF_50",
        percentage=50.0
    )
    snap = tracker.get_snapshot()
    assert snap["records_discovered"] == 50
    assert snap["records_processed"] == 25
    assert snap["stage"] == "JOB_25_OF_50"
    assert snap["progress_percentage"] == 50.0
    print(f"OK: DetailExtractor update verified: {snap}")

    print("\n--- 4. Testing DiscoveryEngine construction with tracker.update ---")
    async def dummy_checkpoint(stage): pass
    async def dummy_publish(event, data): pass

    discovery = DiscoveryEngine(
        checkpoint_fn=dummy_checkpoint,
        event_publisher=dummy_publish,
        progress_updater=tracker.update
    )
    discovery.update_progress(
        records_discovered=22,
        records_processed=18,
        stage="PAGE_2_PROCESSED"
    )
    snap = tracker.get_snapshot()
    assert snap["records_discovered"] == 22
    assert snap["records_processed"] == 18
    assert snap["stage"] == "PAGE_2_PROCESSED"
    print(f"OK: DiscoveryEngine callback executed: {snap}")

    print("\n--- 5. Testing ScraperEngine wiring ---")
    session_mgr = SessionManager()
    browser_mgr = BrowserManager()
    event_mgr = EventManager()
    engine = ScraperEngine(
        session_id=1,
        session_manager=session_mgr,
        progress_tracker=tracker,
        event_manager=event_mgr,
        browser_manager=browser_mgr
    )
    # This was the failing line (engine.py line 123):
    # progress_updater=self.progress_tracker.update
    discovery_wired = DiscoveryEngine(
        checkpoint_fn=engine.checkpoint,
        event_publisher=engine.event_manager.publish,
        progress_updater=engine.progress_tracker.update
    )
    assert discovery_wired.update_progress == tracker.update
    print("OK: ScraperEngine to DiscoveryEngine wiring verified with zero AttributeError.")

    print("\n==========================================")
    print("ALL VERIFICATION CHECKS PASSED PERFECTLY!")
    print("==========================================")

if __name__ == "__main__":
    test_tracker_sync()

