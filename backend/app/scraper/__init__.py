"""
Scraper Engine Subsystem.
Modular infrastructure for background session execution, browser lifecycle management,
synchronization checkpoints (Pause/Resume/Stop), and Server-Sent Events (SSE).
"""

from app.scraper.session_manager import SessionManager, InvalidStateTransitionError
from app.scraper.progress_tracker import ProgressTracker
from app.scraper.event_manager import EventManager
from app.scraper.browser_manager import BrowserManager
from app.scraper.task_manager import TaskManager
from app.scraper.engine import ScraperEngine
from app.scraper.controller import ScraperController, scraper_controller
from app.scraper.auth_manager import AuthManager, AuthStatus
from app.scraper.discovery_engine import DiscoveryEngine, AuthenticationRequiredError
from app.scraper.detail_extractor import DetailExtractor

__all__ = [
    "SessionManager",
    "InvalidStateTransitionError",
    "ProgressTracker",
    "EventManager",
    "BrowserManager",
    "TaskManager",
    "ScraperEngine",
    "ScraperController",
    "scraper_controller",
    "AuthManager",
    "AuthStatus",
    "DiscoveryEngine",
    "AuthenticationRequiredError",
    "DetailExtractor",
]
