# Homework Scraper Lambda Deployment Guide

## Overview

This guide explains how to deploy the homework scraper to AWS Lambda with DynamoDB storage and EventBridge scheduling. The Lambda version provides a serverless, scalable solution that runs automatically on a schedule.

## Architecture

```
EventBridge (Schedule) → Lambda Function → DynamoDB Table
                                ↓
                        Playwright (Web Scraping)
```

### Components

1. **AWS Lambda Function**: Runs the scraper code
2. **DynamoDB Table**: Stores homework data (replaces SQLite)
3. **EventBridge Rules**: Triggers the scraper on schedule
4. **IAM Roles**: Provides necessary permissions

## Key Changes for Lambda

### 1. Database Layer (DynamoDB vs SQLite)

**Original (SQLite)**:
```python
from .db import HomeworkDB
db = HomeworkDB()
db.upsert_items(items)
```

**Lambda (DynamoDB)**:
```python
from database.dynamodb_handler import DynamoDBHandler
db = DynamoDBHandler(table_name='homework-items')
db.upsert_items(items)
```

### 2. DynamoDB Table Structure

**Primary Key**: Composite key for efficient querying
- **Partition Key (PK)**: `date` (YYYY-MM-DD)
- **Sort Key (SK)**: `hour_subject` (e.g., "שיעור 1#מתמטיקה")

**Attributes**:
- `subject`: Subject name
- `description`: Homework description  
- `hour`: Lesson hour
- `due_date`: Due date (optional)
- `homework_text`: Actual homework content
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### 3. Configuration Management

**Environment Variables in Lambda**:
```bash
HW_USERNAME=your_username
HW_PASSWORD=your_password
DYNAMODB_TABLE_NAME=homework-items
LOGIN_URL=https://webtop.smartschool.co.il/account/login
# ... other URLs and selectors
```

### 4. Lambda Handler Function

```python
def lambda_handler(event, context):
    """
    Main entry point for Lambda.
    Triggered by EventBridge on schedule.
    """
    scrape_type = event.get('scrape_type', 'daily')
    
    if scrape_type == 'historical':
        result = run_scrape_lambda(historical=True)
    else:
        result = run_scrape_lambda(historical=False)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'inserted_items': result,
            'scrape_type': scrape_type
        })
    }
```

## DynamoDB Connection Details

### 1. Connection Setup

```python
import boto3
from botocore.exceptions import ClientError

class DynamoDBHandler:
    def __init__(self, table_name: str, region_name: str = None):
        self.table_name = table_name
        self.region_name = region_name or os.environ.get('AWS_REGION', 'us-east-1')
        
        # Initialize DynamoDB client and resource
        self.dynamodb = boto3.resource('dynamodb', region_name=self.region_name)
        self.table = self.dynamodb.Table(table_name)
```

### 2. Table Creation

```python
def create_table_if_not_exists(self):
    table = self.dynamodb.create_table(
        TableName=self.table_name,
        KeySchema=[
            {'AttributeName': 'date', 'KeyType': 'HASH'},      # Partition key
            {'AttributeName': 'hour_subject', 'KeyType': 'RANGE'}  # Sort key
        ],
        AttributeDefinitions=[
            {'AttributeName': 'date', 'AttributeType': 'S'},
            {'AttributeName': 'hour_subject', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'  # On-demand billing
    )
```

### 3. Data Operations

**Insert/Update Items**:
```python
def upsert_items(self, items):
    for item in items:
        hour_subject = f"{item.hour or 'unknown'}#{item.subject}"
        
        # Check for existing item
        existing = self.table.get_item(
            Key={'date': item.date, 'hour_subject': hour_subject}
        ).get('Item')
        
        if existing and content_changed(existing, item):
            # Update existing
            self.table.put_item(Item=item_data)
        elif not existing:
            # Insert new
            self.table.put_item(Item=item_data)
```

**Query by Date**:
```python
def get_items_by_date(self, date: str):
    response = self.table.query(
        KeyConditionExpression=Key('date').eq(date)
    )
    return response.get('Items', [])
```

**Scan All Items**:
```python
def get_all_items(self, limit=None):
    if limit:
        response = self.table.scan(Limit=limit)
    else:
        response = self.table.scan()
    
    # Handle pagination
    items = response.get('Items', [])
    while 'LastEvaluatedKey' in response:
        response = self.table.scan(
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        items.extend(response.get('Items', []))
    
    return items
```

## Scheduling with EventBridge

### 1. Daily Scraper

```json
{
  "Rules": [
    {
      "Name": "daily-homework-scraper",
      "ScheduleExpression": "rate(1 day)",
      "Targets": [
        {
          "Arn": "arn:aws:lambda:region:account:function:homework-scraper",
          "Input": "{\"scrape_type\": \"daily\"}"
        }
      ]
    }
  ]
}
```

### 2. Weekly Historical Scraper

```json
{
  "Rules": [
    {
      "Name": "historical-homework-scraper", 
      "ScheduleExpression": "cron(0 2 ? * SUN *)",
      "Targets": [
        {
          "Arn": "arn:aws:lambda:region:account:function:homework-scraper",
          "Input": "{\"scrape_type\": \"historical\"}"
        }
      ]
    }
  ]
}
```

### 3. Schedule Expression Examples

- `rate(1 day)`: Every day
- `rate(12 hours)`: Every 12 hours
- `cron(0 8 * * ? *)`: Daily at 8 AM
- `cron(0 8 ? * MON-FRI *)`: Weekdays at 8 AM
- `cron(0 2 ? * SUN *)`: Sundays at 2 AM

## Deployment Steps

### 1. Prerequisites

```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install

# Configure AWS credentials
aws configure
```

### 2. Deploy Infrastructure

```bash
# Make deployment script executable
chmod +x deploy.sh

# Run complete deployment
./deploy.sh all

# Or step by step:
./deploy.sh check      # Check requirements
./deploy.sh package    # Create deployment package
./deploy.sh deploy     # Deploy CloudFormation stack
./deploy.sh update-code # Update Lambda function code
./deploy.sh test       # Test the function
```

### 3. Monitor Deployment

```bash
# View CloudFormation stack
aws cloudformation describe-stacks --stack-name homework-scraper-stack

# View Lambda function logs
aws logs tail /aws/lambda/homework-scraper --follow

# Test function manually
aws lambda invoke --function-name homework-scraper response.json
```

## Cost Considerations

### DynamoDB Costs

- **On-demand billing**: Pay per request
- **Typical usage**: ~1000 items, minimal reads
- **Estimated cost**: $1-5/month

### Lambda Costs

- **Free tier**: 1M requests + 400,000 GB-seconds/month
- **Typical usage**: 1-2 invocations/day
- **Estimated cost**: Free under free tier

### Total Estimated Cost: $1-10/month

## Troubleshooting

### Common Issues

1. **Playwright in Lambda**:
   - Use Lambda layers for Playwright
   - Or consider Lambda containers for full browser support

2. **Timeout Issues**:
   - Increase Lambda timeout (max 15 minutes)
   - Optimize scraping logic for faster execution

3. **DynamoDB Throttling**:
   - Use on-demand billing to avoid throttling
   - Implement exponential backoff for retries

4. **Authentication Issues**:
   - Store credentials in AWS Secrets Manager
   - Use IAM roles instead of access keys when possible

### Monitoring

```bash
# CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=homework-scraper \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Average

# DynamoDB metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=homework-items \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

## Security Best Practices

1. **Use IAM roles** with minimal required permissions
2. **Store secrets** in AWS Secrets Manager or Parameter Store
3. **Enable CloudTrail** for API logging
4. **Use VPC endpoints** for private communication
5. **Enable encryption** for DynamoDB table
6. **Regular security updates** for dependencies

## Next Steps

1. Set up monitoring and alerting
2. Implement error notifications (SNS)
3. Add data backup strategy
4. Consider multi-region deployment for disaster recovery
5. Implement data retention policies