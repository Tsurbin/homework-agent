#!/usr/bin/env python3
"""
Clean/reset the homework database
"""
import argparse
from pathlib import Path
from scraper.db import HomeworkDB, DB_PATH

def clean_database(confirm: bool = False):
    """Delete the database file to start fresh"""
    if DB_PATH.exists():
        if not confirm:
            print(f"Database found at: {DB_PATH}")
            response = input("Are you sure you want to delete it? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("Cancelled.")
                return
        
        DB_PATH.unlink()
        print(f"✓ Database deleted: {DB_PATH}")
        print("A new empty database will be created on next use.")
    else:
        print(f"No database found at: {DB_PATH}")

def reset_database():
    """Delete all data but keep the database structure"""
    db = HomeworkDB()
    with db._connect() as conn:
        # Delete all homework items
        cursor = conn.execute("DELETE FROM homework")
        homework_count = cursor.rowcount
        
        # Delete all page snapshots
        cursor = conn.execute("DELETE FROM pages")
        pages_count = cursor.rowcount
        
        conn.commit()
    
    print(f"✓ Deleted {homework_count} homework items")
    print(f"✓ Deleted {pages_count} page snapshots")
    print("Database structure preserved (tables and indexes intact).")

def show_stats():
    """Show database statistics"""
    if not DB_PATH.exists():
        print(f"No database found at: {DB_PATH}")
        return
    
    db = HomeworkDB()
    with db._connect() as conn:
        # Count homework items
        cursor = conn.execute("SELECT COUNT(*) FROM homework")
        homework_count = cursor.fetchone()[0]
        
        # Count pages
        cursor = conn.execute("SELECT COUNT(*) FROM pages")
        pages_count = cursor.fetchone()[0]
        
        # Get date range
        cursor = conn.execute("SELECT MIN(date), MAX(date) FROM homework")
        date_range = cursor.fetchone()
        
        # Count unique dates
        cursor = conn.execute("SELECT COUNT(DISTINCT date) FROM homework")
        unique_dates = cursor.fetchone()[0]
    
    print(f"Database: {DB_PATH}")
    print(f"Homework items: {homework_count}")
    print(f"Page snapshots: {pages_count}")
    print(f"Unique dates: {unique_dates}")
    if date_range[0] and date_range[1]:
        print(f"Date range: {date_range[0]} to {date_range[1]}")

def main():
    parser = argparse.ArgumentParser(description="Clean/reset homework database")
    parser.add_argument("--delete", action="store_true", help="Delete the database file completely")
    parser.add_argument("--reset", action="store_true", help="Clear all data but keep structure")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")
    
    args = parser.parse_args()
    
    if args.stats:
        show_stats()
    elif args.delete:
        clean_database(confirm=args.yes)
    elif args.reset:
        reset_database()
    else:
        parser.print_help()
        print("\nCurrent database status:")
        show_stats()

if __name__ == "__main__":
    main()
