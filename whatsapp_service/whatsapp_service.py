"""
WhatsApp Service for Homework Agent
Provides WhatsApp integration using Twilio API
"""
import os
import asyncio
from typing import Dict, Optional
from datetime import datetime
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from fastapi import FastAPI, Request, Form
from fastapi.responses import PlainTextResponse
import uvicorn
from loguru import logger

from agent.agent import HomeworkAgent


class WhatsAppService:
    def __init__(self):
        """Initialize WhatsApp service with Twilio client."""
        # Twilio credentials - set these in environment variables
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')
        
        if not self.account_sid or not self.auth_token:
            raise ValueError("Twilio credentials not found in environment variables")
        
        self.client = Client(self.account_sid, self.auth_token)
        self.homework_agent = HomeworkAgent()
        
        # Store user sessions to track conversation context
        self.user_sessions: Dict[str, dict] = {}
        
        logger.info("WhatsApp service initialized")

    async def send_message(self, to_number: str, message: str) -> bool:
        """
        Send a WhatsApp message to a user.
        
        Args:
            to_number: WhatsApp number (format: whatsapp:+1234567890)
            message: Message content to send
            
        Returns:
            bool: True if message was sent successfully
        """
        try:
            # Ensure proper WhatsApp number format
            if not to_number.startswith('whatsapp:'):
                to_number = f"whatsapp:{to_number}"
            
            message_instance = self.client.messages.create(
                body=message,
                from_=self.whatsapp_number,
                to=to_number
            )
            
            logger.info(f"Message sent successfully. SID: {message_instance.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            return False

    async def process_incoming_message(self, from_number: str, message_body: str) -> str:
        """
        Process incoming WhatsApp message and generate response.
        
        Args:
            from_number: Sender's WhatsApp number
            message_body: Content of the message
            
        Returns:
            str: Response message to send back
        """
        try:
            # Initialize user session if not exists
            if from_number not in self.user_sessions:
                self.user_sessions[from_number] = {
                    'created_at': datetime.now(),
                    'last_activity': datetime.now(),
                    'message_count': 0
                }
            
            # Update session info
            session = self.user_sessions[from_number]
            session['last_activity'] = datetime.now()
            session['message_count'] += 1
            
            logger.info(f"Processing message from {from_number}: {message_body}")
            
            # Handle special commands
            message_lower = message_body.lower().strip()
            
            if message_lower in ['hi', 'hello', 'hey', 'start']:
                return self._get_welcome_message()
            
            elif message_lower in ['help', '/help']:
                return self._get_help_message()
            
            elif message_lower in ['today', '/today']:
                return await self._get_todays_homework()
            
            elif message_lower.startswith('homework'):
                # Extract the actual question after "homework"
                question = message_body[8:].strip() if len(message_body) > 8 else "What homework do I have today?"
                return await self.homework_agent.process_question(question)
            
            else:
                # Process as general homework question
                response = await self.homework_agent.process_question(message_body)
                return response
                
        except Exception as e:
            logger.error(f"Error processing message from {from_number}: {e}")
            return "Sorry, I encountered an error processing your request. Please try again."

    def _get_welcome_message(self) -> str:
        """Generate welcome message for new users."""
        return """🎓 Welcome to Homework Agent! 

I can help you with your homework questions. Here's what I can do:

📚 Ask me about your homework assignments
📅 Check today's assignments
❓ Get help with specific subjects
⏰ Find out due dates

Just send me a message like:
• "What homework do I have today?"
• "Math homework for tomorrow"
• "When is my science project due?"

Type 'help' for more commands."""

    def _get_help_message(self) -> str:
        """Generate help message."""
        return """📖 Homework Agent Help

Commands:
• 'today' - Show today's homework
• 'homework [question]' - Ask specific homework questions
• 'help' - Show this help message

Examples:
• "What homework do I have for math?"
• "When is my English essay due?"
• "Show me all assignments for this week"
• "Do I have any science homework?"

Just type your question naturally! 🤖"""

    async def _get_todays_homework(self) -> str:
        """Get today's homework formatted for WhatsApp."""
        try:
            today_question = "What homework do I have today?"
            response = await self.homework_agent.process_question(today_question)
            return f"📅 Today's Homework:\n\n{response}"
        except Exception as e:
            logger.error(f"Error getting today's homework: {e}")
            return "Sorry, I couldn't fetch today's homework. Please try again."


# FastAPI app for webhook handling
app = FastAPI(title="Homework Agent WhatsApp Service")
whatsapp_service = WhatsAppService()


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request, From: str = Form(), Body: str = Form()):
    """
    Webhook endpoint for receiving WhatsApp messages from Twilio.
    """
    logger.info(f"Received WhatsApp message from {From}: {Body}")
    
    try:
        # Process the message and get response
        response_text = await whatsapp_service.process_incoming_message(From, Body)
        
        # Create TwiML response
        resp = MessagingResponse()
        resp.message(response_text)
        
        logger.info(f"Sending response to {From}: {response_text[:100]}...")
        
        return PlainTextResponse(content=str(resp), media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error in WhatsApp webhook: {e}")
        
        # Send error response
        resp = MessagingResponse()
        resp.message("Sorry, I'm having trouble right now. Please try again later.")
        return PlainTextResponse(content=str(resp), media_type="application/xml")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "homework-agent-whatsapp"}


@app.post("/send-message")
async def send_message_endpoint(to_number: str, message: str):
    """
    API endpoint to send WhatsApp messages programmatically.
    """
    success = await whatsapp_service.send_message(to_number, message)
    return {"success": success, "to": to_number, "message": message}


if __name__ == "__main__":
    # Run the FastAPI server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )