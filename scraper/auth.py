from __future__ import annotations
from typing import Any
from playwright.sync_api import sync_playwright, BrowserContext
from .config import settings

class AuthSession:
    def __init__(self) -> None:
        self.context: BrowserContext | None = None

    def __enter__(self) -> "AuthSession":
        self.pw = sync_playwright().start()
        browser = self.pw.chromium.launch(headless=False)
        self.context = browser.new_context()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.context:
            self.context.close()
        self.pw.stop()

    def login_and_get_page(self, login_url: str, username_selector: str, password_selector: str, submit_selector: str, target_url: str | None = None):
        assert settings.username and settings.password, "Username/password not configured"
        page = self.context.new_page()
        page.goto(login_url)
        page.fill(username_selector, settings.username)
        page.fill(password_selector, settings.password.get_secret_value())
        page.click(submit_selector)
        page.wait_for_load_state("networkidle")
        if target_url:
            page.goto(target_url)
            page.wait_for_load_state("networkidle")
        return page
