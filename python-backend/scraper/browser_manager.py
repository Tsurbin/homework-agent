"""
Browser management for web scraping.
"""
from playwright.sync_api import sync_playwright, Browser, Page, Playwright
from typing import Optional
import logging

from config.settings import get_settings

logger = logging.getLogger(__name__)


class BrowserManager:
    """Manages Playwright browser instances."""
    
    def __init__(self):
        self.settings = get_settings()
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def start(self):
        """Start browser instance."""
        logger.info("Starting browser...")
        self.playwright = sync_playwright().start()
        
        self.browser = self.playwright.chromium.launch(
            headless=self.settings.headless_mode,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        self.page = context.new_page()
        self.page.set_default_timeout(self.settings.browser_timeout)
        logger.info("✓ Browser started successfully")
    
    def get_page(self) -> Page:
        """Get current page instance."""
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        return self.page
    
    def navigate(self, url: str):
        """Navigate to URL."""
        logger.info(f"Navigating to: {url}")
        self.page.goto(url, wait_until='networkidle')
    
    def wait_for_selector(self, selector: str, timeout: Optional[int] = None):
        """Wait for element to appear."""
        self.page.wait_for_selector(selector, timeout=timeout or self.settings.browser_timeout)
    
    def close(self):
        """Close browser and cleanup."""
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("✓ Browser closed")