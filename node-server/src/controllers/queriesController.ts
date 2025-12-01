import { Request, Response, NextFunction } from 'express';

const AGENT_URL = process.env.AGENT_URL || 'http://127.0.0.1:9000';

export const queryAgent = async (req: Request, res: Response, next: NextFunction) => {
    const { prompt, conversation_history } = req.body;

    try {
        const response = await fetch(`${AGENT_URL}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: prompt, conversation_history }),
        });

        if (!response.ok) {
            next(new Error(`Agent service error: ${response.status}`));
            return;
        }

        const data = await response.json();
        return res.json({ response: data.response });
    } catch (error) {
        console.error('Error calling agent service:', error);
        next(error);
    }
}