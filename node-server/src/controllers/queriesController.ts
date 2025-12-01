import { Request, Response, NextFunction } from 'express';


export const queryAgent = (req: Request, res: Response, next: NextFunction) => {
    
    
    const { prompt } = req.body;
    // Here you would add the logic to interact with the agent using the prompt provided.
    // For demonstration purposes, we'll just return a mock response.
    const mockResponse = `Agent response to the prompt: "${prompt}"`;

    res.json({ response: mockResponse });
}