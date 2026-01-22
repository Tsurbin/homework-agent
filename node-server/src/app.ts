import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import { queries } from './routes/queries.js';

const app = express();
app.use(express.json());

// Configure CORS for both local and production environments
const allowedOrigins = process.env.ALLOWED_ORIGINS 
    ? process.env.ALLOWED_ORIGINS.split(',') 
    : ['http://localhost:5173', 'http://localhost:5174', 'http://localhost:3000'];

app.use(cors({
    origin: allowedOrigins,
    credentials: true,
}));

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'healthy', service: 'homework-agent-lambda', timestamp: new Date().toISOString() });
});

app.use('/api/query', queries);

export { app };
