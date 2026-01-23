import serverless from 'serverless-http';
import { app } from './app.js';

// Create the serverless handler for API Gateway HTTP API (v2)
export const handler = serverless(app);