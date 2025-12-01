# AWS Lambda Deployment Guide

## Prerequisites

1. **AWS CLI configured** with appropriate permissions
2. **Docker** installed and working
3. **jq** installed for JSON processing (optional)

```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS CLI
aws configure

# Install jq (Ubuntu/Debian)
sudo apt-get install jq
```

## Required AWS Permissions

Your AWS user/role needs these permissions:
- CloudFormation (create/update stacks)
- ECR (create repository, push images)
- Lambda (create/update functions)
- DynamoDB (create/manage tables)
- EventBridge (create rules)
- IAM (create roles for Lambda)

## Quick Deployment

### 🔒 **SECURE METHOD (Recommended)**

```bash
# Secure deployment with AWS Secrets Manager
./deploy-secure.sh homework-scraper

# The script will prompt you securely for credentials:
# Enter homework portal username: your_username
# Enter homework portal password: [hidden input]
```

**What it does automatically:**
1. ✅ Prompts for credentials securely (password hidden)
2. ✅ Creates/updates AWS Secrets Manager secret
3. ✅ Deploys infrastructure with proper IAM permissions
4. ✅ Builds and pushes Docker image
5. ✅ Updates Lambda function

### ⚠️ **LEGACY METHOD (Not Recommended)**

```bash
# Old method - credentials exposed in command line
./deploy.sh homework-scraper YOUR_USERNAME YOUR_PASSWORD
```

### 1. Build and Test Lambda Image

```bash
# Build Lambda-compatible image
npm run build:lambda

# Test locally (optional)
docker run --rm -p 8080:8080 homework-scraper-lambda:latest
```

### 2. Deploy to AWS

```bash
# 🔒 SECURE: Use this method
./deploy-secure.sh homework-scraper

# ⚠️  INSECURE: Avoid this method
# ./deploy.sh homework-scraper YOUR_USERNAME YOUR_PASSWORD
```

### 3. Monitor Execution

```bash
# View logs
aws logs tail /aws/lambda/homework-scraper-function --follow

# Check DynamoDB data
aws dynamodb scan --table-name homework-items --limit 5
```

## Schedule Configuration

The default schedule is **every 6 hours**. To change it:

1. Edit `cloudformation-template.yaml`
2. Update the `ScheduleExpression` parameter:
   - `rate(2 hours)` - Every 2 hours
   - `cron(0 8 * * ? *)` - Daily at 8 AM UTC
   - `cron(0 18 ? * MON-FRI *)` - Weekdays at 6 PM UTC

3. Redeploy:
```bash
./deploy.sh homework-scraper YOUR_USERNAME YOUR_PASSWORD
```

## Manual Testing

```bash
# Invoke function manually
aws lambda invoke \
    --function-name homework-scraper-function \
    --payload '{"test": true}' \
    output.json

# View results
cat output.json | jq .
```

## Cost Optimization

- **Memory**: Currently set to 2048 MB (adjust in CloudFormation)
- **Timeout**: 15 minutes max (adjust based on scraping time)
- **Schedule**: Consider your actual homework posting schedule
- **DynamoDB**: Uses pay-per-request (scales automatically)

## Troubleshooting

### Common Issues

1. **Image not found**: Wait 1-2 minutes after pushing to ECR
2. **Timeout errors**: Increase Lambda timeout in CloudFormation
3. **Memory errors**: Increase memory allocation
4. **Access denied**: Check IAM permissions

### Debugging

```bash
# View detailed logs
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/homework-scraper

# Check CloudFormation events
aws cloudformation describe-stack-events --stack-name homework-scraper

# Validate Lambda configuration
aws lambda get-function --function-name homework-scraper-function
```

## Clean Up

```bash
# Delete the entire stack
aws cloudformation delete-stack --stack-name homework-scraper

# Delete ECR images (optional)
aws ecr batch-delete-image \
    --repository-name homework-scraper \
    --image-ids imageTag=latest
```

## Security Notes

- Credentials are stored as CloudFormation parameters (consider AWS Secrets Manager for production)
- Lambda runs with minimal required permissions
- DynamoDB table has point-in-time recovery enabled
- ECR repository scans images for vulnerabilities