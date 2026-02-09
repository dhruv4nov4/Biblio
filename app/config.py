"""
Configuration management for the AI Builder Platform.
All settings are loaded from environment variables.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    GROQ_API_KEY: str
    
    # Model Configuration (ALL GROQ MODELS as per blueprint)
    GATEKEEPER_MODEL: str = "llama-3.3-70b-versatile"
    ARCHITECT_MODEL: str = "llama-3.3-70b-versatile"
    BUILDER_MODEL: str = "openai/gpt-oss-120b"  # Groq's coding specialist
    # AUDITOR_MODEL: str = "llama-3.3-70b-versatile"
    AUDITOR_MODEL: str = "openai/gpt-oss-120b"
    
    # Rate Limiting
    BUILDER_COOLDOWN_SECONDS: int = 2
    MAX_RETRY_COUNT: int = 2
    
    # Temperature Settings
    GATEKEEPER_TEMPERATURE: float = 0.0
    ARCHITECT_TEMPERATURE: float = 0.3
    BUILDER_TEMPERATURE: float = 0.1
    AUDITOR_TEMPERATURE: float = 0.2
    
    # Output Configuration
    OUTPUT_DIR: str = "./output"
    MAX_FILE_SIZE_MB: int = 5
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()