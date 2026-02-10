# Homework Agent

A comprehensive system for scraping and managing homework assignments from educational platforms. This project consists of multiple components working together to automate homework data collection and provide a web interface for viewing assignments.

## 🏗️ Architecture

The system includes:

- **Node.js Scraper**: Uses Playwright to scrape homework data from educational websites
- **AWS Lambda Function**: Scheduled execution of the scraper with DynamoDB storage
- **React Client**: Web interface for viewing homework assignments
- **Infrastructure**: CloudFormation templates for AWS deployment

## 📋 Components

### 1. Node.js Scraper (`node-scraper/`)

A Playwright-based scraper that retrieves homework and weekly plan data from educational platforms.

#### Setup

```bash
cd node-scraper
npm install
```

#### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Copy the example file
cp ../.env.example .env

# Edit with your credentials
# Required: SCHOOL_USERNAME, SCHOOL_PASSWORD, AWS_REGION, DYNAMODB_TABLES, etc.
```

#### Running Locally

```bash
# Daily scrape (default)
npm start

# Historical scrape (all available data)
npm run start:historical

# Test Lambda locally
npm run test:lambda
```

#### Deployment

```bash
npm run deploy
```

### 2. AWS Lambda Function (`build/`)

Python-based Lambda function that runs the scraper on a schedule.

#### Dependencies

The Lambda uses a minimal set of dependencies defined in `requirements-lambda-minimal.txt`.

#### Deployment

```bash
./deploy-lambda-runner.sh
```

This script:
- Creates an optimized Lambda package
- Deploys via CloudFormation
- Sets up EventBridge scheduling

### 3. React Client (`client/`)

A modern React application built with Vite, TypeScript, and Tailwind CSS for viewing homework data.

#### Setup

```bash
cd client
npm install
```

#### Development

```bash
npm run dev
```

#### Build

```bash
npm run build
```

#### Deployment

```bash
npm run deploy
```

Deploys to S3 and CloudFront using the provided CloudFormation template.

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd homework-agent-2
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Install dependencies for all components**
   ```bash
   # Node.js scraper
   cd node-scraper && npm install && cd ..
   
   # React client
   cd client && npm install && cd ..
   ```

4. **Deploy infrastructure**
   ```bash
   # Deploy Lambda function
   ./deploy-lambda-runner.sh
   
   # Deploy client
   cd client && npm run deploy && cd ..
   ```

5. **Test locally**
   ```bash
   cd node-scraper
   npm run test:lambda
   ```

## ⚙️ Configuration

### Required Environment Variables

- `SCHOOL_USERNAME`: Educational platform username
- `SCHOOL_PASSWORD`: Educational platform password
- `AWS_REGION`: AWS region for deployment
- `DYNAMODB_TABLE_HOMEWORK`: DynamoDB table name for homework items
- `DYNAMODB_TABLE_WEEKLY_PLAN`: DynamoDB table name for weekly plans

### AWS Permissions

The system requires IAM permissions for:
- DynamoDB read/write access
- CloudFormation stack management
- Lambda function execution
- S3 bucket access for client deployment

## 📊 Data Flow

1. **Scheduled Execution**: EventBridge triggers Lambda function daily
2. **Scraping**: Lambda runs Node.js scraper via Playwright
3. **Storage**: Scraped data saved to DynamoDB tables
4. **Display**: React client queries DynamoDB and displays homework data

## 🧪 Testing

```bash
# Run scraper tests
cd node-scraper
npm test

# Test Lambda function locally
npm run test:lambda
```

## 📁 Project Structure

```
homework-agent-2/
├── build/                    # Lambda function and dependencies
│   ├── lambda_function.py
│   └── scraper/
├── client/                   # React web application
│   ├── src/
│   ├── package.json
│   └── deploy-s3-cloudfront.sh
├── node-scraper/             # Playwright scraper
│   ├── src/
│   ├── package.json
│   └── deploy.sh
├── config/                   # Configuration files
├── tests/                    # Test files
├── cloudformation-template.json
├── deploy-lambda-runner.sh
├── iam-policy.json
└── README.md
```

## 🔒 Security

- Credentials are stored in AWS Secrets Manager
- Environment variables are used for configuration
- IAM roles follow least-privilege principle

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Troubleshooting

### Common Issues

- **Playwright browser issues**: Ensure all dependencies are installed
- **AWS permissions**: Verify IAM roles and policies
- **DynamoDB tables**: Check table names and regions
- **Environment variables**: Ensure all required variables are set

### Logs

Check CloudWatch logs for Lambda function errors and deployment issues.