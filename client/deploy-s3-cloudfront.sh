#!/bin/bash
set -e

# ============================================
# S3 + CloudFront Deployment Script for Client
# ============================================

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
STACK_NAME="${STACK_NAME:-homework-agent-client}"
ENVIRONMENT="${ENVIRONMENT:-prod}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Starting Client Deployment${NC}"
echo "================================================"
echo "Region: $AWS_REGION"
echo "Stack: $STACK_NAME"
echo "Environment: $ENVIRONMENT"
echo "================================================"

# Step 1: Check if CloudFormation stack exists, if not create it
echo -e "\n${YELLOW}📦 Step 1: Checking infrastructure...${NC}"
STACK_STATUS=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $AWS_REGION \
    --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "DOES_NOT_EXIST")

# Handle failed or rolled back stacks
if [[ "$STACK_STATUS" == "ROLLBACK_COMPLETE" || "$STACK_STATUS" == "DELETE_FAILED" || "$STACK_STATUS" == "CREATE_FAILED" ]]; then
    echo -e "${YELLOW}⚠️  Previous stack failed (Status: $STACK_STATUS). Deleting and recreating...${NC}"
    
    # Show error from failed stack
    echo -e "${YELLOW}Previous failure reason:${NC}"
    aws cloudformation describe-stack-events \
        --stack-name $STACK_NAME \
        --region $AWS_REGION \
        --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`].[LogicalResourceId,ResourceStatusReason]' \
        --output table 2>/dev/null || true
    
    # Delete the failed stack
    echo -e "${YELLOW}Deleting failed stack...${NC}"
    aws cloudformation delete-stack --stack-name $STACK_NAME --region $AWS_REGION
    aws cloudformation wait stack-delete-complete --stack-name $STACK_NAME --region $AWS_REGION
    echo -e "${GREEN}✅ Failed stack deleted${NC}"
    STACK_STATUS="DOES_NOT_EXIST"
fi

if [ "$STACK_STATUS" == "DOES_NOT_EXIST" ]; then
    echo -e "${YELLOW}Creating S3 + CloudFront infrastructure (this takes 5-10 minutes)...${NC}"
    aws cloudformation create-stack \
        --stack-name $STACK_NAME \
        --template-body file://cloudformation-s3-cloudfront.yaml \
        --parameters ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
        --region $AWS_REGION
    
    echo -e "${YELLOW}Waiting for stack creation to complete...${NC}"
    aws cloudformation wait stack-create-complete --stack-name $STACK_NAME --region $AWS_REGION
    echo -e "${GREEN}✅ Infrastructure created!${NC}"
else
    echo -e "${GREEN}✅ Infrastructure already exists (Status: $STACK_STATUS)${NC}"
fi

# Step 2: Get bucket name and distribution ID from CloudFormation outputs
echo -e "\n${YELLOW}📋 Step 2: Getting deployment targets...${NC}"
BUCKET_NAME=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`BucketName`].OutputValue' --output text)
DISTRIBUTION_ID=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' --output text)
WEBSITE_URL=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`WebsiteURL`].OutputValue' --output text)

echo "Bucket: $BUCKET_NAME"
echo "Distribution ID: $DISTRIBUTION_ID"
echo "Website URL: $WEBSITE_URL"

# Step 3: Build the application
echo -e "\n${YELLOW}🔨 Step 3: Building application...${NC}"
npm run build

# Step 4: Upload to S3
echo -e "\n${YELLOW}⬆️  Step 4: Uploading to S3...${NC}"
aws s3 sync dist/ s3://$BUCKET_NAME --delete --region $AWS_REGION

# Step 5: Invalidate CloudFront cache
echo -e "\n${YELLOW}🔄 Step 5: Invalidating CloudFront cache...${NC}"
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id $DISTRIBUTION_ID \
    --paths "/*" \
    --query 'Invalidation.Id' \
    --output text)
echo "Invalidation ID: $INVALIDATION_ID"

# Done!
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}🌐 Your app is live at:${NC}"
echo -e "${GREEN}   $WEBSITE_URL${NC}"
echo ""
echo -e "${YELLOW}Note: CloudFront cache invalidation may take 1-2 minutes${NC}"
echo ""
