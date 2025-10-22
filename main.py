#!/usr/bin/env python3
"""
Homework Agent CLI Entrypoint
"""
import argparse
from datetime import date
from pathlib import Path
from scraper.logging_setup import logger
from scraper.runner import run_scrape_once
from scraper.db import HomeworkDB

def main():
    parser = argparse.ArgumentParser(description="Homework Agent")
    parser.add_argument("--scrape", action="store_true", help="Run a single scrape")
    parser.add_argument("--list", type=str, help="List homework for date (YYYY-MM-DD)")
    parser.add_argument("--today", action="store_true", help="List today's homework")
    
    args = parser.parse_args()
    
    if args.scrape:
        logger.info("Starting homework scrape...")
        count = run_scrape_once()
        print(f"Scraped {count} homework items")
        
    elif args.list:
        db = HomeworkDB()
        items = db.list_by_date(args.list)
        if items:
            print(f"\nHomework for {args.list}:")
            for item in items:
                print(f"  {item.subject}: {item.description}")
                if item.due_date:
                    print(f"    Due: {item.due_date}")
        else:
            print(f"No homework found for {args.list}")
            
    elif args.today:
        db = HomeworkDB()
        today = date.today().isoformat()
        items = db.list_by_date(today)
        if items:
            print(f"\nToday's homework ({today}):")
            for item in items:
                print(f"  {item.subject}: {item.description}")
                if item.due_date:
                    print(f"    Due: {item.due_date}")
        else:
            print(f"No homework found for today ({today})")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
