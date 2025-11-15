"""
Quick setup script for WhatsApp service
"""
import os
import subprocess
import sys
from pathlib import Path


def install_dependencies():
    """Install required dependencies for WhatsApp service."""
    dependencies = [
        "twilio",
        "python-dotenv",
        "fastapi[all]",
        "uvicorn[standard]",
    ]
    
    print("📦 Installing WhatsApp service dependencies...")
    
    for dep in dependencies:
        print(f"Installing {dep}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✅ {dep} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {dep}: {e}")
            return False
    
    return True


def setup_env_file():
    """Setup environment file for WhatsApp service."""
    env_file = Path(".env")
    
    if env_file.exists():
        print("📄 .env file already exists")
        return
    
    print("📝 Creating .env file...")
    
    env_content = """# WhatsApp Service Configuration

# Twilio WhatsApp API Credentials (Get these from Twilio Console)
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

# Rate Limiting (messages per user)
WHATSAPP_RATE_LIMIT_PER_MINUTE=10
WHATSAPP_RATE_LIMIT_PER_HOUR=100

# Logging
WHATSAPP_LOG_LEVEL=INFO
"""
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Created .env file at {env_file.absolute()}")


def print_setup_instructions():
    """Print setup instructions for the user."""
    instructions = """
🎉 WhatsApp Service Setup Complete!

📋 Next Steps:

1. 📱 Set up Twilio WhatsApp:
   - Go to https://console.twilio.com/
   - Create a new account or log in
   - Navigate to WhatsApp > Senders
   - Get your Account SID and Auth Token
   - Update the .env file with your credentials

2. 🔧 Configure Webhook:
   - In Twilio Console, set your webhook URL to:
     http://your-server-url:8080/webhook/whatsapp
   - For local development, use ngrok:
     ngrok http 8080
     Then use: https://your-ngrok-url.ngrok.io/webhook/whatsapp

3. 🚀 Start the service:
   python whatsapp_service/main.py

4. 📱 Test with WhatsApp:
   - Send a message to your Twilio WhatsApp number
   - Try commands like "hi", "today", "help"

🔗 Useful Links:
- Twilio Console: https://console.twilio.com/
- Ngrok: https://ngrok.com/
- WhatsApp API Docs: https://www.twilio.com/docs/whatsapp

📝 Configuration file: .env (update with your Twilio credentials)
"""
    print(instructions)


def main():
    """Main setup function."""
    print("🚀 Setting up WhatsApp Service for Homework Agent...")
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        return
    
    # Setup environment file
    setup_env_file()
    
    # Print instructions
    print_setup_instructions()


if __name__ == "__main__":
    main()