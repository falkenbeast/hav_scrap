import logging
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from fastapi import HTTPException
from app.scraper.session_manager import SessionManager, InvalidStateTransitionError
from app.scraper.progress_tracker import ProgressTracker
from app.scraper.event_manager import EventManager
from app.scraper.browser_manager import BrowserManager
from app.scraper.task_manager import TaskManager

if TYPE_CHECKING:
    from app.scraper.engine import ScraperEngine

logger = logging.getLogger("hav_scrap")


class ScraperController:
    """
    Central controller receiving operator directives (start, pause, resume, stop).
    Enforces concurrency isolation, valid state transitions, and delegates background tasks.
    """

    def __init__(self):
        self.session_manager = SessionManager()
        self.event_manager = EventManager()
        self.progress_tracker = ProgressTracker(event_manager=self.event_manager)
        self.browser_manager = BrowserManager()
        self.task_manager = TaskManager()
        self.active_engine: Optional[ScraperEngine] = None

    def is_active(self) -> bool:
        return self.task_manager.is_running()

    async def start(self) -> Dict[str, Any]:
        """
        Starts a new background scraping session.
        Prevents multiple simultaneous running sessions.
        """
        if self.is_active():
            snapshot = self.progress_tracker.get_snapshot()
            raise HTTPException(
                status_code=400,
                detail=f"Scraper session #{snapshot.get('session_id')} is currently {snapshot.get('status')}."
            )

        try:
            # 1. Create session record in SQLite
            session = self.session_manager.create_session("INITIALIZING")

            # 2. Initialize in-memory telemetry
            self.progress_tracker.start_session(session.id)

            # 3. Instantiate Engine
            from app.scraper.engine import ScraperEngine
            self.active_engine = ScraperEngine(
                session_id=session.id,
                session_manager=self.session_manager,
                progress_tracker=self.progress_tracker,
                event_manager=self.event_manager,
                browser_manager=self.browser_manager
            )

            # 4. Spawn background task
            self.task_manager.start_task(
                self.active_engine.run(),
                name=f"scraper_session_{session.id}"
            )

            return {
                "message": f"Scraping session #{session.id} started successfully.",
                "session_id": session.id,
                "status": "INITIALIZING"
            }

        except Exception as e:
            logger.error(f"Failed to start scraper session: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")

    async def pause(self) -> Dict[str, Any]:
        """
        Pauses the currently running scraping session at the next safe checkpoint.
        """
        if not self.is_active() or not self.active_engine:
            raise HTTPException(status_code=400, detail="No active scraping session is currently running to pause.")

        curr_status = self.progress_tracker.status
        if curr_status != "RUNNING":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot pause session in '{curr_status}' state (must be RUNNING)."
            )

        try:
            await self.active_engine.pause()
            return {
                "message": f"Session #{self.active_engine.session_id} paused at checkpoint.",
                "session_id": self.active_engine.session_id,
                "status": "PAUSED"
            }
        except InvalidStateTransitionError as te:
            raise HTTPException(status_code=400, detail=str(te))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to pause session: {str(e)}")

    async def resume(self) -> Dict[str, Any]:
        """
        Resumes a paused scraping session.
        """
        if not self.is_active() or not self.active_engine:
            raise HTTPException(status_code=400, detail="No paused scraping session is currently active to resume.")

        curr_status = self.progress_tracker.status
        if curr_status != "PAUSED":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot resume session in '{curr_status}' state (must be PAUSED)."
            )

        try:
            await self.active_engine.resume()
            return {
                "message": f"Session #{self.active_engine.session_id} resumed.",
                "session_id": self.active_engine.session_id,
                "status": "RUNNING"
            }
        except InvalidStateTransitionError as te:
            raise HTTPException(status_code=400, detail=str(te))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to resume session: {str(e)}")

    async def stop(self) -> Dict[str, Any]:
        """
        Safely stops and cancels the current scraping session.
        """
        if not self.is_active() or not self.active_engine:
            raise HTTPException(status_code=400, detail="No active scraping session to stop.")

        session_id = self.active_engine.session_id
        try:
            # Transition to STOPPING first
            try:
                self.session_manager.transition_status(session_id, "STOPPING")
            except Exception:
                pass

            self.progress_tracker.update_status("STOPPING", stage="ABORT_REQUESTED")
            self.active_engine.request_stop()
            await self.task_manager.cancel_task(timeout=4.0)

            return {
                "message": f"Session #{session_id} stopped and cancelled.",
                "session_id": session_id,
                "status": "CANCELLED"
            }
        except Exception as e:
            logger.error(f"Error stopping session #{session_id}: {str(e)}")
            return {
                "message": f"Session #{session_id} stop requested.",
                "session_id": session_id,
                "status": "CANCELLED"
            }
        finally:
            self.active_engine = None

    def get_status(self) -> Dict[str, Any]:
        """
        Returns real-time session progress, record counters, and engine state.
        """
        snapshot = self.progress_tracker.get_snapshot()
        if snapshot.get("session_id") is None:
            latest = self.session_manager.get_latest_session()
            if latest:
                return {
                    "session_id": latest.id,
                    "status": latest.status,
                    "progress_percentage": 100.0 if latest.status == "COMPLETED" else 0.0,
                    "records_discovered": latest.records_discovered,
                    "records_processed": latest.records_processed,
                    "started_at": latest.started_at.isoformat() + "Z" if latest.started_at else None,
                    "error_message": latest.error_message
                }
            return {
                "session_id": None,
                "status": "IDLE",
                "progress_percentage": 0.0,
                "records_discovered": 0,
                "records_processed": 0,
                "started_at": None,
                "error_message": None
            }
        return snapshot

    def get_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.event_manager.get_recent_logs(limit=limit)


# Singleton Controller instance
scraper_controller = ScraperController()

