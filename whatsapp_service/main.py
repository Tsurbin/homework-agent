"""
Main entry point for WhatsApp service
"""
import os
import sys
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from whatsapp_service.enhanced_service import app, whatsapp_service
from whatsapp_service.config import get_whatsapp_settings
import uvicorn
from loguru import logger


def setup_environment():
    """Setup environment variables and configuration."""
    env_file = project_root / ".env"
    
    if not env_file.exists():
        logger.info("Creating .env file template...")
        create_env_template(env_file)
        
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv(env_file)


def create_env_template(env_file: Path):
    """Create a template .env file with WhatsApp configuration."""
    template = """# WhatsApp Service Configuration

# Twilio WhatsApp API Credentials (Required for production)
WHATSAPP_TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
WHATSAPP_TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
WHATSAPP_TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Server Configuration
WHATSAPP_WEBHOOK_HOST=0.0.0.0
WHATSAPP_WEBHOOK_PORT=8080
WHATSAPP_WEBHOOK_PATH=/webhook/whatsapp

# Security
WHATSAPP_VERIFY_WEBHOOK=true
WHATSAPP_WEBHOOK_SECRET=your_webhook_secret_here

# Rate Limiting
WHATSAPP_RATE_LIMIT_PER_MINUTE=10
WHATSAPP_RATE_LIMIT_PER_HOUR=100

# Logging
WHATSAPP_LOG_LEVEL=INFO
"""
    
    with open(env_file, 'w') as f:
        f.write(template)
    
    print(f"✅ Created .env template at {env_file}")
    print("📝 Please update the Twilio credentials in the .env file")


def main():
    """Main entry point for WhatsApp service."""
    setup_environment()
    
    settings = get_whatsapp_settings()
    
    logger.info("🚀 Starting Homework Agent WhatsApp Service...")
    logger.info(f"📱 Service will run on {settings.webhook_host}:{settings.webhook_port}")
    logger.info(f"🔗 Webhook URL: http://{settings.webhook_host}:{settings.webhook_port}{settings.webhook_path}")
    
    # Check Twilio credentials
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        logger.warning("⚠️  Twilio credentials not configured. Running in development mode.")
        logger.info("📝 Update WHATSAPP_TWILIO_ACCOUNT_SID and WHATSAPP_TWILIO_AUTH_TOKEN in .env")
    else:
        logger.info("✅ Twilio credentials configured")
    
    try:
        uvicorn.run(
            app,
            host=settings.webhook_host,
            port=settings.webhook_port,
            log_level=settings.log_level.lower(),
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("👋 Shutting down WhatsApp service...")
    except Exception as e:
        logger.error(f"❌ Error starting service: {e}")


if __name__ == "__main__":
    main()