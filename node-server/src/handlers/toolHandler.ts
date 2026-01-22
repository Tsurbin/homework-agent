import { DynamoDBService } from '../services/dynamoDbService.js';
import logger from '../utils/logger.js';


interface getHomeworkByDateInputType {
    class_name: string, 
    date: Date, 
}

interface getHomeworkByDateRangeInputType {
    class_name: string, 
    start_date: Date, 
    end_date: Date
}

interface getUpcomingHomeworkInputType {
    class_name: string, 
    limit: number
}


export class ToolHandler {
 
    private dbService;
    
    constructor() {
        this.dbService = new DynamoDBService(process.env.DYNAMODB_TABLE_NAME || process.env.HOMEWORK_TABLE_NAME);
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


    async handleGetHomeworkByDate({ class_name, date }: getHomeworkByDateInputType) {
        const results = await this.dbService.getHomeworkByDate(class_name, date);
        
        if (results.length === 0) {
            return { 
                success: true,
                message: `No homework found for ${class_name} on ${date}`,
                data: []
            };
        }

        return {
            success: true,
            data: results
        };
    }

    async handleGetHomeworkByDateRange({ class_name, start_date, end_date }: getHomeworkByDateRangeInputType) {
        const results = await this.dbService.getHomeworkByDateRange(class_name, start_date, end_date);
    
        return {
            success: true,
            data: results,
            count: results.length
        };
    }
    
    async handleGetAllHomeworkForDate({ date }: { date: Date }) {
        const results = await this.dbService.getAllHomeworkForDate(date);
        
        return {
            success: true,
            data: results,
            count: results.length
        };
    }

    async handleGetUpcomingHomework({ class_name, limit = 10 }: getUpcomingHomeworkInputType) {
        const results = await this.dbService.getUpcomingHomework(class_name, limit);
        
        return {
            success: true,
            data: results,
            count: results.length
        };
    }
}