import { body, validationResult } from 'express-validator';
import { Request, Response, NextFunction } from 'express';
import { logger } from '../utils/logger';


export const validateQueryAgent = [
    body('prompt').trim().isLength({ min: 1 }).withMessage('Prompt is required'),
    body('prompt').trim().isLength({ max: 500 }).withMessage('Prompt is too long (max 500 characters)'),
];

export const validate = (req: Request, res: Response, next: NextFunction): void => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        logger.error('Input Validation error');
        logger.error(JSON.stringify(errors.array()));
        res.status(400).json({ errors: errors.array() });
        return;
    }
    next();
};
