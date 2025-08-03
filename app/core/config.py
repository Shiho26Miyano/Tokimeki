import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App settings
    app_name: str = "Tokimeki FastAPI"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8080
    
    # API settings
    openrouter_api_key: Optional[str] = os.getenv("OPENROUTER_API_KEY")
    openrouter_api_url: str = "https://openrouter.ai/api/v1/chat/completions"
    
    # Redis settings
    redis_url: Optional[str] = None
    cache_enabled: bool = True
    cache_ttl: int = 300  # 5 minutes
    
    # Rate limiting
    rate_limit_per_hour: int = 50
    rate_limit_per_day: int = 200
    
    # CORS settings
    cors_origins: list = ["*"]
    cors_methods: list = ["GET", "POST", "OPTIONS"]
    cors_headers: list = ["Content-Type", "Authorization"]
    
    # ML models
    sentiment_model: str = "distilbert-base-uncased-finetuned-sst-2-english"
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "env_prefix": "",
        "extra": "ignore"
    }

# Global settings instance
settings = Settings()

# Debug: Print API key status
api_key = os.getenv("OPENROUTER_API_KEY")
print(f"Environment API key: {'Set' if api_key else 'Not set'}")
print(f"Settings API key: {'Set' if settings.openrouter_api_key else 'Not set'}")

# Free model configuration
FREE_MODELS = {
    "mistral-small": "mistralai/mistral-small-3.2-24b-instruct:free",
    "deepseek-r1": "deepseek/deepseek-r1-0528:free",
    "deepseek-chat": "deepseek/deepseek-chat-v3-0324:free",
    "llama-3.1-405b": "meta-llama/llama-3.1-405b-instruct:free"
} 