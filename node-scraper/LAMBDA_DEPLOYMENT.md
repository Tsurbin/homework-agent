# Lambda Deployment Guide - Node.js Homework Scraper

This guide explains how to deploy the homework scraper as an AWS Lambda function in the **il-central-1** (Tel Aviv) region.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     AWS il-central-1 Region                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐         ┌────────────────────────────┐   │
│  │  EventBridge     │────────▶│  Lambda Function           │   │
│  │  Schedules       │         │  (homework-scraper)        │   │
│  │                  │         │                            │   │
│  │  Sun-Thu:        │         │  Uses:                     │   │
│  │  - 10:00 IST     │         │  - @sparticuz/chromium     │   │
│  │  - 13:00 IST     │         │  - Existing scraper code   │   │
│  │  - 16:00 IST     │         │                            │   │
│  │                  │         └─────────────┬──────────────┘   │
│  │  Friday:         │                       │                   │
│  │  - 12:00 IST     │                       ▼                   │
│  │  - 15:00 IST     │         ┌────────────────────────────┐   │
│  └──────────────────┘         │  Secrets Manager           │   │
│                               │  (HW_USERNAME, HW_PASSWORD)│   │
│                               └────────────────────────────┘   │
│                                             │                   │
│                                             ▼                   │
│                               ┌────────────────────────────┐   │
│                               │  DynamoDB Tables           │   │
│                               │  - homework-items          │   │
│                               │  - weekly-plan             │   │
│                               └────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Schedule Summary (Israel Time)

| Day | Times |
|-----|-------|
| Sunday | 10:00, 13:00, 16:00 |
| Monday | 10:00, 13:00, 16:00 |
| Tuesday | 10:00, 13:00, 16:00 |
| Wednesday | 10:00, 13:00, 16:00 |
| Thursday | 10:00, 13:00, 16:00 |
| Friday | 12:00, 15:00 |
| Saturday | - (no runs) |

## Prerequisites

1. **AWS CLI** installed and configured
   ```bash
   aws configure
   # Set default region to il-central-1
   ```

2. **AWS SAM CLI** installed
   ```bash
   pip install aws-sam-cli
   ```

3. **Node.js 20.x** or later

4. **Docker** (for SAM build with container)

## Deployment Steps

### 1. Store Credentials in Secrets Manager

First, create a secret with your school portal credentials:

```bash
aws secretsmanager create-secret \
    --name "homework-scraper/credentials" \
    --region "il-central-1" \
    --secret-string '{"HW_USERNAME":"your_username","HW_PASSWORD":"your_password"}'
```

### 2. Deploy Using the Script

```bash
# Make the script executable
chmod +x deploy.sh

# Deploy to il-central-1 (default)
./deploy.sh deploy

# Or specify options via environment variables
STACK_NAME=my-scraper AWS_REGION=il-central-1 ./deploy.sh deploy
```

### 3. Manual Deployment (Alternative)

If you prefer to deploy manually:

```bash
# Install dependencies
npm ci --production

# Build with SAM
sam build --use-container --region il-central-1

# Deploy
sam deploy \
    --stack-name homework-scraper \
    --region il-central-1 \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides \
        Environment=production \
        SecretsName=homework-scraper/credentials
```

## Testing

### Invoke the Lambda Manually

```bash
aws lambda invoke \
    --function-name homework-scraper \
    --region il-central-1 \
    --payload '{"source": "manual-test"}' \
    --cli-binary-format raw-in-base64-out \
    response.json

cat response.json
```

### Check Logs

```bash
aws logs tail /aws/lambda/homework-scraper --region il-central-1 --follow
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRETS_NAME` | Secrets Manager secret name | `homework-scraper/credentials` |
| `DYNAMODB_TABLE_NAME` | Homework items table | `homework-items` |
| `WEEKLY_PLAN_TABLE_NAME` | Weekly plan table | `weekly-plan` |
| `LOGIN_URL` | School portal login URL | `https://webtop.smartschool.co.il/account/login` |

### Adjusting the Schedule

The schedules are defined in `template.yaml`. To modify them, edit the `ScheduleExpression` values in the EventBridge rules.

**Cron format:** `cron(minutes hours day-of-month month day-of-week year)`

**Note:** AWS cron uses UTC time. Israel is UTC+2 (winter) or UTC+3 (summer).

Example conversions (summer time, UTC+3):
- 10:00 IST = 07:00 UTC → `cron(0 7 ? * 1,2,3,4,5 *)`
- 13:00 IST = 10:00 UTC → `cron(0 10 ? * 1,2,3,4,5 *)`
- 16:00 IST = 13:00 UTC → `cron(0 13 ? * 1,2,3,4,5 *)`

## Files Structure

```
node-scraper/
├── lambda.js              # Lambda handler (thin wrapper)
├── template.yaml          # SAM/CloudFormation template
├── deploy.sh              # Deployment script
├── package.json           # Dependencies
├── src/
│   ├── index.js           # Main scraper (reused by Lambda)
│   ├── config/
│   │   └── config.js      # Configuration
│   └── scraper/
│       ├── auth.js        # Auth (auto-detects Lambda env)
│       ├── homework.js    # Homework scraper
│       ├── weeklyPlan.js  # Weekly plan scraper
│       └── dynamodb.js    # DynamoDB handlers
```

## How It Works

1. **Lambda handler** (`lambda.js`) is a thin wrapper that:
   - Fetches credentials from Secrets Manager
   - Sets them as environment variables
   - Calls the existing `runAllScrapers()` function

2. **Auth module** (`src/scraper/auth.js`) automatically detects Lambda environment:
   - In Lambda: Uses `@sparticuz/chromium` for serverless Chromium
   - Locally: Uses regular Playwright

3. **No code duplication** - Lambda uses the exact same scraping logic as local development

## Troubleshooting

### Lambda Timeout
The default timeout is 5 minutes. If scraping takes longer, increase the `Timeout` value in `template.yaml`.

### Memory Issues
The default memory is 2GB. Chromium needs significant memory. Increase `MemorySize` if you see out-of-memory errors.

### Chromium Not Found
Ensure `@sparticuz/chromium` is in your dependencies and the Lambda function has enough memory.

### Credentials Error
Verify the secret exists and has the correct format:
```bash
aws secretsmanager get-secret-value \
    --secret-id homework-scraper/credentials \
    --region il-central-1
```

## Costs Estimate

- **Lambda**: ~$0.20/month (5 min × 17 runs/week × 4 weeks × 2GB)
- **DynamoDB**: ~$0 (PAY_PER_REQUEST, minimal reads/writes)
- **Secrets Manager**: ~$0.40/month (1 secret)
- **Total**: ~$1/month

## Cleanup

To delete all resources:

```bash
./deploy.sh delete

# Or manually:
aws cloudformation delete-stack --stack-name homework-scraper --region il-central-1
```

**Note:** This will delete the DynamoDB tables and all stored data!
