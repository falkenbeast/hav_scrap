import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from app.core.config import settings
from app.scraper.browser_manager import BrowserManager

logger = logging.getLogger("hav_scrap")

# Standardized Authentication Lifecycle States
class AuthStatus:
    DISCONNECTED = "DISCONNECTED"
    BROWSER_LAUNCHING = "BROWSER_LAUNCHING"
    AWAITING_LOGIN = "AWAITING_LOGIN"
    VERIFYING = "VERIFYING"
    CONNECTED = "CONNECTED"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    UNKNOWN = "UNKNOWN"
    ERROR = "ERROR"


class AuthManager:
    """
    Orchestrates manual authentication, session persistence,
    target dashboard validation, and connection telemetry.
    Strictly forbids storing, capturing, or logging user passwords or tokens.
    """

    def __init__(self, browser_manager: BrowserManager):
        self.browser_manager = browser_manager
        self.status: str = AuthStatus.DISCONNECTED
        self.last_connected_at: Optional[str] = None
        self.last_error_message: Optional[str] = None
        self.portal_url: str = settings.HAVELOC_LOGIN_URL
        self.target_dashboard_url: str = settings.HAVELOC_TARGET_DASHBOARD_URL

        self._monitor_task: Optional[asyncio.Task] = None
        self._lock: Optional[asyncio.Lock] = None

        # Register callback for browser unexpected termination
        self.browser_manager.set_on_close_callback(self._on_browser_closed)

    @property
    def lock(self) -> asyncio.Lock:
        """
        Lazily initializes the asyncio.Lock within the active running event loop.
        """
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    def _on_browser_closed(self):
        """
        Handler triggered when user manually closes the Chromium browser window.
        """
        logger.info("Browser window was closed by user.")
        if self.status != AuthStatus.DISCONNECTED:
            self.status = AuthStatus.DISCONNECTED
            self.last_error_message = "Browser window was closed."

    def get_status_summary(self) -> Dict[str, Any]:
        """
        Returns safe portal status information.
        Exposes zero credentials, session cookies, or tokens.
        """
        browser_running = self.browser_manager.is_running()
        is_pw_installed = self.browser_manager.is_playwright_installed()
        is_chr_installed = self.browser_manager.is_chromium_installed()

        # Connection classification
        if self.status == AuthStatus.CONNECTED:
            conn_status = "CONNECTED"
        elif self.status in [AuthStatus.DISCONNECTED, AuthStatus.ERROR]:
            conn_status = "DISCONNECTED"
        else:
            conn_status = "PENDING"

        exec_path = self.browser_manager.get_chromium_executable_path()

        return {
            "portal_url": self.portal_url,
            "target_dashboard_url": self.target_dashboard_url,
            "browser_status": "RUNNING" if browser_running else "DISCONNECTED",
            "authentication_status": self.status,
            "connection_status": conn_status,
            "last_connected_at": self.last_connected_at,
            "last_error_message": self.last_error_message,
            "playwright_installed": is_pw_installed,
            "chromium_installed": is_chr_installed,
            "executable_path": str(exec_path.resolve()) if exec_path else None,
            "profile_path": str(self.browser_manager.browser_profile_dir),
            "updated_at": datetime.utcnow().isoformat() + "Z",
        }

    async def connect(self) -> Dict[str, Any]:
        """
        Launches a visible Chromium browser with persistent profile,
        opens the Haveloc login page, and awaits manual operator authentication.
        """
        async with self.lock:
            # Check for prerequisites
            if not self.browser_manager.is_playwright_installed():
                self.status = AuthStatus.ERROR
                self.last_error_message = (
                    "Playwright Python package is not installed. Please review installation requirements."
                )
                logger.error(self.last_error_message)
                return self.get_status_summary()

            if not self.browser_manager.is_chromium_installed():
                self.status = AuthStatus.ERROR
                self.last_error_message = (
                    "Chromium browser binary is missing at configured path. Please install Chromium first."
                )
                logger.error(self.last_error_message)
                return self.get_status_summary()

            # Prevent duplicate launch
            if self.browser_manager.is_running() and self.status in [
                AuthStatus.AWAITING_LOGIN,
                AuthStatus.VERIFYING,
                AuthStatus.CONNECTED,
            ]:
                logger.info("Browser already running in active authentication state.")
                return self.get_status_summary()

            try:
                self.status = AuthStatus.BROWSER_LAUNCHING
                self.last_error_message = None

                # Launch visible persistent context
                context = await self.browser_manager.launch_persistent_context(headless=False)
                if not context:
                    self.status = AuthStatus.ERROR
                    self.last_error_message = "Failed to instantiate Chromium browser context."
                    return self.get_status_summary()

                page = await self.browser_manager.get_active_page()
                if not page:
                    self.status = AuthStatus.ERROR
                    self.last_error_message = "Failed to allocate active browser page."
                    return self.get_status_summary()

                # Navigate to Haveloc login portal
                logger.info(f"Navigating to Haveloc portal: {self.portal_url}")
                await page.goto(self.portal_url, wait_until="domcontentloaded", timeout=30000)

                self.status = AuthStatus.AWAITING_LOGIN
                logger.info("Awaiting manual operator login in visible browser...")

                # Cancel previous monitor task if active
                if self._monitor_task and not self._monitor_task.done():
                    self._monitor_task.cancel()

                # Start background authentication observation loop
                self._monitor_task = asyncio.create_task(self._monitor_authentication_loop())

                return self.get_status_summary()

            except Exception as e:
                self.status = AuthStatus.ERROR
                self.last_error_message = f"Error during portal connection initiation: {str(e)}"
                logger.error(self.last_error_message, exc_info=True)
                return self.get_status_summary()

    async def reconnect(self) -> Dict[str, Any]:
        """
        Attempts to restore an existing authenticated session from the persistent profile
        by directly probing the target placement dashboard.
        """
        async with self.lock:
            if not self.browser_manager.is_playwright_installed():
                self.status = AuthStatus.ERROR
                self.last_error_message = "Playwright Python package is not installed."
                return self.get_status_summary()

            if not self.browser_manager.is_chromium_installed():
                self.status = AuthStatus.ERROR
                self.last_error_message = "Chromium browser binary is missing."
                return self.get_status_summary()

            try:
                self.status = AuthStatus.VERIFYING
                self.last_error_message = None

                # Launch or get context
                if not self.browser_manager.is_running():
                    context = await self.browser_manager.launch_persistent_context(headless=False)
                    if not context:
                        self.status = AuthStatus.ERROR
                        self.last_error_message = "Could not launch persistent browser context for reconnect."
                        return self.get_status_summary()

                page = await self.browser_manager.get_active_page()
                if not page:
                    self.status = AuthStatus.ERROR
                    self.last_error_message = "Could not obtain active browser page."
                    return self.get_status_summary()

                # Directly probe target dashboard
                logger.info(f"Reconnection probe navigating to target dashboard: {self.target_dashboard_url}")
                await page.goto(self.target_dashboard_url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)

                # Verify authenticated state on dashboard
                verified = await self._verify_target_dashboard(page)
                if verified is True:
                    self.status = AuthStatus.CONNECTED
                    self.last_connected_at = datetime.utcnow().isoformat() + "Z"
                    logger.info("Session successfully restored. Authenticated target dashboard accessible.")
                elif verified is False:
                    # Session expired / redirected to login or captcha
                    self.status = AuthStatus.SESSION_EXPIRED
                    self.last_error_message = "Session expired. Manual re-authentication required."
                    logger.warning("Session expired; redirected to login/captcha.")
                    # Automatically transition to awaiting login
                    if self._monitor_task and not self._monitor_task.done():
                        self._monitor_task.cancel()
                    self._monitor_task = asyncio.create_task(self._monitor_authentication_loop())
                else:
                    self.status = AuthStatus.AWAITING_LOGIN
                    self.last_error_message = None
                    logger.info("Target dashboard not yet conclusive. Observation supervisor initiated.")
                    if self._monitor_task and not self._monitor_task.done():
                        self._monitor_task.cancel()
                    self._monitor_task = asyncio.create_task(self._monitor_authentication_loop())

                return self.get_status_summary()

            except Exception as e:
                self.status = AuthStatus.ERROR
                self.last_error_message = f"Error during reconnection: {str(e)}"
                logger.error(self.last_error_message, exc_info=True)
                return self.get_status_summary()

    async def disconnect(self) -> Dict[str, Any]:
        """
        Safely terminates browser resources and marks the session DISCONNECTED.
        Preserves the persistent browser profile on disk.
        """
        async with self.lock:
            if self._monitor_task and not self._monitor_task.done():
                self._monitor_task.cancel()

            await self.browser_manager.cleanup()
            self.status = AuthStatus.DISCONNECTED
            self.last_error_message = None
            logger.info("Haveloc portal disconnected cleanly.")
            return self.get_status_summary()

    async def _monitor_authentication_loop(self):
        """
        Background observation loop that passively waits for the operator to complete manual login.
        Monitors all open browser tabs without interrupting user interaction, credentials, or CAPTCHA.
        """
        logger.info("Authentication observation supervisor active.")
        timeout_seconds = 300  # 5 minutes for manual operator login
        elapsed = 0
        poll_interval = 2.0
        last_logged_stage = None

        try:
            while elapsed < timeout_seconds:
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval

                if not self.browser_manager.is_running():
                    logger.info("Browser closed during manual authentication.")
                    self.status = AuthStatus.DISCONNECTED
                    break

                context = self.browser_manager._context
                if not context:
                    continue

                open_pages = [p for p in context.pages if not p.is_closed()]
                if not open_pages:
                    continue

                # 1. Check if any open tab has reached the authenticated target jobs dashboard
                target_jobs_page = None
                for p in reversed(open_pages):
                    if "placements.haveloc.com/jobs" in p.url:
                        target_jobs_page = p
                        break

                if target_jobs_page:
                    logger.info(f"Target jobs dashboard page identified: {target_jobs_page.url}. Initiating verification...")
                    self.status = AuthStatus.VERIFYING
                    self.browser_manager._active_page = target_jobs_page

                    # Verify authenticated state on this page
                    verification_result = await self._verify_target_dashboard(target_jobs_page)
                    if verification_result is True:
                        self.status = AuthStatus.CONNECTED
                        self.last_connected_at = datetime.utcnow().isoformat() + "Z"
                        logger.info("Authentication verified! Target dashboard accessible.")
                        break
                    elif verification_result is False:
                        # Redirected back to login/captcha
                        self.status = AuthStatus.AWAITING_LOGIN
                        logger.info("Verification redirected away from jobs. Continuing to await manual login...")
                        continue
                    else:
                        # Still hydrating / ambiguous: do NOT break, keep waiting!
                        logger.debug("Jobs dashboard reached; awaiting page content hydration...")
                        continue

                # 2. Check if operator is on a post-login placement page (not captcha or login)
                post_login_page = None
                for p in reversed(open_pages):
                    url_lower = p.url.lower()
                    if (
                        "placements.haveloc.com" in url_lower
                        and "captcha" not in url_lower
                        and "login" not in url_lower
                    ):
                        post_login_page = p
                        break

                if post_login_page:
                    logger.info(f"Post-login placement session detected on {post_login_page.url}. Navigating to target jobs dashboard...")
                    self.status = AuthStatus.VERIFYING
                    self.browser_manager._active_page = post_login_page
                    try:
                        await post_login_page.goto(self.target_dashboard_url, wait_until="domcontentloaded", timeout=30000)
                        await asyncio.sleep(2)
                    except Exception as ge:
                        logger.warning(f"Error navigating post-login page to target dashboard: {ge}")
                    continue

                # 3. Intermediate manual login stages (CAPTCHA or Login form)
                # DO NOT navigate away! Let the operator complete the challenge peacefully.
                active_page = await self.browser_manager.get_active_page()
                curr_url = active_page.url if active_page else ""
                current_stage = "AWAITING_LOGIN"
                if "captcha" in curr_url.lower():
                    current_stage = "CAPTCHA_VERIFICATION"
                elif "login" in curr_url.lower():
                    current_stage = "CREDENTIAL_ENTRY"

                if current_stage != last_logged_stage:
                    logger.info(f"Operator at stage: {current_stage} (URL: {curr_url})")
                    last_logged_stage = current_stage

                self.status = AuthStatus.AWAITING_LOGIN

            if elapsed >= timeout_seconds and self.status == AuthStatus.AWAITING_LOGIN:
                self.status = AuthStatus.ERROR
                self.last_error_message = "Authentication timed out after 5 minutes."
                logger.warning("Operator manual login timed out.")

        except asyncio.CancelledError:
            logger.info("Authentication observation supervisor cancelled.")
        except Exception as e:
            logger.error(f"Error in authentication observation loop: {str(e)}", exc_info=True)
            self.status = AuthStatus.ERROR
            self.last_error_message = f"Monitoring fault: {str(e)}"

    async def _verify_target_dashboard(self, page) -> Optional[bool]:
        """
        Inspects page to verify if target dashboard is truly authenticated and accessible.
        Returns:
            True: Conclusively authenticated.
            False: Redirected to login/captcha or unauthenticated.
            None: Ambiguous / still hydrating.
        """
        try:
            current_url = page.url

            # 1. Check for unauthenticated redirection to login or captcha
            if "login" in current_url.lower() or "captcha" in current_url.lower() or current_url.rstrip("/") == self.portal_url.rstrip("/"):
                logger.info(f"Verification detected unauthenticated gate: {current_url}")
                return False

            # 2. Check if URL matches target placements dashboard
            if "placements.haveloc.com" in current_url and "jobs" in current_url:
                title = await page.title()
                content = await page.content()

                # If sign in or password prompt is still present inside placements
                if "sign in" in content.lower() and "password" in content.lower() and len(content) < 3000:
                    return False

                # Confirmed on jobs dashboard with rendered page content
                if len(content) > 300:
                    logger.info(f"Target dashboard verified. Title: '{title}', URL: {current_url}, Content size: {len(content)} bytes")
                    return True
                else:
                    return None

            return None
        except Exception as e:
            logger.warning(f"Error inspecting page during authentication verification: {e}")
            return None
