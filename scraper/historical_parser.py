from __future__ import annotations
from typing import List
from datetime import datetime
from .db import HomeworkItem
from playwright.sync_api import Page
from loguru import logger
import re

# Selectors for the historical homework page structure
MULTI_CARDS_VIEW = "app-multi-cards-view"
LESSON_HOMEWORK = "app-lesson-homework"
LESSON_HOMEWORK_VIEW = "app-lesson-homework-view"
DATE_CARD_SELECTOR = "app-content-card mat-card"


def parse_date_from_card_title(title: str) -> str | None:
    """
    Parse date from Hebrew title like "יום ראשון | 26/10/2025 | ד׳ חֶשְׁוָן תשפ״ו"
    Returns date in YYYY-MM-DD format
    """
    # Extract the date pattern DD/MM/YYYY
    match = re.search(r'(\d{2})/(\d{2})/(\d{4})', title)
    if match:
        day, month, year = match.groups()
        try:
            # Convert to YYYY-MM-DD format
            date_obj = datetime.strptime(f"{year}-{month}-{day}", "%Y-%m-%d")
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            logger.warning(f"Invalid date parsed from title: {title}")
            return None
    return None


def parse_all_historical_homework(page: Page) -> List[HomeworkItem]:
    """
    Parse all homework from the historical view page (Student_Card/11).
    This page contains homework from all previous dates.
    """
    items: List[HomeworkItem] = []
    
    # Find all date cards
    date_cards = page.query_selector_all(DATE_CARD_SELECTOR)
    logger.info(f"Found {len(date_cards)} date cards")
    
    for card in date_cards:
        # Extract the date from the card title
        title_element = card.query_selector("mat-card-title .card-title")
        if not title_element:
            continue
            
        title_text = title_element.inner_text().strip()
        date_str = parse_date_from_card_title(title_text)
        
        if not date_str:
            logger.warning(f"Could not parse date from title: {title_text}")
            continue
            
        logger.info(f"Processing homework for date: {date_str}")
        
        # Find all lesson rows within this card
        lesson_rows = card.query_selector_all(".lesson-wrpper")
        
        for lesson_row in lesson_rows:
            # Get the actual row div inside the wrapper
            row_div = lesson_row.query_selector("div[role='row']")
            if not row_div:
                continue
            
            # Get all cells in order
            cells = row_div.query_selector_all("span[role='cell']")
            if len(cells) < 6:
                logger.warning(f"Row has only {len(cells)} cells, expected at least 6")
                continue
            
            # Column 1: Lesson number (שעה) - e.g., "שיעור 1", "שיעור 2"
            lesson_num = cells[0].inner_text().strip()
            
            # Column 2: Subject (מקצוע)
            subject_el = cells[1].query_selector("a.link-text")
            if not subject_el:
                continue
            subject = subject_el.inner_text().strip()
            
            # Column 3: Teacher name (מורה)
            teacher = cells[2].inner_text().strip()
            
            # Column 4: Lesson status (סטטוס שיעור)
            status = cells[3].inner_text().strip()
            
            # Column 5: Lesson topic (נושא שיעור/סיבת ביטול)
            topic_text = cells[4].inner_text().strip()
            # Remove the "נושא שיעור: " prefix if it exists
            topic = topic_text.replace("נושא שיעור: ", "")
            
            # Column 6: Homework (שיעורי בית)
            homework_text = ""
            if len(cells) > 5:
                # Look for the span with homework text inside
                homework_span = cells[5].query_selector("span.font-small")
                if homework_span:
                    homework_text = homework_span.inner_text().strip()
                else:
                    # Sometimes the text might be directly in the cell without span.font-small
                    cell_text = cells[5].inner_text().strip()
                    # Remove the "שיעורי בית: " prefix if it exists
                    if cell_text and "שיעורי בית:" in cell_text:
                        homework_text = cell_text.replace("שיעורי בית: ", "").strip()
            
            # Build the description
            description_parts = []
            if lesson_num:
                description_parts.append(f"{lesson_num}")
            if subject:
                description_parts.append(f"מקצוע: {subject}")
            if teacher:
                description_parts.append(f"מורה: {teacher}")
            if status:
                description_parts.append(f"סטטוס: {status}")
            if topic:
                description_parts.append(f"נושא: {topic}")
            
            full_description = "\n".join(description_parts)
            
            if not homework_text:
                continue
            
            items.append(HomeworkItem(
                id=None,
                date=date_str,
                subject=subject,
                description=full_description,
                due_date=None,  # Due date not available in this structure
                homework_text=homework_text if homework_text else None,
                source=page.url
            ))
    
    logger.info(f"Parsed {len(items)} homework items from historical data")
    return items
