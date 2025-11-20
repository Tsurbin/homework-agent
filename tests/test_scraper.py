#!/usr/bin/env python3
"""
Simple script to test just the scraping functionality.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_scraper():
    """Test the scraper functionality."""
    print("🕷️  Testing Homework Scraper")
    print("=" * 40)
    
    try:
        # Import scraper
        from scraper.runner import run_scrape_once
        from scraper.db import HomeworkDB
        
        print("✅ Scraper modules imported successfully")
        
        # Check existing data
        db = HomeworkDB()
        existing_items = db.list()
        print(f"📊 Found {len(existing_items)} existing homework items in database")
        
        if existing_items:
            print("📝 Latest 3 items:")
            for item in existing_items[-3:]:
                print(f"   - {item.date}: {item.subject} - {item.description[:50]}...")
        
        # Ask user if they want to run actual scraping
        print(f"\n⚠️  About to run actual web scraping...")
        print(f"   This will:")
        print(f"   • Log into the homework website")
        print(f"   • Scrape today's homework")
        print(f"   • Save to local SQLite database")
        
        response = input(f"\n🤔 Do you want to proceed? (y/N): ").lower().strip()
        
        if response == 'y':
            print("\n🚀 Running scraper...")
            try:
                result = run_scrape_once()
                print(f"✅ Scraping completed successfully!")
                print(f"📈 Inserted/updated {result} homework items")
                
                # Show new total
                new_items = db.list()
                print(f"📊 Total items in database: {len(new_items)}")
                
            except Exception as e:
                print(f"❌ Scraping failed: {e}")
                print(f"💡 Check your credentials and network connection")
        else:
            print("⏭️  Skipping actual scraping test")
        
    except ImportError as e:
        print(f"❌ Failed to import scraper modules: {e}")
        print(f"💡 Make sure you're in the virtual environment:")
        print(f"   source venv/bin/activate")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_scraper()