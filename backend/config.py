"""
Configuration file for backend service
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings."""

    # API configuration
    APP_NAME: str = "NLP Sentiment Analysis Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False") == "True"

    # Deployment endpoints
    LAMBDA_ENDPOINT: str = os.getenv(
        "LAMBDA_ENDPOINT"
    )
    KUBERNETES_ENDPOINT: Optional[str] = os.getenv(
        "KUBERNETES_ENDPOINT",
        None
    )
    # TODO: Provide kubernetes settings when deployed

    # Retry configuration
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    INITIAL_BACKOFF: float = float(os.getenv("INITIAL_BACKOFF", "5"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "35"))

    # Server configurations
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: str = int(os.getenv("PORT", "8000"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO") 

settings = Settings()