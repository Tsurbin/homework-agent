from __future__ import annotations
from datetime import date
from loguru import logger
from .db import HomeworkDB
from .auth import AuthSession
from .homework_parser import parse_homework_for_today

# Placeholder selectors and URLs; update for your site
LOGIN_URL = "https://lgn.edu.gov.il/nidp/wsfed/ep?id=EduCombinedAuthUidPwd&sid=0&option=credential&sid=0"
USERNAME_SELECTOR = "#userName"
PASSWORD_SELECTOR = "#password"
SUBMIT_SELECTOR = "button[type=submit]"
TARGET_URL = "https://school.example.com/homework/today"


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

if __name__ == "__main__":
    run_scrape_once()
