from __future__ import annotations
from typing import Any
from playwright.sync_api import sync_playwright, BrowserContext
from .config import settings

class AuthSession:
    def __init__(self) -> None:
        self.context: BrowserContext | None = None
    
    def __enter__(self) -> "AuthSession":
        self.pw = sync_playwright().start()
        
        browser = self.pw.chromium.launch(
            headless=True,
            devtools=True,
            slow_mo=50,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-web-security",  # Add this to handle CORS
                "--disable-features=IsolateOrigins,site-per-process", # Handle iframe restrictions
            ],
        )
        # use a realistic user agent and locale
        self.context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/117.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            viewport={"width": 1280, "height": 800},
            accept_downloads=True,
            ignore_https_errors=True,  # Add this for SSL/TLS issues
        )
        # hide common automation indicators
        self.context.set_extra_http_headers({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document"
        })
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.context:
            self.context.close()
        self.pw.stop()

    def login_and_get_page(self, login_url: str, username_selector: str, password_selector: str, submit_selector: str, target_url: str | None = None):
        page = self.context.new_page()
        
        # navigate and wait for the login form to appear before filling
        response = page.goto(login_url, wait_until="networkidle", timeout=30000)
        if not response:
            raise Exception("Page failed to load")
        cookie_selector = "button:has-text('אשר cookies ')"
        if page.locator(cookie_selector).count() > 0:
            page.click(cookie_selector)
            page.wait_for_load_state("networkidle")

        go_to_login_page_selector = "button:has-text('הזדהות משרד החינוך')"
        if page.locator(go_to_login_page_selector).count() > 0:
            button = page.locator(go_to_login_page_selector)
            if button.get_attribute("disabled") == "true":
                print("The button is disabled.")
                raise Exception("Login page is disabled")
            else:
                print("The button is enabled.")
                button.click()  # Click the button if it's enabled
                page.wait_for_load_state("networkidle")
                
        page.wait_for_selector(username_selector, timeout=15000)
        page.fill(username_selector, settings.username)
        pw_loc = page.locator(password_selector)
        try:
            pw_loc.wait_for(state="attached", timeout=5000)
        except Exception:
            pass
        
        try:
            pw_loc.focus()
        except Exception:
            pass
        
        try:
            page.eval_on_selector(password_selector, "el => el.removeAttribute('readonly')")
        except Exception:
            pass
        
        pwd = settings.password.get_secret_value()
        try:
            pw_loc.fill(pwd, timeout=15000)
        except Exception:
            try:
                pw_loc.click()
            except Exception:
                pass
            page.keyboard.type(pwd, delay=20)
        
        page.click(submit_selector)
        page.wait_for_load_state("networkidle")
        
        return page