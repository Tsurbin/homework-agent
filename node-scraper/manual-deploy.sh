#!/bin/bash

# Manual Lambda Deployment Script (bypassing CloudFormation)
set -e

STACK_NAME="homework-scraper"
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${STACK_NAME}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Creating IAM role for Lambda...${NC}"
aws iam create-role \
    --role-name ${STACK_NAME}-lambda-role \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }' 2>/dev/null || echo "Role already exists"

echo -e "${YELLOW}Attaching basic execution policy...${NC}"
aws iam attach-role-policy \
    --role-name ${STACK_NAME}-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

echo -e "${YELLOW}Creating inline policy for DynamoDB and Secrets Manager...${NC}"
aws iam put-role-policy \
    --role-name ${STACK_NAME}-lambda-role \
    --policy-name ${STACK_NAME}-permissions \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                "Resource": "arn:aws:dynamodb:'${REGION}':'${ACCOUNT_ID}':table/homework-items"
            },
            {
                "Effect": "Allow",
                "Action": "secretsmanager:GetSecretValue",
                "Resource": "arn:aws:secretsmanager:'${REGION}':'${ACCOUNT_ID}':secret:homework-scraper-credentials*"
            }
        ]
    }'

echo -e "${YELLOW}Waiting for IAM role to propagate...${NC}"
sleep 10

echo -e "${YELLOW}Creating Lambda function...${NC}"
aws lambda create-function \
    --function-name ${STACK_NAME}-function \
    --role arn:aws:iam::${ACCOUNT_ID}:role/${STACK_NAME}-lambda-role \
    --package-type Image \
    --code ImageUri=${ECR_URI}:latest \
    --timeout 900 \
    --memory-size 2048 \
    --environment "Variables={
        DYNAMODB_TABLE_NAME=homework-items,
        SECRETS_MANAGER_SECRET_NAME=homework-scraper-credentials,
        LOGIN_URL=https://webtop.smartschool.co.il/account/login,
        HOMEWORK_URL=https://webtop.smartschool.co.il/Student_Card/11,
        AWS_REGION=${REGION},
        NODE_ENV=production,
        PLAYWRIGHT_HEADLESS=true
    }" \
    --region ${REGION} 2>/dev/null || aws lambda update-function-code \
        --function-name ${STACK_NAME}-function \
        --image-uri ${ECR_URI}:latest \
        --region ${REGION}

echo -e "${YELLOW}Creating EventBridge rule...${NC}"
aws events put-rule \
    --name ${STACK_NAME}-schedule \
    --description "Triggers homework scraper at 16:30 every day except Saturday" \
    --schedule-expression "cron(30 16 ? * SUN,MON,TUE,WED,THU,FRI *)" \
    --state ENABLED \
    --region ${REGION}

echo -e "${YELLOW}Adding Lambda permission for EventBridge...${NC}"
aws lambda add-permission \
    --function-name ${STACK_NAME}-function \
    --statement-id EventBridgeInvoke \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn arn:aws:events:${REGION}:${ACCOUNT_ID}:rule/${STACK_NAME}-schedule \
    --region ${REGION} 2>/dev/null || echo "Permission already exists"

echo -e "${YELLOW}Adding Lambda target to EventBridge rule...${NC}"
aws events put-targets \
    --rule ${STACK_NAME}-schedule \
    --targets "Id=1,Arn=arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${STACK_NAME}-function" \
    --region ${REGION}

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo -e "${GREEN}Lambda Function: ${STACK_NAME}-function${NC}"
echo -e "${GREEN}Schedule: Every day at 16:30 except Saturday${NC}"
