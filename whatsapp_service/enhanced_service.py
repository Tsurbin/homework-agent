"""
Enhanced WhatsApp Service with rate limiting and better message formatting
"""
import os
import asyncio
from typing import Dict, Optional
from datetime import datetime
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from loguru import logger

from agent.agent import HomeworkAgent
from .config import get_whatsapp_settings
from .rate_limiter import RateLimiter
from .message_formatter import WhatsAppFormatter

# Try to import Twilio, fall back to mock if not available
try:
    from twilio.rest import Client
    from twilio.twiml.messaging_response import MessagingResponse
    TWILIO_AVAILABLE = True
except ImportError:
    logger.warning("Twilio not installed. WhatsApp service will run in mock mode.")
    TWILIO_AVAILABLE = False
    
    # Mock Twilio classes for development
    class Client:
        def __init__(self, *args, **kwargs):
            pass
        
        @property
        def messages(self):
            return self
        
        def create(self, **kwargs):
            logger.info(f"Mock message sent: {kwargs}")
            return type('Message', (), {'sid': 'mock_sid'})()
    
    class MessagingResponse:
        def __init__(self):
            self._messages = []
        
        def message(self, body):
            self._messages.append(body)
            return self
        
        def __str__(self):
            return f"<Response>{self._messages[0] if self._messages else ''}</Response>"


class EnhancedWhatsAppService:
    def __init__(self):
        """Initialize enhanced WhatsApp service."""
        self.settings = get_whatsapp_settings()
        self.rate_limiter = RateLimiter(
            max_per_minute=self.settings.rate_limit_per_minute,
            max_per_hour=self.settings.rate_limit_per_hour
        )
        self.formatter = WhatsAppFormatter()
        
        # Initialize Twilio client if credentials are available
        if TWILIO_AVAILABLE and self.settings.twilio_account_sid and self.settings.twilio_auth_token:
            self.client = Client(self.settings.twilio_account_sid, self.settings.twilio_auth_token)
            logger.info("Twilio client initialized successfully")
        else:
            self.client = Client()  # Mock client
            logger.info("Using mock Twilio client (development mode)")
        
        self.homework_agent = HomeworkAgent()
        
        # Store user sessions
        self.user_sessions: Dict[str, dict] = {}
        
        logger.info("Enhanced WhatsApp service initialized")

    async def send_message(self, to_number: str, message: str) -> bool:
        """Send a WhatsApp message to a user."""
        try:
            # Ensure proper WhatsApp number format
            if not to_number.startswith('whatsapp:'):
                to_number = f"whatsapp:{to_number}"
            
            # Truncate message if too long
            message = self.formatter.truncate_message(message)
            
            message_instance = self.client.messages.create(
                body=message,
                from_=self.settings.twilio_whatsapp_number,
                to=to_number
            )
            
            logger.info(f"Message sent successfully. SID: {message_instance.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            return False

    async def process_incoming_message(self, from_number: str, message_body: str) -> str:
        """Process incoming WhatsApp message with rate limiting."""
        try:
            # Check rate limits
            if not self.rate_limiter.is_allowed(from_number):
                reset_time = self.rate_limiter.get_reset_time(from_number)
                return self.formatter.format_error_message("rate_limit")
            
            # Initialize or update user session
            self._update_user_session(from_number)
            
            logger.info(f"Processing message from {from_number}: {message_body}")
            
            # Handle commands and questions
            return await self._handle_message(from_number, message_body)
                
        except Exception as e:
            logger.error(f"Error processing message from {from_number}: {e}")
            return self.formatter.format_error_message("general")

    def _update_user_session(self, from_number: str):
        """Update user session information."""
        if from_number not in self.user_sessions:
            self.user_sessions[from_number] = {
                'created_at': datetime.now(),
                'last_activity': datetime.now(),
                'message_count': 0,
                'context': {}
            }
        
        session = self.user_sessions[from_number]
        session['last_activity'] = datetime.now()
        session['message_count'] += 1

    async def _handle_message(self, from_number: str, message_body: str) -> str:
        """Handle different types of messages and commands."""
        message_lower = message_body.lower().strip()
        
        # Welcome messages
        if message_lower in ['hi', 'hello', 'hey', 'start', 'begin']:
            return self._get_welcome_message()
        
        # Help command
        elif message_lower in ['help', '/help', 'commands']:
            return self._get_help_message()
        
        # Today's homework
        elif message_lower in ['today', '/today', "today's homework", 'homework today']:
            return await self._get_todays_homework()
        
        # Tomorrow's homework
        elif message_lower in ['tomorrow', '/tomorrow', "tomorrow's homework", 'homework tomorrow']:
            return await self._get_tomorrows_homework()
        
        # Due dates
        elif message_lower in ['due', 'due dates', 'deadlines', '/due']:
            return await self._get_due_dates()
        
        # Subject-specific homework
        elif any(subject in message_lower for subject in ['math', 'science', 'english', 'history', 'physics', 'chemistry', 'biology']):
            return await self._get_subject_homework(message_body)
        
        # Date-specific queries
        elif self._is_date_query(message_body):
            return await self._get_date_homework(message_body)
        
        # General homework questions
        else:
            response = await self.homework_agent.process_question(message_body)
            # Format the response for WhatsApp if it's just plain text
            if response and not response.startswith('📚') and not response.startswith('🎓'):
                response = f"🤖 {response}"
            return response

    def _is_date_query(self, message: str) -> bool:
        """Check if message contains date patterns."""
        date_patterns = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
                        'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
                        'next week', 'this week', 'yesterday', '2024', '2025']
        return any(pattern in message.lower() for pattern in date_patterns)

    async def _get_subject_homework(self, message: str) -> str:
        """Get homework for a specific subject."""
        try:
            response = await self.homework_agent.process_question(message)
            return f"📖 {response}"
        except Exception as e:
            logger.error(f"Error getting subject homework: {e}")
            return self.formatter.format_error_message("general")

    async def _get_date_homework(self, message: str) -> str:
        """Get homework for a specific date."""
        try:
            response = await self.homework_agent.process_question(message)
            return f"📅 {response}"
        except Exception as e:
            logger.error(f"Error getting date homework: {e}")
            return self.formatter.format_error_message("general")

    async def _get_tomorrows_homework(self) -> str:
        """Get tomorrow's homework."""
        try:
            response = await self.homework_agent.process_question("What homework do I have tomorrow?")
            return f"📅 Tomorrow's Homework:\n\n{response}"
        except Exception as e:
            logger.error(f"Error getting tomorrow's homework: {e}")
            return self.formatter.format_error_message("general")

    async def _get_due_dates(self) -> str:
        """Get upcoming due dates."""
        try:
            response = await self.homework_agent.process_question("What homework is due soon?")
            return f"⏰ Upcoming Due Dates:\n\n{response}"
        except Exception as e:
            logger.error(f"Error getting due dates: {e}")
            return self.formatter.format_error_message("general")

    async def _get_todays_homework(self) -> str:
        """Get today's homework."""
        try:
            response = await self.homework_agent.process_question("What homework do I have today?")
            return f"📅 Today's Homework:\n\n{response}"
        except Exception as e:
            logger.error(f"Error getting today's homework: {e}")
            return self.formatter.format_error_message("general")

    def _get_welcome_message(self) -> str:
        """Generate welcome message."""
        return """🎓 *Welcome to Homework Agent!* 

I'm here to help you stay on top of your assignments! 📚

*Quick Commands:*
• `today` - Today's homework
• `tomorrow` - Tomorrow's homework  
• `due` - Upcoming due dates
• `help` - Show all commands

*Ask me naturally:*
• "What math homework do I have?"
• "When is my science project due?"
• "Show me homework for Friday"
• "Do I have any English assignments?"

Just type your question and I'll help! 🤖✨"""

    def _get_help_message(self) -> str:
        """Generate help message."""
        return """📖 *Homework Agent Commands*

*Quick Commands:*
• `today` - Show today's homework
• `tomorrow` - Show tomorrow's homework
• `due` - Show upcoming due dates
• `help` - Show this help message

*Natural Questions:*
• "What homework do I have for [subject]?"
• "When is my [assignment] due?"
• "Show me homework for [day/date]"
• "Do I have any assignments this week?"

*Examples:*
• "Math homework for tomorrow"
• "Science assignments due this week"
• "What's due on Friday?"
• "Show me all English homework"

Just ask me naturally - I understand! 🤖💭"""


# Create FastAPI app
def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Homework Agent WhatsApp Service",
        description="WhatsApp integration for homework management",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app


# Initialize app and service
app = create_app()
whatsapp_service = EnhancedWhatsAppService()


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request, From: str = Form(), Body: str = Form()):
    """Webhook endpoint for receiving WhatsApp messages from Twilio."""
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
        resp.message(whatsapp_service.formatter.format_error_message("general"))
        return PlainTextResponse(content=str(resp), media_type="application/xml")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy", 
        "service": "homework-agent-whatsapp",
        "twilio_available": TWILIO_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/send-message")
async def send_message_endpoint(to_number: str, message: str):
    """API endpoint to send WhatsApp messages programmatically."""
    try:
        success = await whatsapp_service.send_message(to_number, message)
        return {"success": success, "to": to_number, "message": message[:100]}
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """Get service statistics."""
    return {
        "active_users": len(whatsapp_service.user_sessions),
        "total_sessions": len(whatsapp_service.user_sessions),
        "service_uptime": datetime.now().isoformat()
    }


if __name__ == "__main__":
    settings = get_whatsapp_settings()
    
    uvicorn.run(
        app,
        host=settings.webhook_host,
        port=settings.webhook_port,
        log_level=settings.log_level.lower()
    )