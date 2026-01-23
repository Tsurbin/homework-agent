import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, QueryCommand, ScanCommand } from '@aws-sdk/lib-dynamodb';

interface WeeklyPlanItem {
    date: string;
    class_number_teacher: string;
    class_number?: number;
    subject?: string;
    teacher?: string;
    class_description?: string;
    class_comments?: string;
    day_name?: string;
    created_at?: string;
    updated_at?: string;
}

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

export class WeeklyPlanService {
    tableName: string;

    constructor(tableName = 'weekly-plan') {
        this.tableName = tableName;
    }

    /**
     * Get all schedule entries for a specific date
     */
    async getScheduleForDate(date: string) {
        const params = {
            TableName: this.tableName,
            KeyConditionExpression: '#date = :date',
            ExpressionAttributeNames: {
                '#date': 'date'
            },
            ExpressionAttributeValues: {
                ':date': date
            }
        };

        const command = new QueryCommand(params);
        const result = await docClient.send(command);
        
        // Sort by class_number
        const items = result.Items || [];
        return items.sort((a: Record<string, any>, b: Record<string, any>) => (a.class_number || 0) - (b.class_number || 0));
    }

    /**
     * Get schedule entries for a specific subject on a given date
     */
    async getScheduleForSubject(subject: string, date: string) {
        const params = {
            TableName: this.tableName,
            KeyConditionExpression: '#date = :date',
            FilterExpression: 'contains(#subject, :subject)',
            ExpressionAttributeNames: {
                '#date': 'date',
                '#subject': 'subject'
            },
            ExpressionAttributeValues: {
                ':date': date,
                ':subject': subject
            }
        };

        const command = new QueryCommand(params);
        const result = await docClient.send(command);
        return result.Items || [];
    }

    /**
     * Get schedule entries for a date range
     */
    async getScheduleByDateRange(startDate: string, endDate: string) {
        const params = {
            TableName: this.tableName,
            FilterExpression: '#date BETWEEN :start AND :end',
            ExpressionAttributeNames: {
                '#date': 'date'
            },
            ExpressionAttributeValues: {
                ':start': startDate,
                ':end': endDate
            }
        };

        const command = new ScanCommand(params);
        const result = await docClient.send(command);
        
        // Sort by date and then by class_number
        const items = result.Items || [];
        return items.sort((a: Record<string, any>, b: Record<string, any>) => {
            if (a.date !== b.date) {
                return a.date.localeCompare(b.date);
            }
            return (a.class_number || 0) - (b.class_number || 0);
        });
    }

    /**
     * Get what to bring for a specific date
     * Returns schedule with class_comments which contain what to bring
     */
    async getWhatToBring(date: string) {
        const schedule = await this.getScheduleForDate(date);
        
        // Transform the data to focus on what to bring
        return schedule.map((entry) => ({
            class_number: entry.class_number,
            subject: entry.subject,
            teacher: entry.teacher,
            class_description: entry.class_description,
            class_comments: entry.class_comments,
            day_name: entry.day_name,
            what_to_bring: this.extractWhatToBring(entry)
        }));
    }

    /**
     * Helper to extract what to bring from entry
     * The "what to bring" info is found in class_comments field
     */
    private extractWhatToBring(entry: Record<string, any>): string {
        const items: string[] = [];
        
        // class_comments contains the "what to bring" information
        if (entry.class_comments && entry.class_comments.trim()) {
            items.push(entry.class_comments);
        }
        
        return items.length > 0 ? items.join('; ') : 'No specific items noted';
    }
}
