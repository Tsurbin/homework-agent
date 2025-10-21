"""
Homework parser - extracts homework data from school website.
"""
import logging
from typing import List, Dict
from datetime import datetime, date
from playwright.sync_api import Page
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class HomeworkParser:
    """Parses homework assignments from school website."""
    
    def parse_homework(self, page: Page) -> List[Dict]:
        """
        Parse homework from the current page.
        
        This is a TEMPLATE - you need to customize based on your school website structure.
        
        Args:
            page: Playwright page instance
            
        Returns:
            List of homework dictionaries
        """
        homework_list = []
        
        try:
            logger.info("Starting homework parsing...")
            
            # TODO: Navigate to homework page if needed
            # page.click('a[href="/homework"]')
            # page.wait_for_selector('.homework-list')
            
            # Get page content
            html_content = page.content()
            soup = BeautifulSoup(html_content, 'lxml')
            
            # TODO: CUSTOMIZE THESE SELECTORS FOR YOUR SCHOOL WEBSITE
            # Example: Find all homework items
            homework_items = soup.select('.homework-item')
            
            logger.info(f"Found {len(homework_items)} homework items")
            
            for item in homework_items:
                try:
                    homework_data = self._parse_homework_item(item, page.url)
                    if homework_data:
                        homework_list.append(homework_data)
                except Exception as e:
                    logger.error(f"Error parsing homework item: {e}")
                    continue
            
            logger.info(f"✓ Successfully parsed {len(homework_list)} homework assignments")
            return homework_list
            
        except Exception as e:
            logger.error(f"Error parsing homework: {e}")
            raise
    
    def _parse_homework_item(self, item, source_url: str) -> Dict:
        """
        Parse a single homework item.
        
        TODO: Customize this method based on your website's HTML structure.
        
        Args:
            item: BeautifulSoup element
            source_url: URL where homework was found
            
        Returns:
            Dictionary with homework data
        """
        try:
            # TODO: CUSTOMIZE THESE SELECTORS
            # Example selectors - replace with actual ones
            
            # Extract subject
            subject_elem = item.select_one('.subject')
            subject = subject_elem.text.strip() if subject_elem else 'Unknown'
            
            # Extract title
            title_elem = item.select_one('.title')
            title = title_elem.text.strip() if title_elem else 'No title'
            
            # Extract description
            desc_elem = item.select_one('.description')
            description = desc_elem.text.strip() if desc_elem else None
            
            # Extract due date
            due_date_elem = item.select_one('.due-date')
            due_date = self._parse_date(due_date_elem.text.strip()) if due_date_elem else date.today()
            
            # Extract assigned date (or use today)
            assigned_date_elem = item.select_one('.assigned-date')
            assigned_date = self._parse_date(assigned_date_elem.text.strip()) if assigned_date_elem else date.today()
            
            # Extract homework type
            type_elem = item.select_one('.homework-type')
            homework_type = type_elem.text.strip() if type_elem else None
            
            # Extract priority (if available)
            priority_elem = item.select_one('.priority')
            priority = priority_elem.text.strip().lower() if priority_elem else 'normal'
            
            # Try to get unique ID from the website
            source_id = item.get('data-homework-id') or item.get('id')
            
            return {
                'subject': subject,
                'title': title,
                'description': description,
                'due_date': due_date,
                'assigned_date': assigned_date,
                'homework_type': homework_type,
                'priority': priority,
                'source_url': source_url,
                'source_id': source_id,
                'is_completed': False
            }
            
        except Exception as e:
            logger.error(f"Error parsing homework item details: {e}")
            return None
    
    def _parse_date(self, date_string: str) -> date:
        """
        Parse date string to date object.
        
        TODO: Customize date formats based on your website.
        
        Args:
            date_string: Date string from website
            
        Returns:
            date object
        """
        # Common date formats - add more as needed
        formats = [
            '%Y-%m-%d',           # 2024-10-21
            '%d/%m/%Y',           # 21/10/2024
            '%m/%d/%Y',           # 10/21/2024
            '%d-%m-%Y',           # 21-10-2024
            '%B %d, %Y',          # October 21, 2024
            '%d %B %Y',           # 21 October 2024
            '%d.%m.%Y',           # 21.10.2024
        ]
        
        # Clean the string
        date_string = date_string.strip()
        
        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt).date()
            except ValueError:
                continue
        
        # If no format matches, log warning and return today
        logger.warning(f"Could not parse date: '{date_string}', using today")
        return date.today()
    
    def extract_homework_details(self, page: Page, homework_url: str) -> Dict:
        """
        Extract detailed information from individual homework page.
        
        Optional: Use this if homework details are on separate pages.
        
        Args:
            page: Playwright page instance
            homework_url: URL of homework detail page
            
        Returns:
            Dictionary with detailed homework data
        """
        try:
            page.goto(homework_url, wait_until='networkidle')
            
            # TODO: Extract detailed information
            # This is useful if the main page only shows summaries
            
            html_content = page.content()
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Extract additional details
            # ...
            
            return {}
            
        except Exception as e:
            logger.error(f"Error extracting homework details from {homework_url}: {e}")
            return {}