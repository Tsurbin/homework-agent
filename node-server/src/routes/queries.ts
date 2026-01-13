
import { Router, Response, Request, NextFunction } from 'express';
import { validateQueryAgent, validate } from '../middleware/validateInput';
import logger from '../utils/logger';

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