import sys
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.scraper.progress_tracker import ProgressTracker
from app.scraper.event_manager import EventManager


async def test_sse_emission():
    print("--- Testing SSE PROGRESS_UPDATED event broadcast ---")
    event_mgr = EventManager()
    queue = await event_mgr.subscribe()

    tracker = ProgressTracker(event_manager=event_mgr)
    tracker.start_session(session_id=42)

    tracker.update(
        records_discovered=100,
        records_processed=85,
        stage="PAGE_10_PROCESSED",
        percentage=85.0
    )

    # Allow event loop task to publish
    await asyncio.sleep(0.05)

    assert not queue.empty(), "Subscriber queue is unexpectedly empty!"
    payload = queue.get_nowait()
    assert payload["event"] == "PROGRESS_UPDATED", f"Expected PROGRESS_UPDATED, got {payload['event']}"
    assert payload["data"]["session_id"] == 42
    assert payload["data"]["records_discovered"] == 100
    assert payload["data"]["records_processed"] == 85
    assert payload["data"]["stage"] == "PAGE_10_PROCESSED"
    assert payload["data"]["progress_percentage"] == 85.0

    print(f"OK: Received SSE event: {payload}")
    print("SSE VERIFICATION PASSED!")


if __name__ == "__main__":
    asyncio.run(test_sse_emission())

