#!/usr/bin/env python3
"""
Remote debugging setup
"""
import debugpy
from scraper.logging_setup import logger

def setup_remote_debug():
    """Setup remote debugging on port 5678"""
    debugpy.listen(("0.0.0.0", 5678))
    logger.info("Remote debugger listening on port 5678")
    logger.info("Connect VS Code to localhost:5678")
    
    # Wait for debugger to attach
    debugpy.wait_for_client()
    logger.info("Debugger attached!")

if __name__ == "__main__":
    setup_remote_debug()
    # Your code here
    from scraper.runner import run_scrape_once
    run_scrape_once()
