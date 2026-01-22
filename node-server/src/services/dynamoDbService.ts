import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, GetCommand, QueryCommand, ScanCommand } from '@aws-sdk/lib-dynamodb';

// In Lambda, use IAM role credentials (don't pass explicit credentials)
// Only use explicit credentials for local development
const isLambda = !!process.env.AWS_LAMBDA_FUNCTION_NAME;

const client = new DynamoDBClient({
      region: process.env.AWS_REGION || 'us-east-1',
      credentials: (!isLambda && process.env.AWS_ACCESS_KEY_ID) ? {
        accessKeyId: process.env.AWS_ACCESS_KEY_ID,
        secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!
      } : undefined
});

const docClient = DynamoDBDocumentClient.from(client);


export class DynamoDBService {

    tableName = "";

    constructor(tableName = "") {
        this.tableName = tableName;
    }

    async getHomeworkByDate(className = "", date = new Date()) {
        const params = {
        TableName: this.tableName,
        KeyConditionExpression: 'class_name = :className AND #date = :date',
        ExpressionAttributeNames: {
            '#date': 'date'
        },
        ExpressionAttributeValues: {
            ':className': className,
            ':date': date
        }
        };

        const command = new QueryCommand(params);
        const result = await docClient.send(command);
        return result.Items || [];
    }

    async getHomeworkByDateRange(className = "", startDate = new Date(), endDate = new Date(Date.now() + 1)) {
        const params = {
        TableName: this.tableName,
        KeyConditionExpression: 'class_name = :className AND #date BETWEEN :start AND :end',
        ExpressionAttributeNames: {
            '#date': 'date'
        },
        ExpressionAttributeValues: {
            ':className': className,
            ':start': startDate,
            ':end': endDate
        }
        };

        const command = new QueryCommand(params);
        const result = await docClient.send(command);
        return result.Items || [];
    }

    async getAllHomeworkForDate(date = new Date()) {
        const params = {
        TableName: this.tableName,
        FilterExpression: '#date = :date',
        ExpressionAttributeNames: {
            '#date': 'date'
        },
        ExpressionAttributeValues: {
            ':date': date
        }
        };

        const command = new ScanCommand(params);
        const result = await docClient.send(command);
        return result.Items || [];
    }

    async getUpcomingHomework(className: string | null = null, limit: number = 10) {
        const today = new Date().toISOString().split('T')[0];
        let filterExpression = '#date >= :today';
        const expressionAttributeNames: Record<string, string> = {
            '#date': 'date'
        };
        const expressionAttributeValues: Record<string, any> = {
            ':today': today
        }
        if (className) {
            filterExpression += ' AND class_name = :className';
            expressionAttributeValues[':className'] = className;
        }

        let params: any = {
            TableName: this.tableName,
            FilterExpression: filterExpression,
            ExpressionAttributeNames: expressionAttributeNames,
            ExpressionAttributeValues: expressionAttributeValues,
            Limit: limit
        };

        const command = new ScanCommand(params);
        const result = await docClient.send(command);
        return result.Items || [];
    }
}
