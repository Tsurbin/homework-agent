from __future__ import annotations
from typing import List
from datetime import date
from .db import HomeworkItem
from playwright.sync_api import Page

# NOTE: Replace CSS selectors with the real site structure
HOMEWORK_ROW_SELECTOR = "tr.homework-row"
SUBJECT_SELECTOR = ".subject"
DESCRIPTION_SELECTOR = ".description"
DUE_SELECTOR = ".due-date"


def parse_homework_for_today(page: Page) -> List[HomeworkItem]:
    today = date.today().isoformat()
    items: list[HomeworkItem] = []
    for row in page.query_selector_all(HOMEWORK_ROW_SELECTOR):
        subject = row.query_selector(SUBJECT_SELECTOR).inner_text().strip()
        desc = row.query_selector(DESCRIPTION_SELECTOR).inner_text().strip()
        due_el = row.query_selector(DUE_SELECTOR)
        due = due_el.inner_text().strip() if due_el else None
        items.append(HomeworkItem(id=None, date=today, subject=subject, description=desc, due_date=due, source=page.url))
    return items
