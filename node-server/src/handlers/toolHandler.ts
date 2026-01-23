import { DynamoDBService } from '../services/dynamoDbService';
import logger from '../utils/logger';


interface getHomeworkByDateInputType {
    subject: string, 
    date: string, 
}

interface getHomeworkByDateRangeInputType {
    subject: string, 
    start_date: string, 
    end_date: string
}

interface getUpcomingHomeworkInputType {
    subject: string, 
    limit: number
}


export class ToolHandler {
 
    private dbService;
    
    constructor() {
        this.dbService = new DynamoDBService(process.env.HOMEWORK_TABLE_NAME);
    }

    async executeTool<T>(toolName: string, toolInput: T) {
        logger.info(`Executing tool: ${toolName}`, { input: toolInput });

        try {
            if (!(toolName in this.toolsHandlers)) {
                throw new Error(`Tool '${toolName}' not found`);
            }
            return this.toolsHandlers[toolName as keyof typeof this.toolsHandlers](toolInput);
        }
        catch(err) {
            logger.error(`Error executing tool ${toolName}:`, err);
            throw err;
        }
    }


    toolsHandlers = {
        get_homework_by_date: async (toolInput: any) => await this.handleGetHomeworkByDate(toolInput),
        get_homework_by_date_range: async (toolInput: any) => await this.handleGetHomeworkByDateRange(toolInput),
        get_all_homework_for_date: async (toolInput: any) => await this.handleGetAllHomeworkForDate(toolInput),
        get_upcoming_homework: async (toolInput: any) => await this.handleGetUpcomingHomework(toolInput)
    }


    async handleGetHomeworkByDate({ subject, date }: getHomeworkByDateInputType) {
        const results = await this.dbService.getHomeworkByDate(subject, date);
        
        if (results.length === 0) {
            return { 
                success: true,
                message: `No homework found for ${subject} on ${date}`,
                data: []
            };
        }

        return {
            success: true,
            data: results
        };
    }

    async handleGetHomeworkByDateRange({ subject, start_date, end_date }: getHomeworkByDateRangeInputType) {
        const results = await this.dbService.getHomeworkByDateRange(subject, start_date, end_date);
    
        return {
            success: true,
            data: results,
            count: results.length
        };
    }
    
    async handleGetAllHomeworkForDate({ date }: { date: string }) {
        const results = await this.dbService.getAllHomeworkForDate(date);
        
        return {
            success: true,
            data: results,
            count: results.length
        };
    }

    async handleGetUpcomingHomework({ subject, limit = 10 }: getUpcomingHomeworkInputType) {
        const results = await this.dbService.getUpcomingHomework(subject, limit);
        
        return {
            success: true,
            data: results,
            count: results.length
        };
    }
}