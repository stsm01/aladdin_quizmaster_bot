"""Application configuration and environment variables"""

import os
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseModel):
    """Application settings"""
    
    # Bot configuration
    bot_token: str = os.getenv("BOT_TOKEN", "your_bot_token_here").strip()
    
    # API configuration
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "5000"))
    
    # Admin API key for question management
    admin_api_key: str = os.getenv("ADMIN_API_KEY", "admin_secret_key_123")
    
    # Application settings
    max_questions_per_quiz: int = 20
    question_timeout_seconds: int = 300  # 5 minutes per question
    
    # Webhook configuration
    webhook_enabled: bool = os.getenv("BOT_WEBHOOK_ENABLED", "false").lower() in ("1", "true", "yes")
    webhook_url: str = os.getenv("WEBHOOK_URL", "").strip()
    webhook_path_prefix: str = os.getenv("WEBHOOK_PATH_PREFIX", "/webhook")
    
    class Config:
        case_sensitive = False

# Global settings instance
settings = Settings()

# No validation needed - running in open mode
