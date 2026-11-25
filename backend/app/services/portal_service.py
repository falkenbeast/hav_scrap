import logging
from typing import Dict, Any
from app.core.config import settings
from app.scraper.browser_manager import BrowserManager
from app.scraper.auth_manager import AuthManager

logger = logging.getLogger("hav_scrap")


class PortalService:
    """
    Service layer coordinating the Haveloc browser instance, persistent profile,
    and manual authentication state management.
    """

    def __init__(self):
        self.browser_manager = BrowserManager()
        self.auth_manager = AuthManager(browser_manager=self.browser_manager)

    def get_status(self) -> Dict[str, Any]:
        """
        Retrieves the current authentication and connection status summary.
        """
        return self.auth_manager.get_status_summary()

    def get_info(self) -> Dict[str, Any]:
        """
        Provides safe portal and configuration metadata without credentials.
        """
        paths = self.browser_manager.get_browser_paths()
        return {
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "portal_url": settings.HAVELOC_LOGIN_URL,
            "target_dashboard_url": settings.HAVELOC_TARGET_DASHBOARD_URL,
            "browser_profile_path": paths["profile_path"],
            "browsers_binary_path": paths["browsers_path"],
            "chromium_executable_path": paths.get("executable_path"),
            "playwright_installed": paths["playwright_installed"],
            "chromium_installed": paths["chromium_installed"],
            "headless_mode": settings.PLAYWRIGHT_HEADLESS,
        }

    async def connect(self) -> Dict[str, Any]:
        """
        Initiates the visible Chromium browser session for manual operator login.
        """
        return await self.auth_manager.connect()

    async def reconnect(self) -> Dict[str, Any]:
        """
        Probes existing persistent session cookies to reconnect without manual login.
        """
        return await self.auth_manager.reconnect()

    async def disconnect(self) -> Dict[str, Any]:
        """
        Closes the active browser and marks the session disconnected.
        """
        return await self.auth_manager.disconnect()


# Singleton service instance
portal_service = PortalService()

