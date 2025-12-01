import express from 'express';
import { queries } from './routes/queries';
import cors from 'cors';



const app = express();
app.use(express.json());

app.use(cors({
    origin: 'http://localhost:5173',
}))

app.use('/api/query', queries)



const PORT = process.env.PORT || 8000;

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});