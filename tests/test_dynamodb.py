#!/usr/bin/env python3
"""
Test script for DynamoDB connections and operations.
This script helps validate the DynamoDB handler before deploying to Lambda.
"""

import os
import sys
import json
from datetime import date, datetime, timezone
from dataclasses import dataclass

# Add the scraper module to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Test with local DynamoDB (using localstack or DynamoDB local)
# or configure AWS credentials for testing with real DynamoDB
os.environ['AWS_REGION'] = 'us-east-1'
# os.environ['AWS_ENDPOINT_URL'] = 'http://localhost:8000'  # Uncomment for DynamoDB Local

try:
    from scraper.dynamodb_handler import DynamoDBHandler, HomeworkItem
    import boto3
    print("✅ Successfully imported DynamoDB modules")
except ImportError as e:
    print(f"❌ Failed to import modules: {e}")
    print("Make sure to install requirements: pip install boto3")
    sys.exit(1)

def test_dynamodb_connection():
    """Test basic DynamoDB connection."""
    print("\n🔧 Testing DynamoDB connection...")
    
    try:
        # Test with a temporary table name
        table_name = "test-homework-items"
        db = DynamoDBHandler(table_name=table_name)
        
        # Try to create table
        created = db.create_table_if_not_exists()
        if created:
            print(f"✅ Created test table: {table_name}")
        else:
            print(f"ℹ️  Table {table_name} already exists")
        
        return db
        
    except Exception as e:
        print(f"❌ DynamoDB connection failed: {e}")
        print("Make sure AWS credentials are configured: aws configure")
        return None

def test_crud_operations(db: DynamoDBHandler):
    """Test CRUD operations on DynamoDB."""
    print("\n📝 Testing CRUD operations...")
    
    # Create test homework items
    test_items = [
        HomeworkItem(
            date=date.today().isoformat(),
            subject="Mathematics",
            description="Solve exercises 1-10",
            hour="שיעור 1",
            homework_text="Pages 45-50 in textbook"
        ),
        HomeworkItem(
            date=date.today().isoformat(),
            subject="English",
            description="Read chapter 3",
            hour="שיעור 2",
            homework_text="Answer questions at the end"
        ),
        HomeworkItem(
            date=date.today().isoformat(),
            subject="History",
            description="Research project",
            hour="שיעור 3",
            due_date=(date.today()).isoformat(),
            homework_text="Write 2 pages about WWI"
        )
    ]
    
    try:
        # Test insert
        print("📥 Testing insert operations...")
        inserted_count = db.upsert_items(test_items)
        print(f"✅ Inserted {inserted_count} items")
        
        # Test query by date
        print("🔍 Testing query by date...")
        today_items = db.get_items_by_date(date.today().isoformat())
        print(f"✅ Retrieved {len(today_items)} items for today")
        
        for item in today_items:
            print(f"   - {item['subject']}: {item['description']}")
        
        # Test update (upsert with changed content)
        print("🔄 Testing update operations...")
        updated_item = test_items[0]
        updated_item.homework_text = "Updated homework text"
        update_count = db.upsert_items([updated_item])
        print(f"✅ Updated {update_count} items")
        
        # Test scan all items
        print("📊 Testing scan all items...")
        all_items = db.get_all_items(limit=10)
        print(f"✅ Retrieved {len(all_items)} total items (limited to 10)")
        
        return True
        
    except Exception as e:
        print(f"❌ CRUD operations failed: {e}")
        return False

def test_performance(db: DynamoDBHandler):
    """Test performance with larger datasets."""
    print("\n⚡ Testing performance...")
    
    try:
        import time
        
        # Generate test data
        test_data = []
        for i in range(50):
            test_data.append(
                HomeworkItem(
                    date=f"2024-01-{(i % 30) + 1:02d}",
                    subject=f"Subject {i % 5}",
                    description=f"Test homework {i}",
                    hour=f"שיעור {(i % 6) + 1}",
                    homework_text=f"Test content for item {i}"
                )
            )
        
        # Test bulk insert
        start_time = time.time()
        inserted_count = db.upsert_items(test_data)
        end_time = time.time()
        
        print(f"✅ Bulk insert: {inserted_count} items in {end_time - start_time:.2f} seconds")
        
        # Test query performance
        start_time = time.time()
        items = db.get_items_by_date("2024-01-15")
        end_time = time.time()
        
        print(f"✅ Query performance: Retrieved {len(items)} items in {end_time - start_time:.3f} seconds")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

def cleanup_test_data(db: DynamoDBHandler):
    """Clean up test data."""
    print("\n🧹 Cleaning up test data...")
    
    try:
        # Get all items from test table
        all_items = db.get_all_items()
        
        # Delete items one by one (for demonstration)
        # In production, you might want to delete the entire table
        deleted_count = 0
        for item in all_items:
            if db.delete_item(
                date=item['date'],
                hour=item.get('hour'),
                subject=item['subject']
            ):
                deleted_count += 1
        
        print(f"✅ Deleted {deleted_count} test items")
        
        # Optionally delete the test table
        if input("Delete test table? (y/N): ").lower() == 'y':
            db.dynamodb.Table(db.table_name).delete()
            print("✅ Test table deleted")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")

def main():
    """Run all tests."""
    print("🧪 DynamoDB Handler Test Suite")
    print("=" * 40)
    
    # Test connection
    db = test_dynamodb_connection()
    if not db:
        return False
    
    # Test CRUD operations
    if not test_crud_operations(db):
        return False
    
    # Test performance
    if not test_performance(db):
        return False
    
    # Cleanup
    cleanup_test_data(db)
    
    print("\n🎉 All tests completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)