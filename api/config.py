"""
API Configuration

Configuration settings for the APGI REST API.
"""

import os
import warnings
from typing import List

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """
    API configuration settings.

    Settings can be overridden via environment variables.
    """

    def __init__(self):
        # API Settings
        self.api_title: str = "APGI System API"
        self.api_version: str = "1.0.0"
        self.api_description: str = "REST API for consciousness modeling"

        # Server Settings
        self.host: str = "0.0.0.0"
        self.port: int = 8000
        self.reload: bool = True

        # Database Settings
        self.database_url: str = os.getenv("DATABASE_URL", "postgresql://localhost/apgi_api")

        # Redis Settings
        self.redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        # Celery Settings
        self.celery_broker_url: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
        self.celery_result_backend: str = os.getenv(
            "CELERY_RESULT_BACKEND", "redis://localhost:6379/2"
        )

        # Authentication Settings
        self.jwt_secret_key: str = os.getenv("JWT_SECRET_KEY")
        self.environment: str = os.getenv("ENVIRONMENT", "development")
        self.jwt_algorithm: str = "HS256"
        self.jwt_access_token_expire_minutes: int = 30
        self.jwt_refresh_token_expire_days: int = 7

        # Rate Limiting Settings
        self.rate_limit_enabled: bool = True
        self.rate_limit_per_minute: int = 60

        # CORS Settings
        self.cors_origins: List[str] = (
            os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") else ["*"]
        )
        self.cors_allow_credentials: bool = (
            os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
        )
        self.cors_allow_methods: List[str] = (
            os.getenv("CORS_ALLOW_METHODS", "*").split(",")
            if os.getenv("CORS_ALLOW_METHODS")
            else ["*"]
        )
        self.cors_allow_headers: List[str] = (
            os.getenv("CORS_ALLOW_HEADERS", "*").split(",")
            if os.getenv("CORS_ALLOW_HEADERS")
            else ["*"]
        )

        # Logging Settings
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")

        # Schema Validation Settings
        self.schema_validation_enabled: bool = (
            os.getenv("SCHEMA_VALIDATION_ENABLED", "true").lower() == "true"
        )
        self.schema_validation_fail_on_error: bool = (
            os.getenv("SCHEMA_VALIDATION_FAIL_ON_ERROR", "false").lower() == "true"
        )

        # Alerting Settings
        self.alert_webhook_urls: List[str] = []  # Can be set via environment
        self.alert_enable_log_channel: bool = True
        self.alert_error_rate_threshold: int = int(os.getenv("ALERT_ERROR_RATE_THRESHOLD", "10"))
        self.alert_error_rate_window_minutes: int = int(
            os.getenv("ALERT_ERROR_RATE_WINDOW_MINUTES", "1")
        )
        self.alert_cooldown_minutes: int = int(os.getenv("ALERT_COOLDOWN_MINUTES", "5"))

        # Validate security settings after initialization
        self.__post_init__()

    def __post_init__(self):
        """Validate critical security settings after initialization."""
        # Handle JWT secret key for development vs production
        if not self.jwt_secret_key:
            if self.environment.lower() in ["production", "prod"]:
                raise ValueError(
                    "CRITICAL: JWT_SECRET_KEY environment variable is not set for production. "
                    "This is required for secure JWT token generation. "
                    "Set a secure JWT_SECRET_KEY environment variable before starting the API."
                )
            else:
                # Development mode - provide a secure default with warning
                self.jwt_secret_key = "development-secret-key-change-in-production-32-chars-min"
                warnings.warn(
                    "DEVELOPMENT WARNING: JWT_SECRET_KEY not set, using development default. "
                    "This is insecure and should NOT be used in production. "
                    "Set JWT_SECRET_KEY environment variable for production deployment. "
                    "Copy .env.example to .env and configure your settings.",
                    UserWarning,
                )

        # Check for known insecure default values
        insecure_defaults = [
            "your-secret-key-change-in-production",
            "secret",
            "default-secret",
            "change-me",
            "insecure-key",
        ]

        if self.jwt_secret_key.lower() in [d.lower() for d in insecure_defaults]:
            if self.environment.lower() in ["production", "prod"]:
                raise ValueError(
                    "CRITICAL: JWT_SECRET_KEY is set to a known insecure default value in production. "
                    "This allows attackers to forge JWT tokens and bypass authentication. "
                    "Set a secure, random JWT_SECRET_KEY environment variable."
                )
            else:
                warnings.warn(
                    "DEVELOPMENT WARNING: JWT_SECRET_KEY is set to a known insecure default value. "
                    "This should be changed before any production deployment. "
                    "Set a secure JWT_SECRET_KEY environment variable.",
                    UserWarning,
                )

        # Validate minimum key length
        if len(self.jwt_secret_key) < 32:
            if self.environment.lower() in ["production", "prod"]:
                raise ValueError(
                    "CRITICAL: JWT_SECRET_KEY is shorter than 32 characters in production. "
                    "Short keys are vulnerable to brute force attacks. "
                    "Use a secure, random key with at least 32 characters."
                )
            else:
                warnings.warn(
                    "DEVELOPMENT WARNING: JWT_SECRET_KEY is shorter than 32 characters. "
                    "This should be fixed before production deployment. "
                    "Use a secure, random key with at least 32 characters.",
                    UserWarning,
                )

        # Validate CORS origins are explicitly configured
        if self.cors_origins == ["*"]:
            if self.cors_allow_credentials:
                raise ValueError(
                    "CRITICAL SECURITY: CORS origins are set to wildcard [*] with credentials enabled. "
                    "This allows any origin to access the API with credentials, enabling CSRF attacks. "
                    "Either set CORS_ORIGINS to specific allowed origins, or set CORS_ALLOW_CREDENTIALS=false."
                )
            else:
                warnings.warn(
                    "SECURITY WARNING: CORS origins are set to wildcard [*]. "
                    "This allows any origin to access the API. "
                    "Set CORS_ORIGINS environment variable to specific allowed origins for production."
                )


# Global settings instance
settings = Settings()
