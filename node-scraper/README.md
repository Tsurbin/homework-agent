# Homework Agent - Node.js Scraper

A Playwright-based web scraper that automatically extracts homework assignments and weekly plans from educational platforms. This scraper can run locally or be deployed as an AWS Lambda function for scheduled execution.

## 🎯 Purpose

This scraper:
- Logs into school portal websites using Playwright
- Extracts homework assignments with due dates
- Retrieves weekly class schedules and plans
- Stores data in DynamoDB for access by other services
- Supports both local execution and serverless Lambda deployment

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Local Execution          OR        Lambda Execution     │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────┐         ┌──────────────────────┐  │
│  │  npm start       │         │  EventBridge         │  │
│  │                  │         │  (Scheduled)         │  │
│  └────────┬─────────┘         └──────────┬───────────┘  │
│           │                               │              │
│           ▼                               ▼              │
│  ┌─────────────────────────────────────────────────┐    │
│  │          Playwright Scraper                     │    │
│  │  - Chromium (local) or @sparticuz/chromium      │    │
│  │  - Login to school portal                       │    │
│  │  - Extract homework & weekly plans              │    │
│  └────────────────────┬────────────────────────────┘    │
│                       │                                  │
│                       ▼                                  │
│           ┌───────────────────────┐                      │
│           │  DynamoDB Tables      │                      │
│           │  - homework-items     │                      │
│           │  - weekly-plan        │                      │
│           └───────────────────────┘                      │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## 📋 Features

- **Automated Login**: Handles authentication with username/password
- **Homework Extraction**: Scrapes homework assignments with:
  - Subject/course name
  - Assignment description
  - Due dates
  - Additional metadata
- **Weekly Plan Extraction**: Retrieves class schedules
- **DynamoDB Storage**: Stores data with efficient querying
- **Lambda Support**: Deploy for serverless scheduled execution
- **Environment Detection**: Automatically uses appropriate Chromium version (local vs Lambda)
- **Error Handling**: Comprehensive error logging and recovery
- **Configurable**: Supports multiple school platforms via configuration

## 🚀 Quick Start

### Prerequisites

- Node.js 20.x or later
- npm or yarn
- AWS credentials (for DynamoDB and Lambda deployment)
- School portal credentials

### Installation

```bash
cd node-scraper
npm install
```

### Configuration

Create a `.env` file in the `node-scraper` directory:

```bash
# School Credentials (stored in AWS Secrets Manager for Lambda)
HW_USERNAME=your_school_username
HW_PASSWORD=your_school_password

# School Portal URLs
LOGIN_URL=https://webtop.smartschool.co.il/account/login
HW_BASE_URL=https://your-school-portal.com

# AWS Configuration
AWS_REGION=il-central-1

# DynamoDB Tables
DYNAMODB_TABLE_NAME=homework-items
WEEKLY_PLAN_TABLE_NAME=weekly-plan

# Scraper Settings (optional)
HEADLESS=true
SCRAPE_MODE=daily  # or 'historical' for full scrape
```

### Running Locally

#### Daily Scrape (Recent Data)
```bash
npm start
# or
node src/index.js
```

#### Historical Scrape (All Available Data)
```bash
npm run start:historical
# or
SCRAPE_MODE=historical node src/index.js
```

#### Test Lambda Handler Locally
```bash
npm run test:lambda
# or
node test-lambda-local.js
```

## 📦 Lambda Deployment

The scraper can be deployed to AWS Lambda for automatic scheduled execution. See [LAMBDA_DEPLOYMENT.md](./LAMBDA_DEPLOYMENT.md) for comprehensive deployment instructions.

### Quick Deploy

```bash
# Deploy using SAM
./deploy.sh deploy

# Or manually
sam build --use-container --region il-central-1
sam deploy --stack-name homework-scraper --region il-central-1 --capabilities CAPABILITY_IAM
```

### Scheduling

By default, the scraper runs on this schedule (Israel Time):
- **Sunday-Thursday**: 10:00, 13:00, 16:00
- **Friday**: 12:00, 15:00
- **Saturday**: No runs

Schedule is configured in `template.yaml` using EventBridge rules.

## 📂 Project Structure

```
node-scraper/
├── src/
│   ├── index.js              # Main entry point
│   ├── config/
│   │   └── config.js         # Configuration management
│   └── scraper/
│       ├── auth.js           # Authentication & browser setup
│       ├── homework.js       # Homework scraping logic
│       ├── weeklyPlan.js     # Weekly plan scraping logic
│       └── dynamodb.js       # DynamoDB operations
├── lambda.js                 # Lambda handler wrapper
├── test-lambda-local.js      # Local Lambda testing
├── template.yaml             # SAM/CloudFormation template
├── deploy.sh                 # Deployment script
├── package.json
├── LAMBDA_DEPLOYMENT.md      # Detailed Lambda deployment guide
└── README.md
```

## 🔧 How It Works

### 1. Authentication (`src/scraper/auth.js`)
- Detects execution environment (local vs Lambda)
- Launches appropriate Chromium version:
  - **Local**: Standard Playwright Chromium
  - **Lambda**: `@sparticuz/chromium` (optimized for Lambda)
- Navigates to login page
- Fills credentials and submits form
- Handles multi-step authentication if needed
- Returns authenticated browser context

### 2. Homework Scraping (`src/scraper/homework.js`)
- Navigates to homework section
- Extracts assignments with selectors
- Parses dates, subjects, descriptions
- Filters by date range (daily or historical)
- Returns structured homework data

### 3. Weekly Plan Scraping (`src/scraper/weeklyPlan.js`)
- Navigates to schedule/timetable section
- Extracts class schedule
- Parses times, subjects, teachers
- Returns weekly plan structure

### 4. Data Storage (`src/scraper/dynamodb.js`)
- Connects to DynamoDB tables
- Stores homework items with unique IDs
- Stores weekly plans
- Handles updates and deduplication
- Supports batch operations

### 5. Main Orchestration (`src/index.js`)
- Loads configuration
- Runs authentication
- Executes scrapers in sequence
- Stores results in DynamoDB
- Handles errors and cleanup
- Closes browser

### 6. Lambda Handler (`lambda.js`)
- Thin wrapper for Lambda execution
- Fetches credentials from Secrets Manager
- Sets environment variables
- Calls `runAllScrapers()` from `src/index.js`
- Returns success/error response

## 🔐 Security

### Local Execution
- Credentials in `.env` file (not committed to git)
- Environment variables for configuration

### Lambda Execution
- Credentials stored in **AWS Secrets Manager**
- IAM role with minimal permissions
- No hardcoded secrets in code

### Required AWS Permissions
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/homework-items",
        "arn:aws:dynamodb:*:*:table/weekly-plan"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:homework-scraper/credentials-*"
    }
  ]
}
```

## 🧪 Testing

### Test Authentication Only
```javascript
const { setupBrowser } = require('./src/scraper/auth');

(async () => {
  const { browser, context, page } = await setupBrowser();
  console.log('Authentication successful!');
  await browser.close();
})();
```

### Test Homework Scraper Only
```javascript
const { runAllScrapers } = require('./src/index');

(async () => {
  await runAllScrapers({ skipWeeklyPlan: true });
})();
```

### Test Lambda Locally
```bash
npm run test:lambda
```

This runs the Lambda handler locally with sample event data.

## 📊 Data Schema

### Homework Item (DynamoDB)
```json
{
  "id": "hw-2026-02-10-math-123",
  "subject": "Mathematics",
  "title": "Chapter 5 Exercises",
  "description": "Complete exercises 1-10 on page 45",
  "dueDate": "2026-02-12",
  "assignedDate": "2026-02-10",
  "status": "pending",
  "timestamp": "2026-02-10T09:00:00Z"
}
```

### Weekly Plan Item (DynamoDB)
```json
{
  "id": "plan-2026-w07",
  "week": "2026-W07",
  "startDate": "2026-02-10",
  "endDate": "2026-02-14",
  "schedule": [
    {
      "day": "Monday",
      "time": "08:00-09:00",
      "subject": "Mathematics",
      "teacher": "Mr. Smith",
      "room": "101"
    }
  ],
  "timestamp": "2026-02-10T09:00:00Z"
}
```

## ⚙️ Configuration Options

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `HW_USERNAME` | School portal username | - | Yes |
| `HW_PASSWORD` | School portal password | - | Yes |
| `LOGIN_URL` | School login page URL | - | Yes |
| `HW_BASE_URL` | School portal base URL | - | Yes |
| `AWS_REGION` | AWS region for DynamoDB | `us-east-1` | No |
| `DYNAMODB_TABLE_NAME` | Homework items table | `homework-items` | No |
| `WEEKLY_PLAN_TABLE_NAME` | Weekly plan table | `weekly-plan` | No |
| `HEADLESS` | Run browser in headless mode | `true` | No |
| `SCRAPE_MODE` | Scrape mode: `daily` or `historical` | `daily` | No |
| `SECRETS_NAME` | Secrets Manager secret name (Lambda) | - | For Lambda |

### Scrape Modes

- **daily**: Scrapes only recent/current homework (faster)
- **historical**: Scrapes all available historical data (slower, useful for initial setup)

## 🆘 Troubleshooting

### Common Issues

**Playwright Browser Not Found**
```bash
npx playwright install chromium
```

**Authentication Fails**
- Verify credentials in `.env`
- Check if login URL has changed
- Look for CAPTCHA or two-factor authentication

**Lambda Timeout**
- Default timeout is 5 minutes in `template.yaml`
- Increase `Timeout` value if scraping takes longer
- Consider splitting into multiple Lambda functions

**Memory Issues (Lambda)**
- Default memory is 2GB (Chromium needs significant memory)
- Increase `MemorySize` in `template.yaml` if needed

**DynamoDB Access Denied**
- Verify AWS credentials
- Check IAM permissions
- Ensure table names match configuration

**Selector Not Found**
- School portal HTML may have changed
- Update selectors in `homework.js` and `weeklyPlan.js`
- Use browser DevTools to find new selectors

### Debug Mode

Run with debug output:
```bash
DEBUG=pw:api npm start
```

Run browser in headed mode (see what's happening):
```bash
HEADLESS=false npm start
```

### View Lambda Logs
```bash
aws logs tail /aws/lambda/homework-scraper --region il-central-1 --follow
```

## 💰 Cost Estimate (Lambda Deployment)

Based on default configuration:
- **Lambda Executions**: 17 runs/week × 5 minutes × 2GB = ~$0.20/month
- **DynamoDB**: PAY_PER_REQUEST, minimal reads/writes = ~$0.01/month
- **Secrets Manager**: 1 secret = ~$0.40/month
- **Data Transfer**: Negligible
- **Total**: ~$0.60-$1.00/month

## 🔄 Updating the Scraper

When the school portal changes:

1. Identify changed elements using browser DevTools
2. Update selectors in `src/scraper/homework.js` or `src/scraper/weeklyPlan.js`
3. Test locally with `npm start`
4. If working, redeploy to Lambda: `./deploy.sh deploy`

## 🤝 Integration with Other Services

This scraper stores data that is consumed by:
- **node-server**: API server that queries homework data from DynamoDB
- **client**: React frontend that displays homework to users

Data flow:
```
Scraper → DynamoDB → node-server → React Client
                  ↘︎ Direct access
```

## 📄 License

MIT License - see main repository LICENSE file for details

## 🔗 Related Documentation

- [Main Project README](../README.md)
- [Lambda Deployment Guide](./LAMBDA_DEPLOYMENT.md)
- [Node.js Server README](../node-server/README.md)
- [React Client README](../client/README.md)
