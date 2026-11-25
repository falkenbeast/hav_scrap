import asyncio
import threading
from datetime import datetime
from typing import Optional, Dict, Any


class ProgressTracker:
    """
    Thread-safe in-memory tracker for live scraping execution telemetry.
    """

    def __init__(self, event_manager: Optional[Any] = None):
        self._lock = threading.Lock()
        self.session_id: Optional[int] = None
        self.status: str = "IDLE"
        self.progress_percentage: float = 0.0
        self.records_discovered: int = 0
        self.records_processed: int = 0
        self.stage: str = "ENGINE_READY"
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.error_message: Optional[str] = None
        self.event_manager: Optional[Any] = event_manager

    def start_session(self, session_id: int):
        with self._lock:
            self.session_id = session_id
            self.status = "INITIALIZING"
            self.progress_percentage = 0.0
            self.records_discovered = 0
            self.records_processed = 0
            self.stage = "INITIALIZING"
            self.started_at = datetime.utcnow().isoformat() + "Z"
            self.completed_at = None
            self.error_message = None

    def update(
        self,
        records_discovered: Optional[int] = None,
        records_processed: Optional[int] = None,
        stage: Optional[str] = None,
        percentage: Optional[float] = None,
        status: Optional[str] = None,
        error_message: Optional[str] = None,
        **kwargs: Any
    ):
        """
        Thread-safe unified update method compatible with DiscoveryEngine and DetailExtractor callbacks.
        Updates in-memory telemetry and emits a PROGRESS_UPDATED event via EventManager if available.
        """
        with self._lock:
            if records_discovered is not None:
                self.records_discovered = records_discovered
            if records_processed is not None:
                self.records_processed = records_processed
            if stage is not None:
                self.stage = stage
            if status is not None:
                self.status = status
                if status in {"COMPLETED", "FAILED", "CANCELLED"}:
                    self.completed_at = datetime.utcnow().isoformat() + "Z"
            if error_message is not None:
                self.error_message = error_message

            pct = percentage if percentage is not None else kwargs.get("progress")
            if pct is None:
                pct = kwargs.get("progress_percentage")
            if pct is not None:
                self.progress_percentage = max(0.0, min(100.0, round(float(pct), 1)))

            snapshot = {
                "session_id": self.session_id,
                "status": self.status,
                "progress_percentage": self.progress_percentage,
                "records_discovered": self.records_discovered,
                "records_processed": self.records_processed,
                "stage": self.stage,
                "started_at": self.started_at,
                "completed_at": self.completed_at,
                "error_message": self.error_message,
            }

        # Dispatch SSE event if event_manager is configured
        mgr = kwargs.get("event_manager") or self.event_manager
        if mgr and hasattr(mgr, "publish"):
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(mgr.publish("PROGRESS_UPDATED", snapshot))
            except RuntimeError:
                # No active running asyncio event loop, safely ignore
                pass

    def update_status(self, status: str, stage: Optional[str] = None, error_message: Optional[str] = None):
        with self._lock:
            self.status = status
            if stage:
                self.stage = stage
            if error_message:
                self.error_message = error_message
            if status in {"COMPLETED", "FAILED", "CANCELLED"}:
                self.completed_at = datetime.utcnow().isoformat() + "Z"

    def set_progress(self, percentage: float, stage: Optional[str] = None):
        with self._lock:
            self.progress_percentage = max(0.0, min(100.0, round(percentage, 1)))
            if stage:
                self.stage = stage

    def increment_discovered(self, count: int = 1):
        with self._lock:
            self.records_discovered += count

    def increment_processed(self, count: int = 1):
        with self._lock:
            self.records_processed += count

    def reset(self):
        with self._lock:
            self.session_id = None
            self.status = "IDLE"
            self.progress_percentage = 0.0
            self.records_discovered = 0
            self.records_processed = 0
            self.stage = "ENGINE_READY"
            self.started_at = None
            self.completed_at = None
            self.error_message = None

    def get_snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "session_id": self.session_id,
                "status": self.status,
                "progress_percentage": self.progress_percentage,
                "records_discovered": self.records_discovered,
                "records_processed": self.records_processed,
                "stage": self.stage,
                "started_at": self.started_at,
                "completed_at": self.completed_at,
                "error_message": self.error_message,
            }
