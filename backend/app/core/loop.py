import sys
import asyncio
import logging

logger = logging.getLogger("hav_scrap")


def setup_windows_event_loop() -> None:
    """
    Ensures that a subprocess-capable ProactorEventLoop is active on Windows.
    This is required for Playwright browser driver execution (PipeTransport /
    create_subprocess_exec).

    On Windows, Uvicorn's default reload supervisor configures a SelectorEventLoop
    because use_subprocess=True. This function sets the global ProactorEventLoopPolicy
    and patches Uvicorn's internal loop factories so that ProactorEventLoop is always
    instantiated.
    """
    if sys.platform == "win32":
        try:
            # 1. Set Windows proactor policy on the asyncio module
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except Exception as e:
            logger.debug(f"Event loop policy configuration notice: {e}")

        # 2. Patch Uvicorn's loop factories to prevent fallback to SelectorEventLoop
        try:
            import uvicorn.loops.asyncio
            uvicorn.loops.asyncio.asyncio_loop_factory = lambda use_subprocess=False: asyncio.ProactorEventLoop
        except Exception:
            pass

        try:
            import uvicorn.loops.auto
            uvicorn.loops.auto.auto_loop_factory = lambda use_subprocess=False: asyncio.ProactorEventLoop
        except Exception:
            pass
