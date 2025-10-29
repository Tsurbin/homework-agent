#!/usr/bin/env python3
"""
Daily scheduler for homework scraping
"""
import schedule
import time
from scraper.logging_setup import logger
from scraper.runner import run_scrape_once

def daily_scrape():
    """Run the daily homework scrape"""
    try:
        logger.info("Starting scheduled homework scrape...")
        count = run_scrape_once()
        logger.info(f"Scheduled scrape completed: {count} items")
    except Exception as e:
        logger.error(f"Scheduled scrape failed: {e}")

def main():
    # Schedule daily scrape at 6 PM
    schedule.every().day.at("18:00").do(daily_scrape)
    
    logger.info("Homework scheduler started - running daily at 6 PM")
    logger.info("Press Ctrl+C to stop")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")

if __name__ == "__main__":
    main()
