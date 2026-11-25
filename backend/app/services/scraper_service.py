import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any, List
from app.scraper.controller import scraper_controller

logger = logging.getLogger("hav_scrap")


class ScraperService:
    """
    Service layer providing unified access to the ScraperController
    and generating Server-Sent Events (SSE) data streams.
    """

    @staticmethod
    async def start_session() -> Dict[str, Any]:
        return await scraper_controller.start()

    @staticmethod
    async def pause_session() -> Dict[str, Any]:
        return await scraper_controller.pause()

    @staticmethod
    async def resume_session() -> Dict[str, Any]:
        return await scraper_controller.resume()

    @staticmethod
    async def stop_session() -> Dict[str, Any]:
        return await scraper_controller.stop()

    @staticmethod
    def get_status() -> Dict[str, Any]:
        return scraper_controller.get_status()

    @staticmethod
    def get_logs(limit: int = 50) -> List[Dict[str, Any]]:
        return scraper_controller.get_logs(limit=limit)

    @staticmethod
    async def event_generator() -> AsyncGenerator[str, None]:
        """
        Subscribes client to event manager and yields SSE formatted event payloads:
        event: <event_name>
        data: <json_string>
        """
        queue = await scraper_controller.event_manager.subscribe()
        try:
            # Send initial connection acknowledgment event
            initial_status = scraper_controller.get_status()
            yield f"event: CONNECTED\ndata: {json.dumps(initial_status)}\n\n"

            while True:
                try:
                    # Wait for next event or send ping keep-alive every 15 seconds
                    event_payload = await asyncio.wait_for(queue.get(), timeout=15.0)
                    event_type = event_payload.get("event", "MESSAGE")
                    data_json = json.dumps(event_payload.get("data", {}))
                    yield f"event: {event_type}\ndata: {data_json}\n\n"
                except asyncio.TimeoutError:
                    # Keep-alive comment line for SSE stream
                    yield ": ping keep-alive\n\n"
        except asyncio.CancelledError:
            logger.debug("SSE client connection closed by consumer.")
        finally:
            await scraper_controller.event_manager.unsubscribe(queue)

