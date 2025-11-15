# WhatsApp Service for Homework Agent

This module provides WhatsApp integration for the Homework Agent, allowing users to interact with the homework system through WhatsApp messages.

## Features

🎯 **Smart Question Processing**: Natural language understanding for homework queries
📱 **WhatsApp Integration**: Full Twilio WhatsApp API integration  
⚡ **Rate Limiting**: Prevents spam with configurable limits
🔒 **Secure**: Webhook verification and authentication
📊 **Rich Formatting**: Formatted responses with emojis and structure
🤖 **Command Support**: Quick commands for common queries

## Quick Start

### 1. Install Dependencies

```bash
pip install twilio python-dotenv fastapi uvicorn
```

Or run the setup script:
```bash
python setup_whatsapp.py
```

### 2. Setup Twilio WhatsApp

1. Create a [Twilio account](https://console.twilio.com/)
2. Go to WhatsApp > Senders
3. Get your Account SID and Auth Token
4. Update the `.env` file with your credentials

### 3. Configure Environment

Update `.env` file:
```env
WHATSAPP_TWILIO_ACCOUNT_SID=your_account_sid
WHATSAPP_TWILIO_AUTH_TOKEN=your_auth_token
WHATSAPP_TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

### 4. Start the Service

```bash
python whatsapp_service/main.py
```

The service will run on `http://localhost:8080`

### 5. Setup Webhook

#### For Production:
Set webhook URL in Twilio Console to:
```
https://your-domain.com/webhook/whatsapp
```

#### For Development (using ngrok):
```bash
# Install ngrok: https://ngrok.com/
ngrok http 8080
# Use the https URL: https://abc123.ngrok.io/webhook/whatsapp
```

## Usage

### Quick Commands

- `hi` - Welcome message
- `today` - Today's homework
- `tomorrow` - Tomorrow's homework
- `due` - Upcoming due dates
- `help` - Show help message

### Natural Questions

Users can ask questions naturally:

- "What homework do I have for math?"
- "When is my science project due?"
- "Show me homework for Friday"
- "Do I have any English assignments?"

### Example Conversation

```
User: hi
Bot: 🎓 Welcome to Homework Agent! 
     I can help you with your homework questions...

User: today
Bot: 📅 Today's Homework:
     📖 Math: Complete exercises 1-10
     📖 Science: Read chapter 5

User: when is my math homework due?
Bot: ⏰ Your math exercises are due tomorrow (Nov 16)
```

## Service Architecture

```
whatsapp_service/
├── __init__.py              # Package initialization
├── main.py                  # Main entry point
├── enhanced_service.py      # Core WhatsApp service logic
├── config.py               # Configuration settings
├── rate_limiter.py         # Rate limiting functionality
├── message_formatter.py    # Message formatting utilities
└── README.md              # This file
```

## API Endpoints

### Webhook
- `POST /webhook/whatsapp` - Receives WhatsApp messages from Twilio

### Utility Endpoints
- `GET /health` - Service health check
- `GET /stats` - Service statistics
- `POST /send-message` - Send message programmatically

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `WHATSAPP_TWILIO_ACCOUNT_SID` | Twilio Account SID | Required |
| `WHATSAPP_TWILIO_AUTH_TOKEN` | Twilio Auth Token | Required |
| `WHATSAPP_TWILIO_WHATSAPP_NUMBER` | Twilio WhatsApp Number | whatsapp:+14155238886 |
| `WHATSAPP_WEBHOOK_HOST` | Server host | 0.0.0.0 |
| `WHATSAPP_WEBHOOK_PORT` | Server port | 8080 |
| `WHATSAPP_RATE_LIMIT_PER_MINUTE` | Messages per minute per user | 10 |
| `WHATSAPP_RATE_LIMIT_PER_HOUR` | Messages per hour per user | 100 |
| `WHATSAPP_LOG_LEVEL` | Logging level | INFO |

## Development Mode

The service can run in development mode without Twilio credentials:

```bash
# Set mock mode
export WHATSAPP_TWILIO_ACCOUNT_SID=""
export WHATSAPP_TWILIO_AUTH_TOKEN=""

python whatsapp_service/main.py
```

In this mode, messages will be logged instead of sent via WhatsApp.

## Rate Limiting

The service includes built-in rate limiting to prevent abuse:

- **Per-minute limit**: 10 messages per user per minute
- **Per-hour limit**: 100 messages per user per hour

Rate-limited users receive a friendly message asking them to wait.

## Security Features

- **Webhook verification** (configurable)
- **Rate limiting** per user
- **Input sanitization**
- **Error handling** with user-friendly messages

## Troubleshooting

### Common Issues

1. **"Twilio not installed"**
   ```bash
   pip install twilio
   ```

2. **"Authentication error"**
   - Check your Twilio Account SID and Auth Token
   - Ensure they're correctly set in the .env file

3. **"Webhook not receiving messages"**
   - Verify webhook URL in Twilio Console
   - Check that the service is running and accessible
   - For local development, use ngrok

4. **"Rate limited"**
   - Users exceeded message limits
   - Limits reset automatically
   - Adjust limits in configuration if needed

### Debugging

Enable debug logging:
```env
WHATSAPP_LOG_LEVEL=DEBUG
```

Check logs for detailed information about message processing.

## Integration with Homework Agent

The WhatsApp service integrates seamlessly with the existing homework agent:

1. **Uses existing agent**: Leverages `agent/agent.py` for question processing
2. **Database integration**: Accesses homework data through existing DB layer
3. **LLM integration**: Uses configured LLM for intelligent responses
4. **Consistent responses**: Maintains same logic as other interfaces

## Extending the Service

### Adding New Commands

1. Add command handling in `enhanced_service.py`:
```python
elif message_lower in ['new_command', '/new']:
    return await self._handle_new_command(message_body)
```

2. Implement the handler:
```python
async def _handle_new_command(self, message: str) -> str:
    # Your command logic here
    return "Command response"
```

### Custom Message Formatting

Extend `message_formatter.py` for custom formatting:

```python
@staticmethod
def format_custom_response(data) -> str:
    # Custom formatting logic
    return formatted_message
```

## Production Deployment

### Using Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "whatsapp_service/main.py"]
```

### Using systemd

Create service file `/etc/systemd/system/homework-whatsapp.service`:
```ini
[Unit]
Description=Homework Agent WhatsApp Service
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/homework-agent-2
ExecStart=/usr/bin/python3 whatsapp_service/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Support

For issues or questions:

1. Check the troubleshooting section
2. Review Twilio WhatsApp documentation
3. Check service logs for error details
4. Verify webhook configuration

## License

This WhatsApp service is part of the Homework Agent project.