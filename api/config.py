"""
API Configuration

Configuration settings for the APGI REST API.
"""

import os
from typing import List


class Settings:
    """
    API configuration settings.
    
    Settings can be overridden via environment variables.
    """
    
    # API Settings
    api_title: str = "APGI System API"
    api_version: str = "1.0.0"
    api_description: str = "REST API for consciousness modeling"
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    
    # Database Settings
    database_url: str = os.getenv("DATABASE_URL", "postgresql://localhost/apgi_api")
    
    # Redis Settings
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Celery Settings
    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    celery_result_backend: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
    
    # Authentication Settings
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    def __post_init__(self):
        """Validate critical security settings after initialization."""
        # Validate JWT secret key is not the default insecure value
        if self.jwt_secret_key == "your-secret-key-change-in-production":
            raise ValueError(
                "CRITICAL: JWT_SECRET_KEY is not configured. "
                "Set a secure JWT_SECRET_KEY environment variable before starting the API. "
                "The default value is insecure and must not be used in production."
            )
        
        # Validate CORS origins are explicitly configured
        if self.cors_origins == ["*"]:
            raise ValueError(
                "SECURITY WARNING: CORS origins are set to wildcard [*]. "
                "This allows any origin to access the API. "
                "Set CORS_ORIGINS environment variable to specific allowed origins for production."
            )
    
    # Rate Limiting Settings
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60
    
    # CORS Settings
    cors_origins: List[str] = os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") else ["*"]
    cors_allow_credentials: bool = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
    cors_allow_methods: List[str] = os.getenv("CORS_ALLOW_METHODS", "*").split(",") if os.getenv("CORS_ALLOW_METHODS") else ["*"]
    cors_allow_headers: List[str] = os.getenv("CORS_ALLOW_HEADERS", "*").split(",") if os.getenv("CORS_ALLOW_HEADERS") else ["*"]
    
    # Logging Settings
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Schema Validation Settings
    schema_validation_enabled: bool = os.getenv("SCHEMA_VALIDATION_ENABLED", "true").lower() == "true"
    schema_validation_fail_on_error: bool = os.getenv("SCHEMA_VALIDATION_FAIL_ON_ERROR", "false").lower() == "true"
    
    # Alerting Settings
    alert_webhook_urls: List[str] = []  # Can be set via environment
    alert_enable_log_channel: bool = True
    alert_error_rate_threshold: int = int(os.getenv("ALERT_ERROR_RATE_THRESHOLD", "10"))
    alert_error_rate_window_minutes: int = int(os.getenv("ALERT_ERROR_RATE_WINDOW_MINUTES", "1"))
    alert_cooldown_minutes: int = int(os.getenv("ALERT_COOLDOWN_MINUTES", "5"))


# Global settings instance
settings = Settings()
settings.__post_init__()
