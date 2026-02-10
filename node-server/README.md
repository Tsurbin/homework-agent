# Homework Agent - WhatsApp Webhook Bridge

This is a Node.js Express server that acts as a bridge between WhatsApp (via Twilio) and the Homework Agent system. It receives webhook requests from Twilio when WhatsApp messages are received, processes them using Claude AI, and responds back through WhatsApp.

## 🏗️ Architecture

```
WhatsApp User ←→ Twilio ←→ Node.js Express Server ←→ Claude AI ←→ DynamoDB
```

The server:
- Receives incoming WhatsApp messages via Twilio webhooks
- Processes messages using Claude AI (Anthropic)
- Queries homework data from DynamoDB
- Sends responses back to WhatsApp via Twilio
- Can be deployed as a traditional Express server or AWS Lambda function

## 📋 Features

- **WhatsApp Integration**: Full webhook support for Twilio WhatsApp API
- **AI-Powered Responses**: Uses Claude (Anthropic) to understand queries and generate responses
- **DynamoDB Integration**: Queries homework items and weekly plans from DynamoDB
- **Model Context Protocol (MCP)**: Supports MCP server for advanced integrations
- **Health Check**: `/health` endpoint for monitoring
- **CORS Support**: Configurable CORS for frontend integration
- **Lambda Support**: Can be deployed as AWS Lambda function with API Gateway

## 🚀 Quick Start

### Prerequisites

- Node.js 20.x or later
- npm or yarn
- AWS credentials configured (for DynamoDB and Secrets Manager access)
- Twilio account (for WhatsApp integration)
- Anthropic API key (for Claude AI)

### Installation

```bash
cd node-server
npm install
```

### Configuration

Create a `.env` file in the `node-server` directory:

```bash
# Server Configuration
PORT=8000
NODE_ENV=development

# AWS Configuration
AWS_REGION=il-central-1

# Twilio Configuration (for WhatsApp)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567890

# Anthropic API Key (for Claude AI)
ANTHROPIC_API_KEY=your_api_key

# DynamoDB Tables
DYNAMODB_TABLE_HOMEWORK=homework-items
DYNAMODB_TABLE_WEEKLY_PLAN=weekly-plan

# CORS Configuration (comma-separated origins)
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Secrets Manager (optional, for credential storage)
SECRETS_NAME=homework-scraper/credentials
```

### Running Locally

#### Development Mode (with auto-reload)
```bash
npm run dev
```

#### Production Mode
```bash
npm run build
npm start
```

#### Run MCP Server
```bash
npm run mcp
```

### Testing the Server

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test query endpoint (example)
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What homework do I have today?"}'
```

## 📦 Deployment

### Deploy as AWS Lambda

The server can be deployed as a Lambda function with API Gateway:

```bash
npm run deploy:lambda
```

This will:
1. Build the TypeScript code
2. Package dependencies
3. Deploy via CloudFormation
4. Set up API Gateway endpoints
5. Configure Lambda function

The deployment script uses `deploy-lambda.sh` and `cloudformation-lambda.yaml`.

### Deploy as Traditional Server

Deploy to any Node.js hosting platform:

```bash
# Build the application
npm run build

# Run with PM2 (recommended for production)
pm2 start dist/index.js --name homework-server

# Or use Docker
docker build -t homework-server .
docker run -p 8000:8000 homework-server
```

## 🔧 API Endpoints

### Health Check
```
GET /health
```
Returns server health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "homework-agent-lambda",
  "timestamp": "2026-02-10T09:00:00.000Z"
}
```

### Query API
```
POST /api/query
```
Processes natural language queries about homework.

**Request Body:**
```json
{
  "query": "What homework do I have for tomorrow?",
  "userId": "optional-user-id"
}
```

**Response:**
```json
{
  "response": "You have Math homework due tomorrow: Complete exercises 1-10 on page 45.",
  "timestamp": "2026-02-10T09:00:00.000Z"
}
```

## 📂 Project Structure

```
node-server/
├── src/
│   ├── index.ts              # Server entry point
│   ├── app.ts                # Express app configuration
│   ├── lambda.ts             # Lambda handler
│   ├── mcp-server.ts         # Model Context Protocol server
│   ├── routes/               # API routes
│   │   └── queries.ts        # Query endpoints
│   ├── controllers/          # Request controllers
│   ├── handlers/             # Business logic handlers
│   ├── services/             # External service integrations
│   │   ├── anthropic.ts      # Claude AI integration
│   │   ├── dynamodb.ts       # DynamoDB operations
│   │   └── twilio.ts         # WhatsApp/Twilio integration
│   ├── middleware/           # Express middleware
│   ├── tools/                # MCP tools
│   └── utils/                # Utility functions
├── package.json
├── tsconfig.json
├── cloudformation-lambda.yaml
├── deploy-lambda.sh
└── README.md
```

## 🔐 Security

- **Environment Variables**: All sensitive data stored in environment variables
- **AWS Secrets Manager**: Credentials can be fetched from Secrets Manager
- **CORS**: Configurable allowed origins
- **Input Validation**: Uses express-validator for request validation
- **IAM Roles**: Lambda uses IAM roles for AWS service access (no hardcoded credentials)

### Required IAM Permissions

When running as Lambda, the function needs:
- `dynamodb:GetItem`, `dynamodb:Query`, `dynamodb:Scan` on homework tables
- `secretsmanager:GetSecretValue` on credentials secret
- CloudWatch Logs permissions for logging

## 🧪 Testing

```bash
# Run linter
npm run lint

# Run type check
npm run build
```

## 📊 Monitoring

### CloudWatch Logs (Lambda)
```bash
aws logs tail /aws/lambda/homework-server --region il-central-1 --follow
```

### Application Logs
The server uses Winston for logging:
- Console logs in development
- Daily rotating file logs in production
- Structured JSON logging for CloudWatch

## 🤝 Integration with Other Services

This server integrates with:
- **node-scraper**: Reads homework data stored by the scraper in DynamoDB
- **client**: Provides API endpoints for the React frontend
- **Twilio**: Receives and sends WhatsApp messages
- **Claude AI**: Processes natural language queries
- **AWS Services**: DynamoDB, Secrets Manager, Lambda, API Gateway

## 🆘 Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# Find and kill the process using port 8000
lsof -ti:8000 | xargs kill -9
```

**AWS Credentials Not Found**
```bash
aws configure
# Or set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=il-central-1
```

**Twilio Webhook Errors**
- Ensure your server is publicly accessible (use ngrok for local testing)
- Verify webhook URL in Twilio console
- Check Twilio credentials in environment variables

**Claude AI Errors**
- Verify ANTHROPIC_API_KEY is set correctly
- Check API quota and rate limits

### Debug Mode

Enable debug logging:
```bash
DEBUG=* npm run dev
```

## 📄 License

MIT License - see main repository LICENSE file for details

## 🔗 Related Documentation

- [Main Project README](../README.md)
- [Node.js Scraper README](../node-scraper/README.md)
- [Lambda Deployment Guide](../node-scraper/LAMBDA_DEPLOYMENT.md)
- [React Client README](../client/README.md)
