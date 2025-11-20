"""
Lambda-specific configuration settings.
These settings override the local development settings for AWS Lambda environment.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
import os

class LambdaSettings(BaseSettings):
    """Configuration for Lambda environment."""
    
    model_config = SettingsConfigDict(
        env_prefix="HW_", 
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Scraper credentials (from Lambda environment variables)
    username: str | None = None
    password: SecretStr | None = None
    
    # Scraper URLs and selectors (from Lambda environment variables)
    login_url: str = "https://webtop.smartschool.co.il/account/login"
    username_selector: str = "#userName"
    password_selector: str = "input[formcontrolname='password'][type='password']"
    submit_selector: str = "button[type=submit]"
    historical_url: str = "https://webtop.smartschool.co.il/Student_Card/11"
    
    # DynamoDB settings
    dynamodb_table_name: str = "homework-items"
    aws_region: str = "us-east-1"
    
    # Anthropic API key (if using Claude for processing)
    anthropic_api_key: SecretStr | None = None
    
    # Browser settings for Lambda
    headless: bool = True
    timeout: int = 30000
    
    @classmethod
    def for_lambda(cls) -> "LambdaSettings":
        """Create settings optimized for Lambda environment."""
        return cls(
            # Override any local settings
            headless=True,
            timeout=30000,
            # Pull from environment variables set in Lambda
            username=os.environ.get('HW_USERNAME'),
            password=os.environ.get('HW_PASSWORD'),
            dynamodb_table_name=os.environ.get('DYNAMODB_TABLE_NAME', 'homework-items'),
            aws_region=os.environ.get('AWS_REGION', 'us-east-1'),
            login_url=os.environ.get('LOGIN_URL', "https://webtop.smartschool.co.il/account/login"),
            username_selector=os.environ.get('USERNAME_SELECTOR', "#userName"),
            password_selector=os.environ.get('PASSWORD_SELECTOR', "input[formcontrolname='password'][type='password']"),
            submit_selector=os.environ.get('SUBMIT_SELECTOR', "button[type=submit]"),
            historical_url=os.environ.get('HISTORICAL_URL', "https://webtop.smartschool.co.il/Student_Card/11"),
            anthropic_api_key=os.environ.get('ANTHROPIC_API_KEY')
        )

# For Lambda environment, use lambda settings
if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
    settings = LambdaSettings.for_lambda()
else:
    # For local development, use original settings
    from .config import settings