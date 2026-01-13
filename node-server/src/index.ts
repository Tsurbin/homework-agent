import 'dotenv/config'; // Load environment variables first
import express from 'express';
import cors from 'cors';
import { queries } from './routes/queries';

console.log('🔄 Starting server initialization...');

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

// Health check endpoint for AWS load balancer
// app.get('/health', (req, res) => {
//     res.json({ status: 'healthy', service: 'node-server' });
// });

app.use('/api/query', queries);

const PORT = process.env.PORT || 8000;

app.listen(PORT, () => {
    console.log(`🚀 Server is running on port ${PORT}`);
});