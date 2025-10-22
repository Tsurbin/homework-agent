#!/usr/bin/env python3
"""
Enhanced debugging with ipdb and rich output
"""
import ipdb
from rich.console import Console
from rich.traceback import install
from scraper.logging_setup import logger
from scraper.runner import run_scrape_once
from scraper.db import HomeworkDB

# Install rich traceback for better error display
install()

console = Console()

def debug_with_rich():
    """Enhanced debugging with rich output"""
    console.print("[bold blue]🐛 Starting Enhanced Debug Session[/bold blue]")
    
    # Method 1: Set breakpoint with ipdb (better than pdb)
    ipdb.set_trace()
    
    # Method 2: Alternative - you can also use:
    # import ipdb; ipdb.set_trace()  # Add this line anywhere you want to break
    
    try:
        # Debug database operations
        db = HomeworkDB()
        console.print(f"[green]Database path: {db.path}[/green]")
        
        # Debug scraping
        console.print("[yellow]Starting scrape...[/yellow]")
        count = run_scrape_once()
        
        # Debug results
        today_items = db.list_by_date("2024-01-01")  # Replace with actual date
        console.print(f"[green]Found {len(today_items)} items in DB[/green]")
        
        for item in today_items:
            console.print(f"  📝 {item.subject}: {item.description}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        ipdb.post_mortem()

if __name__ == "__main__":
    debug_with_rich()
