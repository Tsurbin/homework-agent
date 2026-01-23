#!/bin/bash

# ============================================
# Homework Scraper Lambda Deployment Script
# Deploys to AWS il-central-1 region
# ============================================

set -e  # Exit on error

# Configuration
STACK_NAME="${STACK_NAME:-homework-scraper}"
REGION="${AWS_REGION:-il-central-1}"
S3_BUCKET="${S3_BUCKET:-}"  # Will be created if not provided
ENVIRONMENT="${ENVIRONMENT:-production}"
SECRETS_NAME="${SECRETS_NAME:-homework-scraper-credentials}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check required tools
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    if ! command -v sam &> /dev/null; then
        log_error "AWS SAM CLI is not installed. Please install it first."
        echo "  Install with: pip install aws-sam-cli"
        exit 1
    fi
    
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured or invalid."
        exit 1
    fi
    
    log_success "All prerequisites met"
}

# Create S3 bucket for SAM artifacts if needed
create_s3_bucket() {
    if [ -z "$S3_BUCKET" ]; then
        ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        S3_BUCKET="sam-artifacts-${ACCOUNT_ID}-${REGION}"
    fi
    
    log_info "Checking S3 bucket: $S3_BUCKET"
    
    if ! aws s3api head-bucket --bucket "$S3_BUCKET" --region "$REGION" 2>/dev/null; then
        log_info "Creating S3 bucket: $S3_BUCKET"
        
        if [ "$REGION" == "us-east-1" ]; then
            aws s3api create-bucket --bucket "$S3_BUCKET" --region "$REGION"
        else
            aws s3api create-bucket --bucket "$S3_BUCKET" --region "$REGION" \
                --create-bucket-configuration LocationConstraint="$REGION"
        fi
        
        log_success "S3 bucket created"
    else
        log_success "S3 bucket already exists"
    fi
}

# Create secrets in AWS Secrets Manager
create_secrets() {
    log_info "Checking Secrets Manager secret: $SECRETS_NAME"
    
    if aws secretsmanager describe-secret --secret-id "$SECRETS_NAME" --region "us-east-1" &> /dev/null; then
        log_success "Secret already exists"
        return
    fi
    
    log_warning "Secret not found. Please create it manually with the following command:"
    echo ""
    echo "  aws secretsmanager create-secret \\"
    echo "    --name \"$SECRETS_NAME\" \\"
    echo "    --region \"us-east-1\" \\"
    echo "    --secret-string '{\"HW_USERNAME\":\"your_username\",\"HW_PASSWORD\":\"your_password\"}'"
    echo ""
    
    read -p "Have you created the secret? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_error "Please create the secret before deploying."
        exit 1
    fi
}

# Install dependencies
install_dependencies() {
    log_info "Installing dependencies..."
    npm ci --production
    log_success "Dependencies installed"
}

# Build the SAM application
build_application() {
    log_info "Building SAM application..."
    sam build --region "$REGION"
    log_success "Build complete"
}

# Deploy the application
deploy_application() {
    log_info "Deploying to $REGION..."
    
    sam deploy \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --s3-bucket "$S3_BUCKET" \
        --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
        --parameter-overrides \
            "Environment=$ENVIRONMENT" \
            "SecretsName=$SECRETS_NAME" \
        --no-confirm-changeset \
        --no-fail-on-empty-changeset
    
    log_success "Deployment complete!"
}

# Show deployment info
show_deployment_info() {
    echo ""
    log_info "Deployment Information:"
    echo "=================================="
    echo "  Stack Name:     $STACK_NAME"
    echo "  Region:         $REGION"
    echo "  Environment:    $ENVIRONMENT"
    echo ""
    
    # Get Lambda function ARN
    FUNCTION_ARN=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query "Stacks[0].Outputs[?OutputKey=='ScraperFunctionArn'].OutputValue" \
        --output text 2>/dev/null || echo "N/A")
    
    echo "  Lambda ARN:     $FUNCTION_ARN"
    echo ""
    echo "  Schedule (Israel Time):"
    echo "    Sun-Thu: 10:00, 13:00, 16:00"
    echo "    Friday:  12:00, 15:00"
    echo "=================================="
}

# Invoke function manually for testing
invoke_function() {
    log_info "Invoking Lambda function for testing..."
    
    aws lambda invoke \
        --function-name homework-scraper \
        --region "$REGION" \
        --payload '{"source": "manual-test"}' \
        --cli-binary-format raw-in-base64-out \
        response.json
    
    log_info "Response:"
    cat response.json
    rm -f response.json
}

# Delete the stack
delete_stack() {
    log_warning "This will delete the entire stack and all resources!"
    read -p "Are you sure? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Deleting stack..."
        aws cloudformation delete-stack --stack-name "$STACK_NAME" --region "$REGION"
        log_info "Waiting for deletion..."
        aws cloudformation wait stack-delete-complete --stack-name "$STACK_NAME" --region "$REGION"
        log_success "Stack deleted"
    fi
}

# Show usage
show_usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  deploy    - Full deployment (default)"
    echo "  build     - Build only"
    echo "  invoke    - Invoke function for testing"
    echo "  delete    - Delete the stack"
    echo "  info      - Show deployment info"
    echo ""
    echo "Environment Variables:"
    echo "  STACK_NAME    - CloudFormation stack name (default: homework-scraper)"
    echo "  AWS_REGION    - AWS region (default: il-central-1)"
    echo "  S3_BUCKET     - S3 bucket for artifacts (auto-created if not set)"
    echo "  ENVIRONMENT   - Environment name (default: production)"
    echo "  SECRETS_NAME  - Secrets Manager secret name (default: homework-scraper/credentials)"
}

# Main script
main() {
    COMMAND="${1:-deploy}"
    
    case "$COMMAND" in
        deploy)
            check_prerequisites
            create_s3_bucket
            create_secrets
            install_dependencies
            build_application
            deploy_application
            show_deployment_info
            ;;
        build)
            check_prerequisites
            install_dependencies
            build_application
            ;;
        invoke)
            invoke_function
            ;;
        delete)
            delete_stack
            ;;
        info)
            show_deployment_info
            ;;
        *)
            show_usage
            exit 1
            ;;
    esac
}

main "$@"
