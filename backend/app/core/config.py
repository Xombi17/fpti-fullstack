"""
Configuration settings for the FPTI application.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = "sqlite:///./data/fpti.db"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # API
    api_v1_str: str = "/api/v1"
    project_name: str = "Financial Portfolio Tracking Interface"
    
    # Market Data APIs
    alpha_vantage_api_key: Optional[str] = None
    yahoo_finance_api_key: Optional[str] = None
    market_data_provider: str = "yahoo"  # Options: yahoo, alpha_vantage
    api_rate_limit_per_minute: int = 60
    
    # Application
    debug: bool = True
    
    # Dashboard
    dash_host: str = "127.0.0.1"
    dash_port: int = 8050
    dash_debug: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()