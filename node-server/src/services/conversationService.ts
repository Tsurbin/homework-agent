import { ClaudeService } from './cloudeService.js';
import { ToolHandler } from '../handlers/toolHandler.js';
import logger from '../utils/logger.js';
import { getSecret } from '../utils/secrets.js';



class ConversationService {
 
    private claudeService: ClaudeService;
    private toolHandler: ToolHandler;
    
    constructor(apiKey: string) {
        this.claudeService = new ClaudeService(apiKey);
        this.toolHandler = new ToolHandler();
    }

    static async create(): Promise<ConversationService> {
        const apiKey = await getSecret('ANTHROPIC_API_KEY') || process.env.ANTHROPIC_API_KEY;

        if (!apiKey) {
            throw new Error('Missing ANTHROPIC_API_KEY');
        }

        return new ConversationService(apiKey);
    }

    async handleQuery(userMessage = "", conversationHistory = []) {
    // Build conversation history
    const messages = [
      ...conversationHistory,
      {
        role: 'user',
        content: userMessage
      }
    ];

    const systemPrompt = this.claudeService.getSystemPrompt();
    let response: any = await this.claudeService.sendMessage(messages, systemPrompt);
    
    // Handle tool use loop
    let iterations = 0;
    const maxIterations = 5; // Prevent infinite loops

    while (response.stop_reason === 'tool_use' && iterations < maxIterations) {
      iterations++;
      logger.info(`Tool use iteration ${iterations}`);

      // Add assistant's response to history
      messages.push({
        role: 'assistant',
        content: response.content
      });

      // Execute all tool calls
      const toolResults = await this.executeToolCalls(response.content);

      // Add tool results to history
      messages.push({
        role: 'user',
        content: toolResults as any
      });

      // Get next response from Claude
      response = await this.claudeService.sendMessage(messages, systemPrompt);
    }

    // Extract final text response
    const finalResponse = this.extractTextResponse(response.content);

    return {
      response: finalResponse,
      conversationHistory: messages
    };
  }

  async executeToolCalls(contentBlocks: any[]) {
    const toolResults = [];

    for (const block of contentBlocks) {
      if (block.type === 'tool_use') {
        logger.info(`Executing tool: ${block.name}`);
        
        try {
          const result = await this.toolHandler.executeTool(block.name, block.input);
          
          toolResults.push({
            type: 'tool_result',
            tool_use_id: block.id,
            content: JSON.stringify(result)
          });
        } catch (error: any) {
          logger.error(`Tool execution error for ${block.name}:`, error);
          
          toolResults.push({
            type: 'tool_result',
            tool_use_id: block.id,
            content: JSON.stringify({
              success: false,
              error: error.message
            }),
            is_error: true
          });
        }
      }
    }

    return toolResults;
  }

  extractTextResponse(contentBlocks: any[]) {
    const textBlocks = contentBlocks.filter(block => block.type === 'text');
    return textBlocks.map(block => block.text).join('\n');
  }
}

// Lazy singleton - only create when first used
let conversationServiceInstance: ConversationService | null = null;
let initializationPromise: Promise<ConversationService> | null = null;

export async function getConversationService(): Promise<ConversationService> {
  if (conversationServiceInstance) {
    return conversationServiceInstance;
  }
  
  if (!initializationPromise) {
    initializationPromise = ConversationService.create();
  }
  
  conversationServiceInstance = await initializationPromise;
  return conversationServiceInstance;
}