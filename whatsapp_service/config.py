"""
Configuration settings for WhatsApp Service
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class WhatsAppSettings(BaseSettings):
    """Settings for WhatsApp service configuration."""
    
    # Twilio settings
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_whatsapp_number: str = "whatsapp:+14155238886"  # Twilio Sandbox number
    
    # Server settings
    webhook_host: str = "0.0.0.0"
    webhook_port: int = 8080
    webhook_path: str = "/webhook/whatsapp"
    
    # Security settings
    verify_webhook: bool = True
    webhook_secret: Optional[str] = None
    
    # Rate limiting
    rate_limit_per_minute: int = 10
    rate_limit_per_hour: int = 100
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_prefix = "WHATSAPP_"
        case_sensitive = False


def get_whatsapp_settings() -> WhatsAppSettings:
    """Get WhatsApp service settings."""
    return WhatsAppSettings()