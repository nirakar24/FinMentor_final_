"""
Configuration management for the Financial Coaching Agent.
"""
import os
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # LLM Configuration
    llm_provider: Literal["openai", "gemini"] = "openai"
    openai_api_key: str = ""
    google_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    gemini_model: str = "gemini-1.5-flash"
    
    # External API URLs
    api_base_url: str = "http://localhost:8001"
    
    # API Configuration
    api_timeout: int = 30
    api_max_retries: int = 3
    
    # Logging
    log_level: str = "INFO"
    
    # Feature Flags
    enable_behavior_detection: bool = True
    
    def get_llm_config(self) -> dict:
        """Get LLM configuration based on provider."""
        if self.llm_provider == "openai":
            return {
                "provider": "openai",
                "api_key": self.openai_api_key,
                "model": self.openai_model
            }
        elif self.llm_provider == "gemini":
            return {
                "provider": "gemini",
                "api_key": self.google_api_key,
                "model": self.gemini_model
            }
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")


# Global settings instance
settings = Settings()
