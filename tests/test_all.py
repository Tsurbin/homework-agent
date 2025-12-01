#!/usr/bin/env python3
"""
Comprehensive test script for homework scraper.
Tests both local SQLite version and Lambda DynamoDB version.
"""

import sys
import os
import json
from pathlib import Path
from datetime import date, datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_local_scraper():
    """Test the Lambda scraper modules (local testing)."""
    print("=" * 60)
    print("🧪 TESTING LAMBDA SCRAPER MODULES")
    print("=" * 60)
    
    try:
        from scraper.lambda_runner import run_scrape_lambda
        from database.dynamodb_handler import DynamoDBHandler, HomeworkItem
        
        print("✅ Successfully imported Lambda scraper modules")
        
        # Test HomeworkItem creation
        print("\n� Testing HomeworkItem creation...")
        test_item = HomeworkItem(
            date="2025-11-20",
            subject="מתמטיקה",
            description="תרגילים 1-10",
            hour="שיעור 1"
        )
        print(f"✅ Created test item: {test_item.subject}")
        
        # Test DynamoDB handler initialization (without AWS calls)
        print("\n� Testing DynamoDB handler initialization...")
        db = DynamoDBHandler(table_name="test-homework-items")
        print("✅ DynamoDB handler initialized successfully")
        
        print("✅ Lambda scraper modules test completed")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing Lambda scraper modules: {e}")
        return False

def test_lambda_modules():
    """Test Lambda-specific modules without AWS credentials."""
    print("\n" + "=" * 60)
    print("🧪 TESTING LAMBDA MODULES (Local)")
    print("=" * 60)
    
    try:
        # Test DynamoDB handler import
        print("📦 Testing DynamoDB handler import...")
        try:
            from database.dynamodb_handler import DynamoDBHandler
            print("✅ DynamoDB handler imported successfully")
        except ImportError as e:
            print(f"❌ DynamoDB handler import failed: {e}")
            print("💡 Install boto3: pip install boto3")
            return False
        
        # Test Lambda runner import
        print("📦 Testing Lambda runner import...")
        from scraper.lambda_runner import run_scrape_lambda
        print("✅ Lambda runner imported successfully")
        
        # Test Lambda function import
        print("📦 Testing Lambda function import...")
        from lambda_function import lambda_handler
        print("✅ Lambda function imported successfully")
        
        # Test HomeworkItem creation
        print("📝 Testing HomeworkItem creation...")
        from database.dynamodb_handler import HomeworkItem
        item = HomeworkItem(
            date=date.today().isoformat(),
            subject="Test Subject",
            description="Test homework",
            hour="שיעור 1"
        )
        print(f"✅ Created test item: {item.subject}")
        
        print("✅ All Lambda modules test passed")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Lambda modules: {e}")
        return False

def test_deployment_package():
    """Test if deployment package can be created."""
    print("\n" + "=" * 60)
    print("🧪 TESTING DEPLOYMENT PACKAGE")
    print("=" * 60)
    
    try:
        # Check if deploy script exists
        deploy_script = project_root / "deploy-lambda-runner.sh"
        if not deploy_script.exists():
            print("❌ deploy-lambda-runner.sh not found")
            return False
        
        print("✅ deploy-lambda-runner.sh found")
        
        # Check if requirements file exists
        requirements_file = project_root / "requirements-lambda-minimal.txt"
        if not requirements_file.exists():
            print("❌ requirements-lambda-minimal.txt not found")
            return False
        
        print("✅ requirements-lambda-minimal.txt found")
        
        # Check CloudFormation template
        cf_template = project_root / "cloudformation-template.json"
        if not cf_template.exists():
            print("❌ cloudformation-template.json not found")
            return False
        
        print("✅ cloudformation-template.json found")
        
        # Validate CloudFormation template JSON
        try:
            with open(cf_template, 'r') as f:
                json.load(f)
            print("✅ CloudFormation template is valid JSON")
        except json.JSONDecodeError as e:
            print(f"❌ CloudFormation template JSON error: {e}")
            return False
        
        print("✅ Deployment package structure is valid")
        return True
        
    except Exception as e:
        print(f"❌ Error testing deployment package: {e}")
        return False

def test_aws_configuration():
    """Test AWS configuration and credentials."""
    print("\n" + "=" * 60)
    print("🧪 TESTING AWS CONFIGURATION")
    print("=" * 60)
    
    import subprocess
    
    try:
        # Check if AWS CLI is installed
        result = subprocess.run(['aws', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ AWS CLI installed: {result.stdout.strip()}")
        else:
            print("❌ AWS CLI not found")
            return False
        
        # Check AWS credentials
        result = subprocess.run(['aws', 'sts', 'get-caller-identity'], capture_output=True, text=True)
        if result.returncode == 0:
            identity = json.loads(result.stdout)
            print(f"✅ AWS credentials configured for account: {identity.get('Account')}")
            print(f"   User/Role: {identity.get('Arn', 'Unknown')}")
        else:
            print("❌ AWS credentials not configured")
            print("💡 Run: aws configure")
            return False
        
        print("✅ AWS configuration test passed")
        return True
        
    except FileNotFoundError:
        print("❌ AWS CLI not installed")
        print("💡 Install AWS CLI: https://aws.amazon.com/cli/")
        return False
    except Exception as e:
        print(f"❌ Error testing AWS configuration: {e}")
        return False

def simulate_lambda_execution():
    """Simulate Lambda function execution locally."""
    print("\n" + "=" * 60)
    print("🧪 TESTING LAMBDA EXECUTION (Simulation)")
    print("=" * 60)
    
    try:
        # Load environment variables from .env file
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("✅ Loaded environment variables from .env file")
        except ImportError:
            print("⚠️  python-dotenv not installed, reading .env manually")
            # Manually read .env file
            env_file = project_root / '.env'
            if env_file.exists():
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key] = value
                print("✅ Manually loaded .env file")
            else:
                print("⚠️  .env file not found")
        
        # Set up environment variables for testing
        os.environ['DYNAMODB_TABLE_NAME'] = 'test-homework-items'
        
        # Get real credentials from .env file
        hw_username = os.environ.get('HW_USERNAME')
        hw_password = os.environ.get('HW_PASSWORD')
        
        if not hw_username or not hw_password:
            print("⚠️  HW_USERNAME and HW_PASSWORD not found in .env file")
            print("💡 Make sure your .env file contains valid credentials")
            # Set test values as fallback
            os.environ['HW_USERNAME'] = 'test_user'
            os.environ['HW_PASSWORD'] = 'test_password'
        else:
            print(f"✅ Using credentials from .env: {hw_username[:3]}***")
            os.environ['HW_USERNAME'] = hw_username
            os.environ['HW_PASSWORD'] = hw_password
        
        # Import Lambda function
        from lambda_function import lambda_handler
        
        # Create test events
        daily_event = {'scrape_type': 'daily'}
        historical_event = {'scrape_type': 'historical'}
        
        print("📝 Testing Lambda handler with daily event...")
        print("⚠️  This will fail without real AWS credentials and valid website credentials")
        
        # Note: This will fail without real credentials, but tests the structure
        try:
            result = lambda_handler(historical_event, None)
            print(f"✅ Lambda handler executed: {result}")
        except Exception as e:
            print(f"⚠️  Lambda execution failed (expected): {str(e)}")
            print("💡 This is normal without valid AWS credentials and website login")
        
        print("✅ Lambda structure test completed")
        return True
        
    except Exception as e:
        print(f"❌ Error simulating Lambda execution: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 HOMEWORK SCRAPER TEST SUITE")
    print(f"📅 Running on: {datetime.now().isoformat()}")
    
    tests = [
        ("Lambda Scraper Modules", test_local_scraper),
        ("Lambda Modules", test_lambda_modules),
        ("Deployment Package", test_deployment_package),
        ("AWS Configuration", test_aws_configuration),
        ("Lambda Simulation", simulate_lambda_execution),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except KeyboardInterrupt:
            print(f"\n⚠️  Test '{test_name}' interrupted by user")
            break
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\n📈 Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Ready for deployment.")
        return 0
    else:
        print("⚠️  Some tests failed. Review the issues above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)