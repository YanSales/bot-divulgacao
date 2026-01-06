"""
Configurações centralizadas do bot de divulgação
"""
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # Ambiente
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    SECRET_KEY: str = Field(min_length=32)
    API_KEY: str = Field(min_length=16)
    
    # Database
    DATABASE_URL: str = Field(default="sqlite:///./bot_marketing.db")
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    
    # Instagram
    INSTAGRAM_USERNAME: Optional[str] = None
    INSTAGRAM_PASSWORD: Optional[str] = None
    INSTAGRAM_ACCESS_TOKEN: Optional[str] = None
    INSTAGRAM_USER_ID: Optional[str] = None
    
    # Facebook
    FACEBOOK_APP_ID: Optional[str] = None
    FACEBOOK_APP_SECRET: Optional[str] = None
    FACEBOOK_PAGE_ID: Optional[str] = None
    FACEBOOK_PAGE_ACCESS_TOKEN: Optional[str] = None
    
    # Twitter
    TWITTER_API_KEY: Optional[str] = None
    TWITTER_API_SECRET: Optional[str] = None
    TWITTER_ACCESS_TOKEN: Optional[str] = None
    TWITTER_ACCESS_SECRET: Optional[str] = None
    TWITTER_BEARER_TOKEN: Optional[str] = None
    
    # TikTok
    TIKTOK_CLIENT_KEY: Optional[str] = None
    TIKTOK_CLIENT_SECRET: Optional[str] = None
    TIKTOK_ACCESS_TOKEN: Optional[str] = None
    TIKTOK_ENABLED: bool = Field(default=False)
    
    # YouTube
    YOUTUBE_CLIENT_ID: Optional[str] = None
    YOUTUBE_CLIENT_SECRET: Optional[str] = None
    YOUTUBE_REFRESH_TOKEN: Optional[str] = None
    
    # WhatsApp (Twilio)
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_WHATSAPP_NUMBER: Optional[str] = None
    WHATSAPP_ENABLED: bool = Field(default=False)
    
    # Azure Storage
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = None
    AZURE_STORAGE_CONTAINER: str = Field(default="bot-media")
    LOCAL_STORAGE_PATH: str = Field(default="./uploads")
    
    # Landing Page
    LP_WEBHOOK_SECRET: Optional[str] = None
    LP_API_URL: Optional[str] = None
    LP_API_KEY: Optional[str] = None
    
    # Rate Limits
    MAX_POSTS_PER_HOUR: int = Field(default=10)
    MAX_COMMENTS_PER_HOUR: int = Field(default=30)
    MAX_MESSAGES_PER_DAY: int = Field(default=100)
    MAX_API_REQUESTS_PER_HOUR: int = Field(default=200)
    
    # Configurações do Bot
    POSTING_TIMES: str = Field(default="07:30,12:30,17:30")
    OPERATION_MODE: str = Field(default="semi-automatic")
    AUTO_ANALYSIS_ENABLED: bool = Field(default=True)
    
    # Monitoramento
    APPLICATIONINSIGHTS_CONNECTION_STRING: Optional[str] = None
    SENTRY_DSN: Optional[str] = None
    LOG_LEVEL: str = Field(default="INFO")
    
    # Segurança
    ENCRYPTION_KEY: Optional[str] = None
    CORS_ORIGINS: str = Field(default="http://localhost:3000,http://localhost:8501")
    
    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[str] = None
    
    @validator("POSTING_TIMES")
    def validate_posting_times(cls, v):
        """Valida formato dos horários"""
        times = [t.strip() for t in v.split(",")]
        for time in times:
            if not len(time.split(":")) == 2:
                raise ValueError(f"Horário inválido: {time}")
        return v
    
    @validator("OPERATION_MODE")
    def validate_operation_mode(cls, v):
        """Valida modo de operação"""
        if v not in ["automatic", "semi-automatic"]:
            raise ValueError("OPERATION_MODE deve ser 'automatic' ou 'semi-automatic'")
        return v
    
    @property
    def posting_times_list(self) -> List[str]:
        """Retorna lista de horários de publicação"""
        return [t.strip() for t in self.POSTING_TIMES.split(",")]
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Retorna lista de origens CORS"""
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]
    
    @property
    def is_production(self) -> bool:
        """Verifica se está em produção"""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """Verifica se está em desenvolvimento"""
        return self.ENVIRONMENT == "development"
    
    @property
    def use_azure_storage(self) -> bool:
        """Verifica se deve usar Azure Storage"""
        return bool(self.AZURE_STORAGE_CONNECTION_STRING)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Instância global das configurações
settings = Settings()


# Configurações de plataformas habilitadas
ENABLED_PLATFORMS = {
    'instagram': bool(settings.INSTAGRAM_ACCESS_TOKEN),
    'facebook': bool(settings.FACEBOOK_PAGE_ACCESS_TOKEN),
    'twitter': bool(settings.TWITTER_API_KEY),
    'tiktok': settings.TIKTOK_ENABLED and bool(settings.TIKTOK_ACCESS_TOKEN),
    'youtube': bool(settings.YOUTUBE_CLIENT_ID),
    'whatsapp': settings.WHATSAPP_ENABLED and bool(settings.TWILIO_ACCOUNT_SID),
}


# Diretórios importantes
BASE_DIR = Path(__file__).parent.parent
LOGS_DIR = BASE_DIR / "logs"
UPLOADS_DIR = BASE_DIR / "uploads"
TEMP_DIR = BASE_DIR / "temp"

# Criar diretórios se não existirem
for directory in [LOGS_DIR, UPLOADS_DIR, TEMP_DIR]:
    directory.mkdir(exist_ok=True, parents=True)