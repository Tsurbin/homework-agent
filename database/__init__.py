"""
Database layer for homework agent.
Handles all database operations including DynamoDB access.
"""
from .dynamodb_handler import DynamoDBHandler

__all__ = ['DynamoDBHandler']
