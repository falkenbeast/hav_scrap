import asyncio
import logging
from typing import Optional

logger = logging.getLogger("hav_scrap")


class TaskManager:
    """
    Manages background asyncio tasks for the scraper engine,
    supporting clean cancellation, timeout supervision, and graceful shutdown.
    """

    def __init__(self):
        self._current_task: Optional[asyncio.Task] = None

    def is_running(self) -> bool:
        """
        Returns True if a background task is currently active and not done.
        """
        return self._current_task is not None and not self._current_task.done()

    def start_task(self, coro, name: str = "scraper_background_task") -> asyncio.Task:
        """
        Spawns a new managed background asyncio task.
        """
        if self.is_running():
            raise RuntimeError("A background scraping task is already executing.")

        loop = asyncio.get_event_loop()
        self._current_task = loop.create_task(coro, name=name)
        self._current_task.add_done_callback(self._on_task_done)
        logger.info(f"Background scraping task '{name}' spawned successfully.")
        return self._current_task

    def _on_task_done(self, task: asyncio.Task):
        try:
            exc = task.exception()
            if exc:
                if isinstance(exc, asyncio.CancelledError):
                    logger.info("Scraping background task was safely cancelled.")
                else:
                    logger.error(f"Scraping background task terminated with exception: {exc}", exc_info=exc)
            else:
                logger.info("Scraping background task finished execution normally.")
        except asyncio.CancelledError:
            logger.info("Scraping background task was cancelled.")
        except Exception as e:
            logger.error(f"Error inspecting completed task: {str(e)}")

    async def cancel_task(self, timeout: float = 5.0) -> bool:
        """
        Safely requests cancellation of the current task and waits for cleanup.
        """
        if not self.is_running():
            logger.info("No active scraping task to cancel.")
            return True

        logger.info("Signaling cancellation to background scraping task...")
        self._current_task.cancel()
        try:
            await asyncio.wait_for(asyncio.shield(self._current_task), timeout=timeout)
            logger.info("Background scraping task cancelled cleanly.")
            return True
        except asyncio.TimeoutError:
            logger.warning(f"Task did not terminate within {timeout}s after cancel request.")
            return False
        except asyncio.CancelledError:
            return True
        except Exception as e:
            logger.warning(f"Exception during task cancellation: {str(e)}")
            return True
        finally:
            self._current_task = None

    async def shutdown(self):
        """
        Shutdown hook to ensure no orphaned tasks remain on application exit.
        """
        if self.is_running():
            logger.info("Shutting down active scraping task before process exit...")
            await self.cancel_task(timeout=3.0)

