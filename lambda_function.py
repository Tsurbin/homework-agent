"""
AWS Lambda function for running the homework scraper on a schedule.
This function is designed to be triggered by EventBridge (CloudWatch Events) scheduler.
"""
import json
import os
import logging
from typing import Dict, Any
from datetime import date

# Configure logging for Lambda
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Import your scraper modules
from scraper.lambda_runner import run_scrape_lambda

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda handler function that will be called by AWS Lambda.
    
    Args:
        event: Event data passed by the trigger (e.g., EventBridge)
        context: Lambda context object
        
    Returns:
        Dict containing status and results
    """
    try:
        logger.info(f"Starting homework scraper at {date.today().isoformat()}")
        logger.info(f"Event: {json.dumps(event)}")
        
        # Determine scrape type from event
        scrape_type = "historical" #"daily"  # default
        historical = True
        
        if event.get('source') == 'aws.events':
            # EventBridge trigger
            detail_type = event.get('detail-type', '')
            if 'Historical' in detail_type:
                historical = True
                scrape_type = "historical"
        elif 'scrape_type' in event:
            # Manual invocation with specific type
            scrape_type = event['scrape_type']
            historical = (scrape_type == "historical")
        
        logger.info(f"Running scraper with type: {scrape_type}")
        
        # Run the scraper using the original logic
        items_saved = run_scrape_lambda(historical=historical)
        
        logger.info(f"Scraping completed successfully. Saved {items_saved} items")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Successfully scraped {items_saved} homework items',
                'items_saved': items_saved,
                'scrape_type': scrape_type,
                'date': date.today().isoformat()
            })
        }

    except Exception as e:
        error_msg = f"Lambda function failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': error_msg,
                'date': date.today().isoformat()
            })
        }

# For testing locally
if __name__ == "__main__":
    # Test the lambda function locally
    test_event = {'scrape_type': 'historical'}
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))