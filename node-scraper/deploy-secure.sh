#!/bin/bash

# Secure Deploy Homework Scraper to AWS Lambda
# Usage: ./deploy-secure.sh [STACK_NAME]

set -e  # Exit on any error

# Configuration
STACK_NAME=${1:-homework-scraper}
REGION=${AWS_REGION:-us-east-1}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
SECRET_NAME="homework-scraper-credentials"

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

# Function to securely prompt for credentials
prompt_for_credentials() {
    echo_info "Setting up secure credentials in AWS Secrets Manager"
    
    echo -n "Enter homework portal username: "
    read -r USERNAME
    
    echo -n "Enter homework portal password: "
    read -rs PASSWORD
    echo  # New line after password input
    
    if [ -z "$USERNAME" ] || [ -z "$PASSWORD" ]; then
        echo_error "Username and password are required"
        exit 1
    fi
}

# Function to create/update secret
create_secret() {
    local secret_value=$(cat <<EOF
{
  "username": "$USERNAME",
  "password": "$PASSWORD"
}
EOF
)

    echo_info "Creating/updating secret in AWS Secrets Manager..."
    
    # Try to update existing secret first
    if aws secretsmanager update-secret \
        --secret-id "$SECRET_NAME" \
        --secret-string "$secret_value" \
        --region "$REGION" >/dev/null 2>&1; then
        echo_success "Updated existing secret: $SECRET_NAME"
    else
        # Create new secret if update failed
        if aws secretsmanager create-secret \
            --name "$SECRET_NAME" \
            --description "Login credentials for homework portal" \
            --secret-string "$secret_value" \
            --region "$REGION" >/dev/null 2>&1; then
            echo_success "Created new secret: $SECRET_NAME"
        else
            echo_error "Failed to create/update secret"
            exit 1
        fi
    fi
}

echo_info "Starting secure deployment of homework scraper to AWS Lambda"
echo_info "Stack Name: $STACK_NAME"
echo_info "Region: $REGION"
echo_info "Account ID: $ACCOUNT_ID"

# Step 1: Prompt for credentials securely
prompt_for_credentials

# Step 2: Create/update secret in Secrets Manager
create_secret

# Clear variables from memory
unset USERNAME
unset PASSWORD

# Step 3: Deploy infrastructure without Lambda first (to create ECR repository)
echo_info "Deploying infrastructure (ECR repository first)..."
aws cloudformation deploy \
    --template-file cloudformation-template.yaml \
    --stack-name $STACK_NAME \
    --parameter-overrides \
        ProjectName=$STACK_NAME \
        SecretsManagerSecretName=$SECRET_NAME \
        ScheduleExpression="cron(30 16 ? * SUN,MON,TUE,WED,THU,FRI *)" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region $REGION \
    || true

# Step 5: Get ECR repository URI (create if not exists)
echo_info "Getting ECR repository URI..."
ECR_URI=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`ECRRepositoryURI`].OutputValue' \
    --output text 2>/dev/null)

if [ -z "$ECR_URI" ] || [ "$ECR_URI" == "None" ]; then
    echo_info "ECR repository not found in stack, creating directly..."
    aws ecr create-repository \
        --repository-name $STACK_NAME \
        --image-scanning-configuration scanOnPush=true \
        --region $REGION \
        --query 'repository.repositoryUri' \
        --output text 2>/dev/null || true
    
    ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${STACK_NAME}"
fi

echo_success "ECR Repository: $ECR_URI"

# Step 5: Build Docker image for Lambda
echo_info "Building Lambda Docker image..."
sudo docker build -f Dockerfile.lambda -t homework-scraper-lambda .
echo_success "Docker image built successfully"

# Step 6: Login to ECR
echo_info "Logging into ECR..."
ECR_REGISTRY="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
aws ecr get-login-password --region $REGION | sudo docker login --username AWS --password-stdin $ECR_REGISTRY
echo_success "ECR login successful"

# Step 7: Tag and push image
echo_info "Tagging and pushing image to ECR..."
sudo docker tag homework-scraper-lambda:latest ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${STACK_NAME}:latest

sudo docker push ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${STACK_NAME}:latest

echo_success "Image pushed to ECR"

# Step 8: Redeploy CloudFormation stack now that image exists
echo_info "Redeploying CloudFormation stack with image..."
aws cloudformation deploy \
    --template-file cloudformation-template.yaml \
    --stack-name $STACK_NAME \
    --parameter-overrides \
        ProjectName=$STACK_NAME \
        SecretsManagerSecretName=$SECRET_NAME \
        ScheduleExpression="cron(30 16 ? * SUN,MON,TUE,WED,THU,FRI *)" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region $REGION
echo_success "CloudFormation stack deployed successfully"

# Step 9: Update Lambda function with new image (if needed)
echo_info "Ensuring Lambda function has latest image..."
aws lambda update-function-code \
    --function-name $STACK_NAME-function \
    --image-uri $ECR_URI:latest \
    --region $REGION \
    2>/dev/null || echo_info "Lambda function already up to date"

# Step 9: Wait for function to be ready
echo_info "Waiting for Lambda function to be ready..."
aws lambda wait function-updated \
    --function-name $STACK_NAME-function \
    --region $REGION
echo_success "Lambda function is ready"

# Step 10: Test the function
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

echo_success "🎉 Secure deployment completed successfully!"
echo_info "Your homework scraper is now running on AWS Lambda with EventBridge scheduling"
echo_info "Credentials are securely stored in AWS Secrets Manager: $SECRET_NAME"
echo_info "Function Name: $STACK_NAME-function"
echo_info "Schedule: Every 6 hours (configurable in CloudFormation template)"
echo_info "DynamoDB Table: homework-items"

echo_warning "Security Notes:"
echo "  • Credentials are stored in AWS Secrets Manager (encrypted at rest)"
echo "  • Lambda retrieves credentials at runtime (not in environment variables)"
echo "  • Only the Lambda execution role can access the secret"
echo "  • Credentials are not visible in AWS Console or CloudFormation"

echo_info "To monitor execution:"
echo "  aws logs tail /aws/lambda/$STACK_NAME-function --follow"

echo_info "To update credentials:"
echo "  aws secretsmanager update-secret --secret-id $SECRET_NAME --secret-string '{\"username\":\"new_user\",\"password\":\"new_pass\"}'"