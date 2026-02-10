# Homework Agent

A comprehensive system for scraping and managing homework assignments from educational platforms. This project consists of multiple components working together to automate homework data collection and provide a web interface for viewing assignments.

## 🏗️ Architecture

The system includes:

- **Node.js Scraper** ([node-scraper/](node-scraper/)): Uses Playwright to scrape homework data from educational websites
- **Node.js Server** ([node-server/](node-server/)): WhatsApp webhook bridge that receives messages via Twilio and responds using Claude AI
- **AWS Lambda Function**: Scheduled execution of the scraper with DynamoDB storage
- **React Client** ([client/](client/)): Web interface for viewing homework assignments
- **Infrastructure**: CloudFormation templates for AWS deployment

## 📋 Components

Each component has its own detailed README with setup, configuration, and deployment instructions.

### 1. Node.js Scraper ([`node-scraper/`](node-scraper/))

A Playwright-based scraper that retrieves homework and weekly plan data from educational platforms.

**📖 [Read the full Node.js Scraper documentation →](node-scraper/README.md)**

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

**📖 [Read the Lambda Deployment Guide →](node-scraper/LAMBDA_DEPLOYMENT.md)**

### 2. Node.js Server ([`node-server/`](node-server/))

A WhatsApp webhook bridge built with Express.js that receives messages via Twilio and responds using Claude AI.

**📖 [Read the full Node.js Server documentation →](node-server/README.md)**

#### Setup

```bash
cd node-server
npm install
```

#### Running Locally

```bash
# Development mode with auto-reload
npm run dev

# Production mode
npm run build
npm start
```

#### Deployment

```bash
# Deploy as AWS Lambda
npm run deploy:lambda

# Or deploy to any Node.js hosting platform
```

### 3. AWS Lambda Function

The scraper can be deployed as a Lambda function for scheduled execution.

**📖 [Read the Lambda Deployment Guide →](node-scraper/LAMBDA_DEPLOYMENT.md)**

#### Deployment

```bash
cd node-scraper
./deploy.sh deploy
```

This script:
- Creates an optimized Lambda package with @sparticuz/chromium
- Deploys via SAM/CloudFormation
- Sets up EventBridge scheduling (runs Sun-Thu: 10:00, 13:00, 16:00 IST; Fri: 12:00, 15:00 IST)
- Configures DynamoDB tables and Secrets Manager integration

### 4. React Client ([`client/`](client/))

A modern React application built with Vite, TypeScript, and Tailwind CSS for viewing homework data.

**📖 [Read the full React Client documentation →](client/README.md)**

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
   
   # Node.js server
   cd node-server && npm install && cd ..
   
   # React client
   cd client && npm install && cd ..
   ```

4. **Deploy infrastructure**
   ```bash
   # Deploy scraper as Lambda function
   cd node-scraper && ./deploy.sh deploy && cd ..
   
   # Deploy server as Lambda function (or run locally)
   cd node-server && npm run deploy:lambda && cd ..
   
   # Deploy client to S3 + CloudFront
   cd client && npm run deploy && cd ..
   ```

5. **Test locally**
   ```bash
   # Test scraper
   cd node-scraper
   npm run test:lambda
   
   # Run server locally
   cd ../node-server
   npm run dev
   
   # Run client locally
   cd ../client
   npm run dev
   ```

## ⚙️ Configuration

### Required Environment Variables

**For Scraper (node-scraper/):**
- `HW_USERNAME`: Educational platform username
- `HW_PASSWORD`: Educational platform password
- `LOGIN_URL`: School portal login URL
- `AWS_REGION`: AWS region for deployment
- `DYNAMODB_TABLE_NAME`: DynamoDB table name for homework items
- `WEEKLY_PLAN_TABLE_NAME`: DynamoDB table name for weekly plans

**For Server (node-server/):**
- `PORT`: Server port (default: 8000)
- `AWS_REGION`: AWS region
- `TWILIO_ACCOUNT_SID`: Twilio account SID
- `TWILIO_AUTH_TOKEN`: Twilio auth token
- `TWILIO_WHATSAPP_NUMBER`: Twilio WhatsApp number
- `ANTHROPIC_API_KEY`: Claude AI API key
- `DYNAMODB_TABLE_HOMEWORK`: Homework items table
- `DYNAMODB_TABLE_WEEKLY_PLAN`: Weekly plan table

**For Client (client/):**
- `VITE_API_URL`: Backend API URL (default: http://localhost:8000)

### AWS Permissions

The system requires IAM permissions for:
- DynamoDB read/write access
- CloudFormation stack management
- Lambda function execution
- S3 bucket access for client deployment

## 📊 Data Flow

```
┌─────────────┐         ┌──────────────┐         ┌──────────────┐
│ EventBridge │────────▶│   Lambda     │────────▶│  DynamoDB    │
│  Scheduler  │         │  (Scraper)   │         │   Tables     │
└─────────────┘         └──────────────┘         └───────┬──────┘
                                                          │
                                                          │
┌─────────────┐         ┌──────────────┐         ┌───────▼──────┐
│  WhatsApp   │◀───────▶│   Node.js    │────────▶│   Claude AI  │
│   (Twilio)  │         │    Server    │         │  (Anthropic) │
└─────────────┘         └──────┬───────┘         └──────────────┘
                               │
                               │
┌─────────────┐         ┌──────▼───────┐
│    User     │◀───────▶│    React     │
│   Browser   │         │    Client    │
└─────────────┘         └──────────────┘
```

1. **Scheduled Execution**: EventBridge triggers Lambda function on schedule (Sun-Thu: 10:00, 13:00, 16:00 IST; Fri: 12:00, 15:00 IST)
2. **Scraping**: Lambda runs Node.js scraper with Playwright and @sparticuz/chromium
3. **Storage**: Scraped data saved to DynamoDB tables (homework-items, weekly-plan)
4. **WhatsApp Queries**: Users send messages via WhatsApp → Twilio webhook → Node.js server
5. **AI Processing**: Server uses Claude AI to understand queries and fetch relevant homework data
6. **Web Interface**: React client queries data via Node.js server API
7. **Responses**: Both WhatsApp and web interface display homework information

## 🧪 Testing

```bash
# Test scraper locally
cd node-scraper
npm start
npm run test:lambda

# Test server locally
cd node-server
npm run dev
# In another terminal, test the API:
curl http://localhost:8000/health

# Test client locally
cd client
npm run dev
```

## 📁 Project Structure

```
homework-agent/
├── node-scraper/             # Playwright scraper (Lambda or local)
│   ├── src/
│   │   ├── index.js          # Main scraper orchestrator
│   │   ├── config/           # Configuration
│   │   └── scraper/          # Scraper modules
│   │       ├── auth.js       # Authentication
│   │       ├── homework.js   # Homework scraping
│   │       ├── weeklyPlan.js # Schedule scraping
│   │       └── dynamodb.js   # DynamoDB operations
│   ├── lambda.js             # Lambda handler
│   ├── template.yaml         # SAM template
│   ├── deploy.sh             # Deployment script
│   ├── package.json
│   ├── README.md             # Scraper documentation
│   └── LAMBDA_DEPLOYMENT.md  # Lambda deployment guide
├── node-server/              # Express API server (WhatsApp bridge)
│   ├── src/
│   │   ├── index.ts          # Server entry point
│   │   ├── app.ts            # Express app
│   │   ├── lambda.ts         # Lambda handler
│   │   ├── routes/           # API routes
│   │   ├── controllers/      # Request controllers
│   │   ├── services/         # External services
│   │   │   ├── anthropic.ts  # Claude AI
│   │   │   ├── dynamodb.ts   # DynamoDB
│   │   │   └── twilio.ts     # WhatsApp/Twilio
│   │   └── middleware/       # Express middleware
│   ├── cloudformation-lambda.yaml
│   ├── deploy-lambda.sh
│   ├── package.json
│   └── README.md             # Server documentation
├── client/                   # React web application
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── cloudformation-s3-cloudfront.yaml
│   ├── deploy-s3-cloudfront.sh
│   ├── package.json
│   ├── vite.config.ts
│   └── README.md             # Client documentation
├── config/                   # Shared configuration files
├── tests/                    # Integration tests
├── .env.example              # Environment variables template
├── cloudformation-template.json
├── iam-policy.json
└── README.md                 # This file - Project overview
```
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

## 📚 Documentation

Each component has its own detailed documentation:

- **[Node.js Scraper Documentation](node-scraper/README.md)** - Setup, configuration, local and Lambda deployment
- **[Lambda Deployment Guide](node-scraper/LAMBDA_DEPLOYMENT.md)** - Comprehensive Lambda deployment instructions
- **[Node.js Server Documentation](node-server/README.md)** - WhatsApp webhook bridge setup and deployment
- **[React Client Documentation](client/README.md)** - Frontend setup, development, and deployment

For detailed setup instructions for each component, refer to the individual README files in their respective directories.