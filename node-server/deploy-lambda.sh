#!/bin/bash
set -e

# ============================================
# Lambda Deployment Script for Node Server
# ============================================

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
STACK_NAME="${STACK_NAME:-homework-agent-server}"
ENVIRONMENT="${ENVIRONMENT:-prod}"
CLOUDFRONT_URL="${CLOUDFRONT_URL:-https://d11ppd1e1sqsv0.cloudfront.net}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
S3_BUCKET="homework-agent-lambda-deployments-${AWS_ACCOUNT_ID}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${YELLOW}🚀 Starting Lambda Deployment${NC}"
echo "================================================"
echo "Region: $AWS_REGION"
echo "Stack: $STACK_NAME"
echo "Environment: $ENVIRONMENT"
echo "CloudFront URL: $CLOUDFRONT_URL"
echo "================================================"

# Step 1: Install dependencies
echo -e "\n${YELLOW}📦 Step 1: Installing dependencies...${NC}"
npm ci

# Step 2: Build TypeScript
echo -e "\n${YELLOW}🔨 Step 2: Building TypeScript...${NC}"
npm run build

# Step 3: Prepare Lambda package
echo -e "\n${YELLOW}📁 Step 3: Preparing Lambda package...${NC}"
rm -rf dist-lambda
mkdir -p dist-lambda

# Copy compiled JS files
cp -r dist/* dist-lambda/

# Copy package.json and install production dependencies
cp package.json dist-lambda/
cp package-lock.json dist-lambda/ 2>/dev/null || true

cd dist-lambda
echo -e "${YELLOW}   Installing production dependencies...${NC}"
npm ci --omit=dev --ignore-scripts
cd ..

# Show package size
PACKAGE_SIZE=$(du -sh dist-lambda | cut -f1)
echo -e "${GREEN}   Package size: $PACKAGE_SIZE${NC}"

# Step 4: Create S3 bucket for deployment artifacts (if not exists)
echo -e "\n${YELLOW}🪣 Step 4: Creating deployment bucket...${NC}"
if aws s3 ls "s3://$S3_BUCKET" 2>/dev/null; then
    echo -e "${GREEN}   Bucket already exists${NC}"
else
    aws s3 mb s3://$S3_BUCKET --region $AWS_REGION
    echo -e "${GREEN}   Bucket created${NC}"
fi

# Step 5: Package the CloudFormation template
echo -e "\n${YELLOW}📦 Step 5: Packaging CloudFormation template...${NC}"
aws cloudformation package \
    --template-file cloudformation-lambda.yaml \
    --s3-bucket $S3_BUCKET \
    --output-template-file packaged.yaml \
    --region $AWS_REGION

# Step 6: Deploy the stack
echo -e "\n${YELLOW}☁️  Step 6: Deploying to AWS (this may take a few minutes)...${NC}"

ALLOWED_ORIGINS="${CLOUDFRONT_URL},http://localhost:5173,http://localhost:3000"

aws cloudformation deploy \
    --template-file packaged.yaml \
    --stack-name $STACK_NAME \
    --parameter-overrides \
        Environment=$ENVIRONMENT \
        AllowedOrigins="$ALLOWED_ORIGINS" \
    --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
    --region $AWS_REGION \
    --no-fail-on-empty-changeset

# Step 7: Get outputs
echo -e "\n${YELLOW}📋 Step 7: Getting deployment info...${NC}"
API_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text)

FUNCTION_NAME=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`FunctionName`].OutputValue' \
    --output text)

# Cleanup
rm -f packaged.yaml

# Done!
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Lambda Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}🌐 API URL:${NC}"
echo -e "${GREEN}   $API_URL${NC}"
echo ""
echo -e "${BLUE}📝 Lambda Function:${NC}"
echo -e "${GREEN}   $FUNCTION_NAME${NC}"
echo ""
echo -e "${YELLOW}🔗 Test the health endpoint:${NC}"
echo -e "   curl ${API_URL}health"
echo ""
echo -e "${YELLOW}📝 Next steps:${NC}"
echo -e "   1. Update client/.env.production with:"
echo -e "      ${GREEN}VITE_API_URL=$API_URL${NC}"
echo -e "   2. Redeploy client:"
echo -e "      ${GREEN}cd ../client && ./deploy-s3-cloudfront.sh${NC}"
echo ""
