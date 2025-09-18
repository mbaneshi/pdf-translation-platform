import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "PDF Translation Platform"
    VERSION: str = "1.0.0"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/pdftr")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # OpenAI (legacy completions + chat)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo-instruct")
    OPENAI_CHAT_MODEL: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

    # Feature flags
    USE_CHUNKING: bool = os.getenv("USE_CHUNKING", "false").lower() in {"1", "true", "yes"}

    # Optional pricing (USD per 1M tokens)
    OPENAI_PRICING_INPUT_PER_M: float = float(os.getenv("OPENAI_PRICING_INPUT_PER_M", "1.50"))
    OPENAI_PRICING_OUTPUT_PER_M: float = float(os.getenv("OPENAI_PRICING_OUTPUT_PER_M", "2.00"))
    
    # File Storage
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    class Config:
        case_sensitive = True

settings = Settings()
