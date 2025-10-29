from __future__ import annotations
from datetime import date
from loguru import logger
from .db import HomeworkDB
from .auth import AuthSession
from .homework_parser import parse_homework_for_today
import ipdb  # Import for debugging

# Placeholder selectors and URLs; update for your site
LOGIN_URL = "https://school.example.com/login"
USERNAME_SELECTOR = "#username"
PASSWORD_SELECTOR = "#password"
SUBMIT_SELECTOR = "button[type=submit]"
TARGET_URL = "https://school.example.com/homework/today"


def run_scrape_once_debug() -> int:
    """Debug version of scraper with breakpoints"""
    db = HomeworkDB()
    
    # BREAKPOINT 1: Before starting authentication
    ipdb.set_trace()
    logger.info("Starting authentication...")
    
    with AuthSession() as auth:
        # BREAKPOINT 2: After creating auth session
        ipdb.set_trace()
        logger.info("Auth session created, attempting login...")
        
        page = auth.login_and_get_page(
            login_url=LOGIN_URL,
            username_selector=USERNAME_SELECTOR,
            password_selector=PASSWORD_SELECTOR,
            submit_selector=SUBMIT_SELECTOR,
            target_url=TARGET_URL,
        )
        
        # BREAKPOINT 3: After login, before parsing
        ipdb.set_trace()
        logger.info("Login successful, parsing homework...")
        
        items = parse_homework_for_today(page)
        
        # BREAKPOINT 4: After parsing, before saving
        ipdb.set_trace()
        logger.info(f"Found {len(items)} homework items")
        
        inserted = db.upsert_items(items)
        logger.info(f"Inserted {inserted} homework items for {date.today().isoformat()}")
        return inserted

if __name__ == "__main__":
    run_scrape_once_debug()
