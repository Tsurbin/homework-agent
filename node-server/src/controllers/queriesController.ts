import { Request, Response, NextFunction } from 'express';
import { HomeworkAgent } from '../agent/index.js';
import logger from '../utils/logger.js';
import { getConversationService } from '../services/conversationService.js';


export const queryAgent = async (req: Request, res: Response, next: NextFunction) => {
    const { prompt, conversation_history: conversationHistory } = req.body;

    try {
        logger.info('Received query', { 
            messageLength: prompt.length,
            historyLength: conversationHistory.length 
        });
        
        // Get the service instance
        const conversationService = await getConversationService();
        const result = await conversationService.handleQuery(prompt, conversationHistory);

        res.json({
            success: true,
            response: result.response,
            conversationHistory: result.conversationHistory
        });
        return;
    } catch (error) {
        console.error('Error processing query:', error);
        next(error);
    }
}


// export const queryAgent = async (req: Request, res: Response, next: NextFunction) => {
//     const { prompt, conversation_history: conversationHistory } = req.body;

//     try {
//         logger.info('Received query', { 
//             messageLength: prompt.length,
//             historyLength: conversationHistory.length 
//         });
//         const response = await agent.handleConversation(prompt, conversationHistory);
//         return res.json({ response });
//     } catch (error) {
//         console.error('Error processing query:', error);
//         next(error);
//     }
// }