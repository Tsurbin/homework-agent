#!/bin/bash

# Optimized Lambda deployment script
set -e

STACK_NAME="homework-scraper-stack"
REGION="us-east-1"
FUNCTION_NAME="homework-scraper"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 Creating Optimized Lambda Package${NC}"

# Clean up previous attempts
rm -rf lambda-package/ homework-scraper-lambda-optimized.zip

mkdir -p lambda-package/

# Copy only essential code (no Playwright)
echo -e "${YELLOW}Copying essential code...${NC}"
cp lambda_function.py lambda-package/
cp -r scraper/ lambda-package/

# Install minimal dependencies with timeout
echo -e "${YELLOW}Installing minimal dependencies...${NC}"
timeout 300 pip install -r requirements-lambda-minimal.txt -t lambda-package/ --upgrade --quiet

# Remove unnecessary files to reduce size
echo -e "${YELLOW}Optimizing package size...${NC}"
cd lambda-package/

# Remove cache and test files safely
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.dist-info" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "tests" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "test" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true

# Remove large boto3 data files if they exist (but keep docs)
rm -rf botocore/data/ec2/ 2>/dev/null || true
rm -rf botocore/data/s3/ 2>/dev/null || true

# Create optimized zip
echo -e "${YELLOW}Creating optimized package...${NC}"
zip -r ../homework-scraper-lambda-optimized.zip . -q

cd ..

# Check package size
if [ -f homework-scraper-lambda-optimized.zip ]; then
    PACKAGE_SIZE=$(du -h homework-scraper-lambda-optimized.zip | cut -f1)
    echo -e "${GREEN}✅ Optimized package created: homework-scraper-lambda-optimized.zip (${PACKAGE_SIZE})${NC}"
else
    echo -e "${RED}❌ Failed to create package${NC}"
    exit 1
fi

# Deploy or update function
echo -e "${YELLOW}Deploying to Lambda...${NC}"

# Check if function exists
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION >/dev/null 2>&1; then
    echo -e "${YELLOW}Updating existing function...${NC}"
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://homework-scraper-lambda-optimized.zip \
        --region $REGION
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Lambda function updated successfully!${NC}"
    else
        echo -e "${RED}❌ Failed to update Lambda function${NC}"
        exit 1
    fi
else
    echo -e "${RED}Function doesn't exist. Please deploy CloudFormation stack first.${NC}"
    exit 1
fi

# Clean up
rm -rf lambda-package/

echo -e "${GREEN}🎉 Deployment completed!${NC}"