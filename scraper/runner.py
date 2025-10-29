from __future__ import annotations
from datetime import date
from loguru import logger
from .db import HomeworkDB
from .auth import AuthSession
from .homework_parser import parse_homework_for_today
from .historical_parser import parse_all_historical_homework

# Placeholder selectors and URLs; update for your site
# LOGIN_URL = "https://lgn.edu.gov.il/nidp/wsfed/ep?id=EduCombinedAuthUidPwd&sid=0&option=credential&sid=0"
LOGIN_URL = "https://webtop.smartschool.co.il/account/login"
USERNAME_SELECTOR = "#userName"
PASSWORD_SELECTOR = "input[formcontrolname='password'][type='password']"
SUBMIT_SELECTOR = "button[type=submit]"
TARGET_URL = "https://school.example.com/homework/today"
HISTORICAL_URL = "https://webtop.smartschool.co.il/Student_Card/11"


def run_scrape_once() -> int:
    db = HomeworkDB()
    with AuthSession() as auth:
        page = auth.login_and_get_page(
            login_url=LOGIN_URL,
            username_selector=USERNAME_SELECTOR,
            password_selector=PASSWORD_SELECTOR,
            submit_selector=SUBMIT_SELECTOR,
            target_url=TARGET_URL,
        )
        items = parse_homework_for_today(page)
        inserted = db.upsert_items(items)
        logger.info(f"Inserted {inserted} homework items for {date.today().isoformat()}")
        return inserted


def run_scrape_all_historical() -> int:
    """
    Scrape all historical homework from the Student_Card page.
    This will parse homework from all previous dates and add missing dates to the database.
    """
    db = HomeworkDB()
    with AuthSession() as auth:
        # Login first (don't need to go to any specific target)
        page = auth.login_and_get_page(
            login_url=LOGIN_URL,
            username_selector=USERNAME_SELECTOR,
            password_selector=PASSWORD_SELECTOR,
            submit_selector=SUBMIT_SELECTOR,
            target_url=None,
        )
        
        # Now navigate to the historical homework page
        logger.info(f"Navigating to historical homework page: {HISTORICAL_URL}")
        page.goto(HISTORICAL_URL, wait_until="networkidle", timeout=30000)
        
        # Wait for the page to fully load
        page.wait_for_selector("app-multi-cards-view", timeout=15000)
        page.wait_for_load_state("networkidle")
        logger.info(f"Successfully loaded historical homework page")
        
        # Parse all historical homework items
        items = parse_all_historical_homework(page)
        
        # Insert items into database (upsert will skip duplicates)
        inserted = db.upsert_items(items)
        logger.info(f"Inserted {inserted} new homework items from historical data")
        return inserted

if __name__ == "__main__":
    run_scrape_once()
