
import { Router } from 'express';
import { queryAgent } from '../controllers/queriesController';
import { validateQueryAgent, validate } from '../middleware/validateInput';

export const queries = Router();

queries.post('/', validateQueryAgent, validate , queryAgent);