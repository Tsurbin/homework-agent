import express from 'express';
import { queries } from './routes/queries';
import cors from 'cors';



const app = express();
app.use(express.json());

// Configure CORS for both local and production environments
const allowedOrigins = process.env.ALLOWED_ORIGINS 
    ? process.env.ALLOWED_ORIGINS.split(',') 
    : ['http://localhost:5173'];

app.use(cors({
    origin: allowedOrigins,
    credentials: true,
}));

// Health check endpoint for AWS load balancer
app.get('/health', (req, res) => {
    res.json({ status: 'healthy', service: 'node-server' });
});

app.use('/api/query', queries)



const PORT = process.env.PORT || 8000;

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});