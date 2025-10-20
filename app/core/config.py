import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App settings
    app_name: str = "Tokimeki FastAPI"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
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
    
    # FutureQuant Trader settings
    futurequant_database_url: Optional[str] = os.getenv("FUTUREQUANT_DATABASE_URL")
    mlflow_tracking_uri: Optional[str] = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    mlflow_registry_uri: Optional[str] = os.getenv("MLFLOW_REGISTRY_URI", "http://localhost:5000")
    
    # BRPC Configuration
    BRPC_ENABLED: bool = True
    BRPC_SERVER_ADDRESS: str = "localhost:8001"
    BRPC_SERVICE_NAME: str = "futurequant_service"
    BRPC_TIMEOUT: int = 5000  # milliseconds
    BRPC_MAX_RETRIES: int = 3
    
    # Mini Golf Strategy settings
    golfcourse_api_key: Optional[str] = os.getenv("GOLFCOURSE_API_KEY")
    golfcourse_api_base: str = "https://api.golfcourseapi.com"
    
    # Weather API settings
    openweather_api_key: Optional[str] = os.getenv("OPENWEATHER_API_KEY")
    
    # Polygon API settings (for AAPL Analysis Dashboard)
    polygon_api_key: Optional[str] = os.getenv("POLYGON_API_KEY")
    
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

# OpenRouter model configuration - using paid models to avoid rate limits
OPENROUTER_MODELS = {
    "mistral-small": "mistralai/mistral-small-3.2-24b-instruct",
    "deepseek-chat": "deepseek/deepseek-chat-v3-0324", 
    "claude-haiku": "anthropic/claude-3-haiku-20240307",
    "gpt-4o-mini": "openai/gpt-4o-mini-2024-07-18",
    "llama-3.1-8b": "meta-llama/llama-3.1-8b-instruct",
    "qwen-2.5-7b": "qwen/qwen-2.5-7b-instruct"
} 