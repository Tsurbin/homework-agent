import { logger } from '../utils/logger.js';
import { Request, Response, NextFunction, ErrorRequestHandler } from 'express';

export const errorHandler = (err: ErrorRequestHandler, req: Request, res: Response, next: NextFunction) => {
    logger.error('Error:', err);

    return res.status(500).json({
        error: 'Internal Server Error',
        message: 'An unexpected error occurred',
    });
};