import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, GetCommand, QueryCommand, ScanCommand } from '@aws-sdk/lib-dynamodb';

const client = new DynamoDBClient({
      region: process.env.AWS_REGION || 'us-east-1',
      credentials: process.env.AWS_ACCESS_KEY_ID ? {
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
        KeyConditionExpression: 'class_name = :className AND task_date = :date',
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
        KeyConditionExpression: 'class_name = :className AND task_date BETWEEN :start AND :end',
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
        FilterExpression: 'task_date = :date',
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
        let filterExpression = 'task_date >= :today';
        const expressionAttributeValues: Record<string, any> = {
            ':today': today
        }
        if (className) {
            filterExpression += ' AND class_name = :className';
            expressionAttributeValues[':className'] = className;
        }

        let params = {
            TableName: this.tableName,
            FilterExpression: 'task_date >= :today',
            ExpressionAttributeValues: expressionAttributeValues,
            Limit: limit
        };

        if (className) {
        params.FilterExpression += ' AND class_name = :className';
        params.ExpressionAttributeValues[':className'] = className;
        }

        const command = new ScanCommand(params);
        const result = await docClient.send(command);
        return result.Items || [];
    }
}
