import asyncio
import logging
from datetime import datetime
from typing import Optional
from app.scraper.session_manager import SessionManager
from app.scraper.progress_tracker import ProgressTracker
from app.scraper.event_manager import EventManager
from app.scraper.browser_manager import BrowserManager
from app.scraper.discovery_engine import DiscoveryEngine, AuthenticationRequiredError
from app.services.portal_service import portal_service

logger = logging.getLogger("hav_scrap")


class ScraperEngine:
    """
    Core Scraper Engine coordinating the full session lifecycle.
    Implements true asynchronous checkpointing for Pause, Resume, and Cancellation,
    with database session safety and real-time SSE publishing.
    """

    def __init__(
        self,
        session_id: int,
        session_manager: SessionManager,
        progress_tracker: ProgressTracker,
        event_manager: EventManager,
        browser_manager: BrowserManager
    ):
        self.session_id: int = session_id
        self.session_manager = session_manager
        self.progress_tracker = progress_tracker
        self.event_manager = event_manager
        self.browser_manager = browser_manager

        if hasattr(self.progress_tracker, "event_manager") and not self.progress_tracker.event_manager:
            self.progress_tracker.event_manager = event_manager

        # Synchronization primitive for pause/resume
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Initially unpaused (set = allowed to run)
        self._stop_requested = False

    async def pause(self):
        """
        Pauses the scraping engine at the next checkpoint.
        """
        logger.info(f"Engine pause requested for Session #{self.session_id}")
        self._pause_event.clear()  # clears the event so checkpoints block
        self.session_manager.transition_status(self.session_id, "PAUSED")
        self.progress_tracker.update_status("PAUSED", stage="PAUSED_AT_CHECKPOINT")
        await self.event_manager.publish("SESSION_PAUSED", {
            "session_id": self.session_id,
            "message": f"Scraping session #{self.session_id} paused by operator at safe checkpoint."
        })

    async def resume(self):
        """
        Resumes engine execution from a paused checkpoint.
        """
        logger.info(f"Engine resume requested for Session #{self.session_id}")
        self._pause_event.set()  # unblocks the checkpoint wait
        self.session_manager.transition_status(self.session_id, "RUNNING")
        self.progress_tracker.update_status("RUNNING", stage="PROCESSING")
        await self.event_manager.publish("SESSION_RESUMED", {
            "session_id": self.session_id,
            "message": f"Scraping session #{self.session_id} resumed execution."
        })

    def request_stop(self):
        """
        Flags engine to safely stop and cancel at next checkpoint.
        """
        logger.info(f"Engine stop flagged for Session #{self.session_id}")
        self._stop_requested = True
        self._pause_event.set()  # Unblock if currently paused so it can cancel immediately

    async def checkpoint(self, stage_name: Optional[str] = None):
        """
        Safe synchronization barrier.
        If paused, execution halts here until resumed.
        If stop was requested, raises CancelledError cleanly.
        """
        if self._stop_requested:
            raise asyncio.CancelledError(f"Session #{self.session_id} stop requested.")

        # If pause_event was cleared, wait here until set() is called
        if not self._pause_event.is_set():
            logger.info(f"Session #{self.session_id} holding at safe checkpoint: {stage_name or 'WAIT'}")
            await self._pause_event.wait()

        # Re-check stop after unpausing
        if self._stop_requested:
            raise asyncio.CancelledError(f"Session #{self.session_id} stop requested during resume.")

    async def run(self):
        """
        Main execution loop for Phase 4.
        Executes a controlled task runner that exercises the full lifecycle,
        checkpoints, progress tracking, and SSE broadcasting.
        (Phase 5 attaches actual Haveloc portal DOM navigation and credentials).
        """
        logger.info(f"=== Commencing Scraper Engine Execution for Session #{self.session_id} ===")
        try:
            # 1. INITIALIZING Phase
            self.progress_tracker.update_status("INITIALIZING", stage="STORAGE_VERIFICATION")
            await self.event_manager.publish("SESSION_STARTED", {
                "session_id": self.session_id,
                "message": f"Scraping session #{self.session_id} initialized. Verifying storage environment."
            })
            await asyncio.sleep(0.5)
            await self.checkpoint("STORAGE_VERIFICATION")

            # 2. RUNNING Phase
            self.session_manager.transition_status(self.session_id, "RUNNING")
            self.progress_tracker.update_status("RUNNING", stage="RECON_COMMENCED")
            self.event_manager.log("RECON", f"Session #{self.session_id} entered RUNNING state.")

            # Check if Playwright browser automation is installed
            if portal_service.browser_manager.is_playwright_installed():
                logger.info("Playwright runtime detected. Launching Haveloc Discovery Engine...")
                self.progress_tracker.update_status("RUNNING", stage="LIVE_PORTAL_DISCOVERY")
                discovery_engine = DiscoveryEngine(
                    checkpoint_fn=self.checkpoint,
                    event_publisher=self.event_manager.publish,
                    progress_updater=self.progress_tracker.update,
                )
                discovery_result = await discovery_engine.execute_discovery()

                # Update final session metrics in SQLite
                self.session_manager.update_metrics(
                    self.session_id,
                    records_discovered=discovery_result["companies_discovered"],
                    records_processed=discovery_result["records_saved"]
                )
            else:
                logger.warning(
                    "Playwright is not installed. Please review installation requirements in Phase 5 report."
                )
                raise RuntimeError(
                    "Playwright Python package is required for live Haveloc extraction. "
                    "Please install backend dependencies via 'pip install -r requirements.txt'."
                )

            # 3. COMPLETED Phase
            await self.checkpoint("FINALIZING")
            self.session_manager.transition_status(self.session_id, "COMPLETED")
            self.progress_tracker.update_status("COMPLETED", stage="FINISHED")
            self.progress_tracker.set_progress(100.0)

            await self.event_manager.publish("SESSION_COMPLETED", {
                "session_id": self.session_id,
                "records_discovered": self.progress_tracker.records_discovered,
                "records_processed": self.progress_tracker.records_processed,
                "message": f"Scraping session #{self.session_id} successfully completed all target stages."
            })
            logger.info(f"=== Scraping Session #{self.session_id} COMPLETED ===")

        except asyncio.CancelledError:
            logger.warning(f"=== Scraping Session #{self.session_id} CANCELLED by operator ===")
            try:
                self.session_manager.transition_status(
                    self.session_id,
                    "CANCELLED",
                    error_message="Session safely stopped and cancelled by operator."
                )
                self.progress_tracker.update_status("CANCELLED", stage="CANCELLED")
                await self.event_manager.publish("SESSION_STOPPED", {
                    "session_id": self.session_id,
                    "message": f"Scraping session #{self.session_id} safely stopped and cancelled."
                })
            except Exception as e:
                logger.error(f"Error handling session cancellation transition: {e}")
            raise

        except Exception as e:
            err_msg = f"Engine fault in Session #{self.session_id}: {str(e)}"
            logger.error(err_msg, exc_info=True)
            try:
                self.session_manager.transition_status(self.session_id, "FAILED", error_message=str(e))
                self.progress_tracker.update_status("FAILED", stage="ERROR", error_message=str(e))
                await self.event_manager.publish("ERROR", {
                    "session_id": self.session_id,
                    "error": str(e),
                    "message": err_msg
                })
            except Exception as inner_e:
                logger.error(f"Error recording session failure: {inner_e}")

        finally:
            # Clean up browser instances
            await self.browser_manager.cleanup()
            logger.info(f"Engine cleanup finalized for Session #{self.session_id}")

