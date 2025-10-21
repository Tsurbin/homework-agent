"""
Main entry point for the homework scraper.
"""
import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

from config.settings import get_settings
from database.db_manager import DatabaseManager
from scraper.browser_manager import BrowserManager
from scraper.auth import Authenticator, AuthenticationError
from scraper.homework_parser import HomeworkParser

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scraper.log')
    ]
)
logger = logging.getLogger(__name__)


class HomeworkScraper:
    """Main scraper coordinator."""
    
    def __init__(self):
        self.settings = get_settings()
        self.db = DatabaseManager()
        self.authenticator = Authenticator()
        self.parser = HomeworkParser()
    
    def scrape(self):
        """Execute scraping workflow."""
        start_time = datetime.now()
        homework_count = 0
        status = 'success'
        error_message = None
        
        try:
            logger.info("=" * 60)
            logger.info("Starting homework scraping session")
            logger.info("=" * 60)
            # Create a single browser session so login cookies persist
            with BrowserManager() as bm:
                page = bm.page

                # perform login using same page
                try:
                    self.authenticator.login_on_page(page)
                except AuthenticationError as e:
                    logger.error("Authentication failed: %s", e)
                    raise

                # navigate to homework list (site-specific)
                page.goto(self.settings.school_base_url)
                items = self.parser.parse_homework(page)

                for it in items:
                    # expected keys: subject, description, due_date
                    if getattr(self, 'dry_run', False):
                        logger.info("DRY RUN - would insert: %s", it)
                    else:
                        try:
                            self.db.insert_homework(it.get('subject', 'unknown'), it.get('description', ''), it.get('due_date'))
                        except Exception as e:
                            logger.error("DB insert failed: %s", e)
                    homework_count += 1

            logger.info("Scraping completed, items found: %d", homework_count)
            return {
                'status': status,
                'homework_count': homework_count,
                'duration_seconds': (datetime.now() - start_time).total_seconds(),
            }

        except Exception as e:
            logger.exception("Unhandled error during scraping: %s", e)
            status = 'failure'
            error_message = str(e)

            return {
                'status': status,
                'homework_count': homework_count,
                'error': error_message,
                'duration_seconds': (datetime.now() - start_time).total_seconds(),
            }


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='Homework Scraper')
    parser.add_argument('--init-db', action='store_true', help='Initialize database')
    parser.add_argument('--scrape', action='store_true', help='Scrape homework from website')
    parser.add_argument('--list', type=int, nargs='?', const=7, metavar='DAYS', 
                       help='List upcoming homework (default: 7 days)')
    parser.add_argument('--logs', type=int, nargs='?', const=10, metavar='LIMIT',
                       help='Show recent scraping logs (default: 10)')
    parser.add_argument('--clear', action='store_true', help='Clear all homework (use with caution!)')
    
    args = parser.parse_args()
    
    try:
        scraper = HomeworkScraper()
        
        if args.init_db:
            print("Initializing database...")
            scraper.db.init_db()
            print("✓ Database initialized successfully!")
            
        elif args.scrape:
            scraper.scrape()
            
        elif args.list is not None:
            scraper.list_homework(days=args.list)
            
        elif args.logs is not None:
            scraper.show_logs(limit=args.logs)
            
        elif args.clear:
            confirm = input("⚠️  Are you sure you want to clear ALL homework? (yes/no): ")
            if confirm.lower() == 'yes':
                scraper.db.clear_all_homework()
            else:
                print("Cancelled.")
        
        else:
            parser.print_help()
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()