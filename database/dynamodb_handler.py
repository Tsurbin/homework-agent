"""
DynamoDB handler for storing homework data in AWS DynamoDB.
This replaces the SQLite database with a cloud-native solution.
"""
from __future__ import annotations
import os
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Iterable, List, Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

@dataclass
class HomeworkItem:
    """
    Homework item data structure - optimized for DynamoDB.
    """
    date: str  # YYYY-MM-DD (will be part of composite key)
    subject: str  # Subject name
    description: str  # Homework description
    hour: str = None  # The lesson hour (שעה) - e.g., "שיעור 1", "שיעור 2"
    due_date: Optional[str] = None  # YYYY-MM-DD
    homework_text: Optional[str] = None  # The actual homework assignment text
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    teacher: Optional[str] = None  # Teacher name
    class_description: Optional[str] = None  # Class description
    
    @property
    def composite_key(self) -> str:
        """Generate composite key for DynamoDB: date#hour#subject"""
        hour_part = self.hour or "unknown"
        return f"{self.date}#{hour_part}#{self.subject}"


class DynamoDBHandler:
    """
    DynamoDB handler for homework items.
    
    Table structure:
    - Partition Key (PK): date (YYYY-MM-DD)
    - Sort Key (SK): hour#subject (e.g., "שיעור 1#מתמטיקה")
    - Attributes: description, due_date, homework_text, created_at, updated_at
    """
    
    def __init__(self, table_name: str, region_name: str = None):
        self.table_name = table_name
        self.region_name = region_name or os.environ.get('AWS_REGION', 'us-east-1')
        
        # Initialize DynamoDB client and resource
        self.dynamodb = boto3.resource('dynamodb', region_name=self.region_name)
        self.table = self.dynamodb.Table(table_name)
        
        logger.info(f"Initialized DynamoDB handler for table: {table_name}")
    
    def create_table_if_not_exists(self) -> bool:
        """
        Create the DynamoDB table if it doesn't exist.
        
        Returns:
            True if table was created, False if it already existed
        """
        try:
            # Check if table exists
            self.table.load()
            logger.info(f"Table {self.table_name} already exists")
            return False
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # Table doesn't exist, create it
                logger.info(f"Creating table {self.table_name}")
                
                table = self.dynamodb.create_table(
                    TableName=self.table_name,
                    KeySchema=[
                        {
                            'AttributeName': 'date',
                            'KeyType': 'HASH'  # Partition key
                        },
                        {
                            'AttributeName': 'hour_subject',
                            'KeyType': 'RANGE'  # Sort key
                        }
                    ],
                    AttributeDefinitions=[
                        {
                            'AttributeName': 'date',
                            'AttributeType': 'S'
                        },
                        {
                            'AttributeName': 'hour_subject',
                            'AttributeType': 'S'
                        }
                    ],
                    BillingMode='PAY_PER_REQUEST'  # On-demand billing
                )
                
                # Wait for table to be created
                table.wait_until_exists()
                logger.info(f"Table {self.table_name} created successfully")
                return True
            else:
                raise e
    
    def upsert_items(self, items: Iterable[HomeworkItem]) -> int:
        """
        Upsert homework items to DynamoDB.
        Uses conditional updates to only modify items when content has changed.
        
        Args:
            items: Iterable of HomeworkItem objects
            
        Returns:
            Number of items actually inserted or updated
        """
        count = 0
        
        for item in items:
            try:
                # Generate hour_subject sort key
                hour_part = item.hour or "unknown"
                hour_subject = f"{hour_part}#{item.subject}"
                
                # Prepare item data
                current_time = datetime.now(timezone.utc).isoformat()
                item_data = {
                    'date': item.date,
                    'hour_subject': hour_subject,
                    'subject': item.subject,
                    'description': item.description,
                    'hour': item.hour,
                    'due_date': item.due_date,
                    'homework_text': item.homework_text,
                    'created_at': item.created_at,
                    'updated_at': current_time
                }
                
                # Remove None values
                item_data = {k: v for k, v in item_data.items() if v is not None}
                
                # Try to get existing item
                try:
                    response = self.table.get_item(
                        Key={
                            'date': item.date,
                            'hour_subject': hour_subject
                        }
                    )
                    
                    existing_item = response.get('Item')
                    
                    if existing_item:
                        # Check if meaningful content has changed
                        content_changed = (
                            existing_item.get('homework_text', '') != (item.homework_text or '') or
                            existing_item.get('description', '') != item.description
                        )
                        
                        if content_changed:
                            # Update existing item
                            self.table.put_item(Item=item_data)
                            count += 1
                            logger.debug(f"Updated homework item: {item.date} - {item.subject}")
                        else:
                            logger.debug(f"No changes for homework item: {item.date} - {item.subject}")
                    else:
                        # Insert new item
                        self.table.put_item(Item=item_data)
                        count += 1
                        logger.debug(f"Inserted new homework item: {item.date} - {item.subject}")
                        
                except ClientError as e:
                    logger.error(f"Error upserting item {item.date} - {item.subject}: {e}")
                    continue
                    
            except Exception as e:
                logger.error(f"Error processing homework item: {e}", exc_info=True)
                continue
        
        logger.info(f"Upserted {count} homework items to DynamoDB")
        return count
    
    def get_items_by_date(self, date: str) -> List[Dict[str, Any]]:
        """
        Get all homework items for a specific date.
        
        Args:
            date: Date in YYYY-MM-DD format
            
        Returns:
            List of homework items
        """
        try:
            response = self.table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('date').eq(date)
            )
            
            items = response.get('Items', [])
            
            # Sort by hour and subject
            items.sort(key=lambda x: (x.get('hour', 'unknown'), x.get('subject', '')))
            
            logger.debug(f"Retrieved {len(items)} items for date {date}")
            return items
            
        except ClientError as e:
            logger.error(f"Error querying items for date {date}: {e}")
            return []
    
    def get_all_items(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Get all homework items from the table.
        
        Args:
            limit: Optional limit on number of items to return
            
        Returns:
            List of homework items
        """
        try:
            if limit:
                response = self.table.scan(Limit=limit)
            else:
                response = self.table.scan()
            
            items = response.get('Items', [])
            
            # Handle pagination if needed
            while 'LastEvaluatedKey' in response and (not limit or len(items) < limit):
                remaining_limit = limit - len(items) if limit else None
                scan_kwargs = {'ExclusiveStartKey': response['LastEvaluatedKey']}
                if remaining_limit:
                    scan_kwargs['Limit'] = remaining_limit
                    
                response = self.table.scan(**scan_kwargs)
                items.extend(response.get('Items', []))
            
            # Sort by date, hour, and subject
            items.sort(key=lambda x: (x.get('date', ''), x.get('hour', 'unknown'), x.get('subject', '')))
            
            logger.debug(f"Retrieved {len(items)} total items from DynamoDB")
            return items
            
        except ClientError as e:
            logger.error(f"Error scanning all items: {e}")
            return []
    
    
    def get_all_items_from_date(self, start_date: str) -> List[Dict[str, Any]]:
        """
        Get all homework items from a specific start date onwards.
        
        Args:
            start_date: Date in YYYY-MM-DD format
        Returns:
            List of homework items
        """ 
        try:
            response = self.table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('date').gte(start_date)
            )
            
            items = response.get('Items', [])
            
            # Handle pagination if needed
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(
                    ExclusiveStartKey=response['LastEvaluatedKey'],
                    FilterExpression=boto3.dynamodb.conditions.Attr('date').gte(start_date)
                )
                items.extend(response.get('Items', []))
            
            # Sort by date, hour, and subject
            items.sort(key=lambda x: (x.get('date', ''), x.get('hour', 'unknown'), x.get('subject', '')))
            
            logger.debug(f"Retrieved {len(items)} items from date {start_date} onwards")
            return items
            
        except ClientError as e:
            logger.error(f"Error scanning items from date {start_date}: {e}")
            return []
    
    def delete_item(self, date: str, hour: str, subject: str) -> bool:
        """
        Delete a specific homework item.
        
        Args:
            date: Date in YYYY-MM-DD format
            hour: Hour string
            subject: Subject name
            
        Returns:
            True if deleted successfully
        """
        try:
            hour_part = hour or "unknown"
            hour_subject = f"{hour_part}#{subject}"
            
            self.table.delete_item(
                Key={
                    'date': date,
                    'hour_subject': hour_subject
                }
            )
            
            logger.info(f"Deleted homework item: {date} - {subject}")
            return True
            
        except ClientError as e:
            logger.error(f"Error deleting item {date} - {subject}: {e}")
            return False