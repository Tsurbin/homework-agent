# Lambda-compatible scraper module
from .db import HomeworkDB, HomeworkItem
from .dynamodb_handler import DynamoDBHandler
from .simple_lambda_runner import SimpleLambdaRunner

__all__ = [
    'HomeworkDB',
    'HomeworkItem',
    'DynamoDBHandler',
    'SimpleLambdaRunner'
]
