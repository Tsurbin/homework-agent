import Anthropic from '@anthropic-ai/sdk';
import { getAllTools }from '../tools';
import logger from '../utils/logger';
import { getSecret } from '../utils/secrets';
import { error } from 'console';



export class ClaudeService {

    private client: Anthropic;
    private model: string;
    private tools: any;

    constructor(apiKey: string) {

        this.client = new Anthropic({
            apiKey: apiKey
        });
        this.model = 'claude-sonnet-4-20250514';
        this.tools = getAllTools();
    }

    async sendMessage(messages: any, systemPrompt: string | null = null) {
        try {
            const params = {
                model: this.model,
                max_tokens: 4096,
                messages: messages,
                tools: this.tools,
                system: ""
            }
            
            if (systemPrompt) {
                params["system"] = systemPrompt;
            }

            logger.info('Sending request to Claude', { 
                messageCount: messages.length,
                toolCount: this.tools.length 
            });

            const response = await this.client.messages.create(params);

            logger.info('Received response from Claude', { 
                stopReason: response.stop_reason,
                contentBlocks: response.content.length 
            });

            return response;
        }
        catch(err) {
            logger.error(`Error callinf cloude api: ${err}`);
            throw err;
        }
    }

    getSystemPrompt() {
        return `You are a helpful homework assistant. You help students keep track of their homework assignments and deadlines.

        Your name is Tzipi Bot - please start the first conversation declaring your name

            Current date: ${new Date().toISOString().split('T')[0]}

            You have access to tools that can query the homework database. Use these tools when:
            - A student asks about specific homework assignments
            - A student wants to know what's due on a particular date
            - A student asks about upcoming homework

            Important guidelines:
            - Only use tools when you need specific homework data from the database
            - If a student asks a general question about studying or homework strategies, answer directly without using tools
            - When interpreting dates, "today" means the current date shown above, "tomorrow" is the next day, etc.
            - Be friendly, encouraging, and helpful
            - Format homework information clearly and readably
            - If no homework is found, reassure the student positively
            - If you haven’t used any tools and you return an answer, it should be no longer than two sentences
            - Limit your answers to 20 words max

            Always be specific about which class and date you're checking when you use tools.`;
    }
}