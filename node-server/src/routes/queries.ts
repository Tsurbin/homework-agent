
import { Router, Response, Request, NextFunction } from 'express';
import { validateQueryAgent, validate } from '../middleware/validateInput.js';
import logger from '../utils/logger.js';
import { ToolHandler } from '../handlers/toolHandler.js';

export const queries = Router();

// Lazy-load the controller to avoid blocking module initialization
queries.post('/', validateQueryAgent, validate, async (req: Request, res: Response, next: NextFunction) => {
    try {
        logger.info('Starting queryyyy')
        // Dynamically import the controller only when the route is called
        const { queryAgent } = await import('../controllers/queriesController.js');
        logger.info('Imported queryyyy')
        return queryAgent(req, res, next);
    } catch (error) {
        next(error);
    }
});

// Test endpoint for getAllHomeworkForDate
queries.get('/homework-by-date', async (req: Request, res: Response, next: NextFunction) => {
    try {
        const { date } = req.query;
        
        if (!date) {
            return res.status(400).json({ success: false, message: 'date query parameter is required' });
        }
        
        const toolHandler = new ToolHandler();
        // Convert to ISO date string (YYYY-MM-DD) for DynamoDB
        const dateStr = new Date(date as string).toISOString().split('T')[0];
        const result = await toolHandler.handleGetAllHomeworkForDate({ date: dateStr });
        
        return res.json(result);
    } catch (error) {
        next(error);
    }
});

// Test endpoint for getHomeworkByDateRange
queries.get('/homework-by-date-range', async (req: Request, res: Response, next: NextFunction) => {
    try {
        const { subject, start_date, end_date } = req.query;
        
        if (!subject || !start_date || !end_date) {
            return res.status(400).json({ 
                success: false, 
                message: 'subject, start_date, and end_date query parameters are required' 
            });
        }
        
        const toolHandler = new ToolHandler();
        // Convert to ISO date strings (YYYY-MM-DD) for DynamoDB
        const startDateStr = new Date(start_date as string).toISOString().split('T')[0];
        const endDateStr = new Date(end_date as string).toISOString().split('T')[0];
        
        const result = await toolHandler.handleGetHomeworkByDateRange({ 
            subject: subject as string, 
            start_date: startDateStr, 
            end_date: endDateStr 
        });
        
        return res.json(result);
    } catch (error) {
        next(error);
    }
});
