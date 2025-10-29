from __future__ import annotations
from typing import List
from datetime import date
from .db import HomeworkItem
from playwright.sync_api import Page

# Selectors matching the Angular Material card structure
HOMEWORK_CONTAINER_SELECTOR = "mat-card-content .card-content-row"
SUBJECT_SELECTOR = ".col.l12.s6.bold-text a.link-text"
DESCRIPTION_SELECTOR = ".col.l24.s12.allow-text-overflow b:has-text('נושא שיעור: ') ~ text"
HOMEWORK_SELECTOR = ".col.l24.s12.allow-text-overflow b:has-text('שיעורי בית:') ~ .font-small"


def parse_homework_for_today(page: Page) -> List[HomeworkItem]:
    today = date.today().isoformat()
    items: list[HomeworkItem] = []
    
    # Get all homework rows from the card content
    for row in page.query_selector_all(HOMEWORK_CONTAINER_SELECTOR):
        # Extract subject (e.g., "שפה")
        subject_el = row.query_selector(SUBJECT_SELECTOR)
        if not subject_el:
            continue
        subject = subject_el.inner_text().strip()
        
        # Extract lesson topic/description
        desc_el = row.query_selector(DESCRIPTION_SELECTOR)
        description = desc_el.inner_text().strip() if desc_el else ""
        
        # Extract homework text if exists
        homework_el = row.query_selector(HOMEWORK_SELECTOR)
        homework_text = homework_el.inner_text().strip() if homework_el else None
        
        if not homework_text or homework_text == "לא הוזן":
            # No homework assigned
            continue
        
        # Build description based on whether homework exists
        full_description = f"נושא: {description}"
        
        items.append(HomeworkItem(
            id=None,
            date=today,
            subject=subject,
            description=full_description,
            due_date=None,  # Due date not available in current structure
            homework_text=homework_text if homework_text and homework_text != "לא הוזן" else None,
            source=page.url
        ))
    
    return items
