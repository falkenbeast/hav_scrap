import os
import sys
import glob
import asyncio
import logging
from pathlib import Path
from typing import Optional, Any, Callable
from app.core.config import settings

logger = logging.getLogger("hav_scrap")


class BrowserManager:
    """
    Manages Playwright browser lifecycle, persistent browser profile contexts,
    and isolated Chromium binaries.
    Configured strictly through PLAYWRIGHT_BROWSERS_PATH and BROWSER_PROFILE_DIR.
    """

    def __init__(self):
        self.browsers_path: Path = Path(settings.PLAYWRIGHT_BROWSERS_PATH)
        self.browser_profile_dir: Path = Path(settings.BROWSER_PROFILE_DIR)
        self.headless: bool = settings.PLAYWRIGHT_HEADLESS
        self.slow_mo: int = settings.PLAYWRIGHT_SLOW_MO
        self.timeout: int = settings.PLAYWRIGHT_TIMEOUT

        # Active Playwright references
        self._playwright: Optional[Any] = None
        self._context: Optional[Any] = None
        self._active_page: Optional[Any] = None
        self._on_close_callback: Optional[Callable[[], None]] = None

        # Ensure environment variable is set for Playwright isolation
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(self.browsers_path)
        self.browser_profile_dir.mkdir(parents=True, exist_ok=True)

    def is_playwright_installed(self) -> bool:
        """
        Verifies if playwright python library is installed in the current Python environment.
        """
        try:
            import playwright
            return True
        except ImportError:
            return False

    def get_chromium_executable_path(self) -> Optional[Path]:
        """
        Discovers existing Chromium or Google Chrome binary on the local system.
        Prioritizes user-configured path, standard Chromium locations, and Chrome fallback.
        """
        candidate_paths = []

        # 1. Configured path from settings / environment
        configured_path = getattr(settings, "CHROMIUM_EXECUTABLE_PATH", None)
        if configured_path:
            candidate_paths.append(Path(configured_path))

        # 2. Common Windows Chromium installation paths
        candidate_paths.extend([
            Path(r"C:\Program Files\Chromium\Application\chrome.exe"),
            Path(r"C:\Program Files (x86)\Chromium\Application\chrome.exe"),
            Path(r"C:\Program Files\Chromium\chrome.exe"),
        ])

        # 3. User LocalAppData Chromium
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            candidate_paths.append(Path(local_app_data) / "Chromium" / "Application" / "chrome.exe")

        # 4. Google Chrome installations
        candidate_paths.extend([
            Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
            Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        ])
        if local_app_data:
            candidate_paths.append(Path(local_app_data) / "Google" / "Chrome" / "Application" / "chrome.exe")

        # Check explicit candidates
        for candidate in candidate_paths:
            if candidate.exists() and candidate.is_file():
                return candidate

        # 5. Check custom PLAYWRIGHT_BROWSERS_PATH directory
        if self.browsers_path.exists():
            patterns = [
                str(self.browsers_path / "chromium-*" / "chrome-win" / "chrome.exe"),
                str(self.browsers_path / "chromium-*" / "chrome.exe"),
                str(self.browsers_path / "chrome-win" / "chrome.exe"),
            ]
            for pat in patterns:
                matches = glob.glob(pat)
                if matches:
                    return Path(matches[0])

        # 6. Check default Windows LocalAppData ms-playwright
        if local_app_data:
            default_pw = Path(local_app_data) / "ms-playwright"
            if default_pw.exists():
                patterns = [
                    str(default_pw / "chromium-*" / "chrome-win" / "chrome.exe"),
                    str(default_pw / "chromium-*" / "chrome.exe"),
                ]
                for pat in patterns:
                    matches = glob.glob(pat)
                    if matches:
                        return Path(matches[0])

        return None

    def is_chromium_installed(self) -> bool:
        """
        Verifies whether Chromium binary executable exists in local system paths,
        PLAYWRIGHT_BROWSERS_PATH, or default system Playwright cache.
        """
        return self.get_chromium_executable_path() is not None

    def get_browser_paths(self) -> dict:
        """
        Returns safe path information for diagnostic reporting.
        """
        exec_path = self.get_chromium_executable_path()
        return {
            "browsers_path": str(self.browsers_path.resolve()),
            "executable_path": str(exec_path.resolve()) if exec_path else None,
            "profile_path": str(self.browser_profile_dir.resolve()),
            "playwright_installed": self.is_playwright_installed(),
            "chromium_installed": exec_path is not None,
        }

    def set_on_close_callback(self, callback: Callable[[], None]):
        """
        Registers a callback to execute if the browser context is closed unexpectedly.
        """
        self._on_close_callback = callback

    async def initialize(self) -> bool:
        """
        Initializes the Playwright async driver instance.
        Validates that the active running event loop supports subprocess creation on Windows.
        """
        if not self.is_playwright_installed():
            logger.error("Playwright Python package is not installed.")
            return False

        # Diagnostic check for Windows event loop compatibility
        try:
            loop = asyncio.get_running_loop()
            loop_name = type(loop).__name__
            logger.info(f"BrowserManager initializing on event loop: {loop_name}")
            if sys.platform == "win32" and "Selector" in loop_name:
                logger.error(
                    f"Active event loop is '{loop_name}', which lacks Windows subprocess support for Playwright. "
                    "ProactorEventLoop is required."
                )
                return False
        except Exception as e:
            logger.warning(f"Could not inspect running event loop: {e}")

        try:
            from playwright.async_api import async_playwright
            if self._playwright is None:
                self._playwright = await async_playwright().start()
                logger.info(f"Playwright driver started. Browsers path: {self.browsers_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to start Playwright driver: {str(e)}", exc_info=True)
            return False

    async def launch_persistent_context(self, headless: Optional[bool] = None) -> Optional[Any]:
        """
        Launches a persistent Chromium browser context using data/browser_profile.
        In Phase 5, headless defaults to False so the user can interactively log in.
        """
        if not await self.initialize():
            return None

        effective_headless = headless if headless is not None else self.headless

        try:
            # Ensure profile directory exists
            self.browser_profile_dir.mkdir(parents=True, exist_ok=True)

            logger.info(
                f"Launching persistent Chromium context at {self.browser_profile_dir} "
                f"(headless={effective_headless})..."
            )

            launch_args = [
                "--disable-blink-features=AutomationControlled",
                "--no-default-browser-check",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]

            exec_path = self.get_chromium_executable_path()
            launch_kwargs = {
                "user_data_dir": str(self.browser_profile_dir),
                "headless": effective_headless,
                "slow_mo": self.slow_mo,
                "timeout": self.timeout,
                "viewport": {"width": 1280, "height": 800},
                "args": launch_args,
            }
            if exec_path:
                launch_kwargs["executable_path"] = str(exec_path.resolve())
                logger.info(f"Using Chromium executable at: {exec_path}")

            self._context = await self._playwright.chromium.launch_persistent_context(
                **launch_kwargs
            )

            # Attach listeners for context closure and tab creation
            self._context.on("close", self._handle_context_closed)
            self._context.on("page", self._handle_new_page)

            # Get or create active page
            pages = self._context.pages
            if pages:
                self._active_page = pages[0]
            else:
                self._active_page = await self._context.new_page()

            logger.info("Persistent browser context successfully established.")
            return self._context

        except Exception as e:
            logger.error(f"Failed to launch persistent Chromium context: {str(e)}", exc_info=True)
            return None

    def _handle_new_page(self, page):
        """
        Callback triggered when a new tab or window is opened within the persistent context.
        """
        try:
            logger.info(f"New browser tab/window detected in context: {page.url or 'about:blank'}")
            self._active_page = page
        except Exception as e:
            logger.warning(f"Error handling new browser page event: {e}")

    def _handle_context_closed(self, context):
        """
        Callback triggered when browser context is closed (e.g., user clicked window X).
        """
        logger.info("Browser context closed by user or system.")
        self._context = None
        self._active_page = None
        if self._on_close_callback:
            try:
                self._on_close_callback()
            except Exception as e:
                logger.warning(f"Error executing browser on_close callback: {e}")

    async def get_active_page(self) -> Optional[Any]:
        """
        Returns the active browser page or creates one if none exists.
        Intelligently inspects all open tabs: prioritizes tabs on placements.haveloc.com,
        specifically the jobs dashboard, before falling back to the latest open tab.
        """
        if self._context is None:
            return None

        try:
            pages = [p for p in self._context.pages if not p.is_closed()]
            if not pages:
                self._active_page = await self._context.new_page()
                return self._active_page

            # 1. If currently tracked active page is open and on the target jobs dashboard, keep it
            if self._active_page and not self._active_page.is_closed():
                if "placements.haveloc.com/jobs" in self._active_page.url:
                    return self._active_page

            # 2. Check if any open tab is on the placements jobs dashboard
            for p in reversed(pages):
                if "placements.haveloc.com/jobs" in p.url:
                    self._active_page = p
                    return p

            # 3. Check if any open tab is anywhere on placements.haveloc.com
            for p in reversed(pages):
                if "placements.haveloc.com" in p.url:
                    self._active_page = p
                    return p

            # 4. If current active page is still open, return it
            if self._active_page and not self._active_page.is_closed():
                return self._active_page

            # 5. Default to the most recently opened tab
            self._active_page = pages[-1]
            return self._active_page
        except Exception as e:
            logger.warning(f"Error getting active browser page: {e}")
            return None

    def is_running(self) -> bool:
        """
        Returns True if persistent context is active and open.
        """
        return self._context is not None

    async def cleanup(self):
        """
        Safely closes context and Playwright driver resources without deleting user profile data.
        """
        try:
            if self._context:
                await self._context.close()
                self._context = None
                self._active_page = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
            logger.info("Browser resources cleanly closed.")
        except Exception as e:
            logger.warning(f"Exception during browser cleanup: {str(e)}")

    # Alias for cleanup
    shutdown = cleanup
