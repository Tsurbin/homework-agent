#!/usr/bin/env python3
"""
Debug script for homework scraper
"""
import pdb
from scraper.logging_setup import logger
from scraper.runner import run_scrape_once

def debug_scrape():
    """Run scraper with debugger"""
    logger.info("Starting debug session...")
    
    # Set breakpoint here
    pdb.set_trace()
    
    try:
        count = run_scrape_once()
        logger.info(f"Scraped {count} items")
        return count
    except Exception as e:
        logger.error(f"Scrape failed: {e}")
        pdb.post_mortem()  # Enter debugger on exception
        raise

if __name__ == "__main__":
    debug_scrape()
