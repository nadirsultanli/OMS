"""Configuration module for the application"""

from typing import Optional
from decouple import config as env_config


class Settings:
    """Application settings loaded from environment variables"""
    
    def __init__(self):
        # Database settings
        self.supabase_url: str = env_config("SUPABASE_URL", default="")
        self.supabase_key: str = env_config("SUPABASE_KEY", default="") or env_config("SUPABASE_ANON_KEY", default="")
        self.supabase_service_role_key: Optional[str] = env_config("SUPABASE_SERVICE_ROLE_KEY", default=None)
        self.database_url: Optional[str] = env_config("DATABASE_URL", default=None)
        self.supabase_db_password: Optional[str] = env_config("SUPABASE_DB_PASSWORD", default=None)
        
        # JWT settings
        self.jwt_secret_key: str = env_config("JWT_SECRET_KEY", default="your-secret-key-here")
        self.jwt_algorithm: str = env_config("JWT_ALGORITHM", default="HS256")
        self.jwt_expiration_hours: int = env_config("JWT_EXPIRATION_HOURS", default=24, cast=int)
        
        # Application settings
        self.app_name: str = env_config("APP_NAME", default="OMS Backend")
        debug_env = env_config("DEBUG", default="false")
        self.debug: bool = debug_env.lower() in ("true", "1", "yes", "on")
        self.environment: str = env_config("ENVIRONMENT", default="development")
        
        # Google OAuth settings
        self.google_client_id: Optional[str] = env_config("GOOGLE_CLIENT_ID", default=None)
        self.google_client_secret: Optional[str] = env_config("GOOGLE_CLIENT_SECRET", default=None)
        
        # Railway settings
        railway_env = env_config("RAILWAY_ENVIRONMENT", default="false")
        self.railway_environment: bool = railway_env.lower() in ("true", "1", "yes", "on")
        
        # CORS settings
        self.allowed_origins: list = env_config("ALLOWED_ORIGINS", default="http://localhost:3000,http://localhost:8080", cast=lambda x: x.split(","))
        
        # Stripe settings
        self.stripe_secret_key: Optional[str] = env_config("STRIPE_SECRET_KEY", default=None)
        self.stripe_publishable_key: Optional[str] = env_config("STRIPE_PUBLISHABLE_KEY", default=None)
        self.stripe_webhook_secret: Optional[str] = env_config("STRIPE_WEBHOOK_SECRET", default=None)
        
        # Logging settings
        self.log_level: str = env_config("LOG_LEVEL", default="INFO")
        
        # Email settings
        self.smtp_server: Optional[str] = env_config("SMTP_SERVER", default=None)
        self.smtp_port: int = env_config("SMTP_PORT", default=587, cast=int)
        self.smtp_username: Optional[str] = env_config("SMTP_USERNAME", default=None)
        self.smtp_password: Optional[str] = env_config("SMTP_PASSWORD", default=None)


# Global settings instance
settings = Settings()