from asyncio.log import logger
from dataclasses import dataclass
from playwright.sync_api import Page

from config.settings import get_settings
from .browser_manager import BrowserManager


class AuthenticationError(Exception):
    pass


@dataclass
class Authenticator:
    def login(self) -> None:
        settings = get_settings()
        if not settings.school_base_url:
            raise AuthenticationError("Missing school_base_url in settings or environment.")

        if not (settings.username and settings.password):
            raise AuthenticationError("Username/password not provided in settings or environment.")

        if not (settings.username_selector and settings.password_selector and settings.submit_selector):
            raise AuthenticationError("Login selectors not configured in settings. Please set SCHOOL_USERNAME_SELECTOR, SCHOOL_PASSWORD_SELECTOR, and SCHOOL_SUBMIT_SELECTOR.")

        login_url = settings.school_base_url
        if settings.login_path:
            login_url = login_url.rstrip('/') + '/' + settings.login_path.lstrip('/')

        with BrowserManager() as mgr:
            page: Page = mgr.page
            page.goto(login_url)
            page.fill(settings.username_selector, settings.username)
            logger.debug("Username filled")
            page.fill(settings.password_selector, settings.password)
            logger.debug("password filled")
            page.click(settings.submit_selector)
            logger.debug("Login button clicked")
            #TODO : Adjust the selector below to something that indicates a successful login
            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass
            
            
    # TODO: Customize the following methods based on the target website's structure
    def logout(self, page: Page):
        """
        Logout from school website.
        
        Optional but recommended for cleanup.
        """
        try:
            # TODO: Customize for your site
            page.click('.logout-button')
            logger.info("✓ Logged out successfully")
        except Exception as e:
            logger.warning(f"Logout failed (not critical): {e}")