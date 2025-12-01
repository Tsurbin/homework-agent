# Lambda-compatible scraper module
from database.dynamodb_handler import DynamoDBHandler, HomeworkItem
from .lambda_runner import run_scrape_lambda

__all__ = [
    'HomeworkItem', 
    'DynamoDBHandler',
    'run_scrape_lambda'
]
