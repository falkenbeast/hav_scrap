import asyncio
import json
import logging
from datetime import datetime
from typing import Set, Dict, Any, List, Optional
from collections import deque

logger = logging.getLogger("hav_scrap")


class EventManager:
    """
    Server-Sent Events (SSE) broadcaster and telemetry log buffer.
    Maintains subscriber queues and dispatches real-time events to connected frontend clients.
    """

    def __init__(self, max_log_history: int = 150):
        self._subscribers: Set[asyncio.Queue] = set()
        self._log_history: deque = deque(maxlen=max_log_history)
        self._lock = asyncio.Lock()

    async def subscribe(self) -> asyncio.Queue:
        """
        Registers a new client subscriber queue.
        """
        queue = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._subscribers.add(queue)
            logger.debug(f"New SSE client connected. Total subscribers: {len(self._subscribers)}")
        return queue

    async def unsubscribe(self, queue: asyncio.Queue):
        """
        Unregisters a disconnected client subscriber queue.
        """
        async with self._lock:
            self._subscribers.discard(queue)
            logger.debug(f"SSE client disconnected. Total subscribers: {len(self._subscribers)}")

    async def publish(self, event_type: str, data: Dict[str, Any]):
        """
        Broadcasts an SSE event to all connected subscriber queues
        and records a log entry in the telemetry buffer.
        """
        payload = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        # Record into log history
        log_entry = {
            "timestamp": datetime.utcnow().strftime("%H:%M:%S"),
            "level": "ERROR" if event_type == "ERROR" else "RECON",
            "event": event_type,
            "message": data.get("message", f"Event: {event_type}")
        }
        self._log_history.append(log_entry)

        async with self._lock:
            dead_queues = []
            for queue in self._subscribers:
                try:
                    queue.put_nowait(payload)
                except asyncio.QueueFull:
                    # Drop oldest if full to avoid blocking
                    try:
                        queue.get_nowait()
                        queue.put_nowait(payload)
                    except Exception:
                        dead_queues.append(queue)
                except Exception:
                    dead_queues.append(queue)

            for dead in dead_queues:
                self._subscribers.discard(dead)

    def log(self, level: str, message: str, event_type: str = "LOG"):
        """
        Appends an explicit entry to the in-memory telemetry console buffer.
        """
        entry = {
            "timestamp": datetime.utcnow().strftime("%H:%M:%S"),
            "level": level.upper(),
            "event": event_type,
            "message": message
        }
        self._log_history.append(entry)

    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Returns the latest entries from the activity log history.
        """
        logs = list(self._log_history)
        return logs[-limit:]

