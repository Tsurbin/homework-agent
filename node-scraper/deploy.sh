#!/bin/bash

# Deploy Homework Scraper to AWS Lambda
# Usage: ./deploy.sh [STACK_NAME] [HW_USERNAME] [HW_PASSWORD]

set -e  # Exit on any error

# Configuration
STACK_NAME=${1:-homework-scraper}
HW_USERNAME=${2}
HW_PASSWORD=${3}
REGION=${AWS_REGION:-us-east-1}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

echo_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Validate inputs
if [ -z "$HW_USERNAME" ] || [ -z "$HW_PASSWORD" ]; then
    echo_error "Usage: $0 [STACK_NAME] <HW_USERNAME> <HW_PASSWORD>"
    echo "Example: $0 homework-scraper myusername mypassword"
    exit 1
fi

echo_info "Starting deployment of homework scraper to AWS Lambda"
echo_info "Stack Name: $STACK_NAME"
echo_info "Region: $REGION"
echo_info "Account ID: $ACCOUNT_ID"

# Step 1: Create/Update CloudFormation Stack (without Lambda function)
echo_info "Deploying CloudFormation infrastructure..."

# Deploy stack but Lambda will fail until image is pushed
aws cloudformation deploy \
    --template-file cloudformation-template.yaml \
    --stack-name $STACK_NAME \
    --parameter-overrides \
        ProjectName=$STACK_NAME \
        HWUsername=$HW_USERNAME \
        HWPassword=$HW_PASSWORD \
        ScheduleExpression="rate(6 hours)" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region $REGION \
    || echo_warning "Initial stack deployment may fail due to missing image - continuing..."

# Step 2: Get ECR repository URI
echo_info "Getting ECR repository URI..."
ECR_URI=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`ECRRepositoryURI`].OutputValue' \
    --output text)

if [ -z "$ECR_URI" ]; then
    echo_error "Failed to get ECR repository URI from CloudFormation stack"
    exit 1
fi

echo_success "ECR Repository: $ECR_URI"

# Step 3: Build Docker image for Lambda
echo_info "Building Lambda Docker image..."
docker build -f Dockerfile.lambda -t $STACK_NAME-lambda .
echo_success "Docker image built successfully"

# Step 4: Login to ECR
echo_info "Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_URI
echo_success "ECR login successful"

# Step 5: Tag and push image
echo_info "Tagging and pushing image to ECR..."
docker tag $STACK_NAME-lambda:latest $ECR_URI:latest
docker push $ECR_URI:latest
echo_success "Image pushed to ECR"

# Step 6: Update Lambda function with new image
echo_info "Updating Lambda function with new image..."
aws lambda update-function-code \
    --function-name $STACK_NAME-function \
    --image-uri $ECR_URI:latest \
    --region $REGION
echo_success "Lambda function updated"

# Step 7: Wait for function to be ready
echo_info "Waiting for Lambda function to be ready..."
aws lambda wait function-updated \
    --function-name $STACK_NAME-function \
    --region $REGION
echo_success "Lambda function is ready"

# Step 8: Test the function
echo_info "Testing Lambda function..."
aws lambda invoke \
    --function-name $STACK_NAME-function \
    --region $REGION \
    --payload '{"test": true}' \
    response.json

if [ -f response.json ]; then
    echo_info "Lambda response:"
    cat response.json | jq .
    rm response.json
fi

echo_success "🎉 Deployment completed successfully!"
echo_info "Your homework scraper is now running on AWS Lambda with EventBridge scheduling"
echo_info "Function Name: $STACK_NAME-function"
echo_info "Schedule: Every 6 hours (configurable in CloudFormation template)"
echo_info "DynamoDB Table: homework-items"

echo_info "To monitor execution:"
echo "  aws logs tail /aws/lambda/$STACK_NAME-function --follow"

echo_info "To update the schedule:"
echo "  Edit the ScheduleExpression parameter in the CloudFormation template and redeploy"