"""
Configuración principal de la aplicación Synthia Style
Maneja variables de entorno y configuraciones por entorno
"""

import os
from typing import List, Optional, Union
from functools import lru_cache

from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Información de la aplicación
    APP_NAME: str = "Synthia Style API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Configuración del servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Base de datos
    DATABASE_URL: str
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "synthia_style_db"
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    
    # Seguridad
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # APIs externas
    GEMINI_API_KEY: str
    
    # Configuración de Merchants y Afiliados
    # Amazon Associates API
    AMAZON_AFFILIATE_TAG: Optional[str] = None
    AMAZON_ACCESS_KEY: Optional[str] = None
    AMAZON_SECRET_KEY: Optional[str] = None
    
    # ASOS Affiliate API
    ASOS_AFFILIATE_TAG: Optional[str] = None
    ASOS_API_KEY: Optional[str] = None
    
    # Zara Affiliate
    ZARA_AFFILIATE_TAG: Optional[str] = None
    
    # H&M Affiliate
    HM_AFFILIATE_TAG: Optional[str] = None
    
    # Uniqlo Affiliate
    UNIQLO_AFFILIATE_TAG: Optional[str] = None
    
    # Mango Affiliate
    MANGO_AFFILIATE_TAG: Optional[str] = None
    
    # Shein Affiliate
    SHEIN_AFFILIATE_TAG: Optional[str] = None
    
    # Zalando Affiliate
    ZALANDO_AFFILIATE_TAG: Optional[str] = None
    
    # Configuración de Shopping
    SHOPPING_ENABLED: bool = True
    SHOPPING_CACHE_TTL: int = 3600  # 1 hora
    SHOPPING_MAX_RESULTS_PER_MERCHANT: int = 20
    SHOPPING_CONCURRENT_REQUESTS: int = 5
    SHOPPING_REQUEST_TIMEOUT: int = 30  # segundos
    
    # Configuración de Rate Limiting para Merchants
    MERCHANT_RATE_LIMIT_REQUESTS_PER_MINUTE: int = 30
    MERCHANT_RATE_LIMIT_REQUESTS_PER_DAY: int = 5000
    
    # Configuración de Afiliados
    AFFILIATE_COMMISSION_DEFAULT_RATE: float = 0.05  # 5%
    AFFILIATE_COOKIE_DURATION_DAYS: int = 30
    AFFILIATE_MINIMUM_PAYOUT: float = 25.00
    AFFILIATE_PAYMENT_SCHEDULE: str = "monthly"  # weekly, monthly, quarterly
    
    # Configuración de Tracking
    TRACKING_ENABLED: bool = True
    TRACKING_ANONYMIZE_IP: bool = True
    TRACKING_RETENTION_DAYS: int = 365
    
    # Configuración de archivos
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 16777216  # 16MB
    ALLOWED_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "webp"]
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_HEADERS: List[str] = ["*"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: str = "logs/app.log"
    
    # Redis Configuration
    REDIS_ENABLED: bool = True
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_CONNECT_TIMEOUT: int = 5
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_MAX_CONNECTIONS: int = 20
    
    # Cache TTL Configuration (en segundos)
    CACHE_TTL_SECONDS: int = 3600  # 1 hora - default
    CACHE_ANALYTICS_TTL_SECONDS: int = 1800  # 30 minutos - analytics
    CACHE_USER_SESSION_TTL_SECONDS: int = 86400  # 24 horas - sesiones
    CACHE_AI_ANALYSIS_TTL_SECONDS: int = 604800  # 7 días - análisis IA
    CACHE_CHROMATIC_ANALYSIS_TTL_SECONDS: int = 2592000  # 30 días - análisis cromático
    CACHE_RECOMMENDATIONS_TTL_SECONDS: int = 86400  # 24 horas - recomendaciones
    CACHE_CONFIG_TTL_SECONDS: int = 3600  # 1 hora - configuraciones
    CACHE_SUBSCRIPTION_TTL_SECONDS: int = 1800  # 30 minutos - datos de suscripción
    
    # Cache Compression y Performance
    CACHE_COMPRESSION_ENABLED: bool = True
    CACHE_COMPRESSION_ALGORITHM: str = "lz4"  # lz4, zstd, gzip
    CACHE_COMPRESSION_LEVEL: int = 1
    CACHE_SERIALIZATION_FORMAT: str = "json"  # json, pickle, msgpack
    
    # Cache Features y Behavior
    CACHE_METRICS_ENABLED: bool = True
    CACHE_WARMUP_ENABLED: bool = True
    CACHE_BACKGROUND_REFRESH: bool = True
    CACHE_STALE_WHILE_REVALIDATE: bool = True
    CACHE_NULL_VALUE_TTL: int = 300  # 5 minutos para valores null
    
    # Cache Namespaces
    CACHE_USER_NAMESPACE: str = "user"
    CACHE_ANALYSIS_NAMESPACE: str = "analysis"
    CACHE_RECOMMENDATIONS_NAMESPACE: str = "recommendations"
    CACHE_CONFIG_NAMESPACE: str = "config"
    CACHE_SESSION_NAMESPACE: str = "session"
    
    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    
    # Monitoreo
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_METRICS: bool = False
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Procesar orígenes CORS desde string o lista"""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @validator("ALLOWED_EXTENSIONS", pre=True)
    def assemble_allowed_extensions(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Procesar extensiones permitidas desde string o lista"""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @property
    def database_url_sync(self) -> str:
        """URL de base de datos para conexiones síncronas"""
        return self.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")
    
    @property
    def database_url_async(self) -> str:
        """URL de base de datos para conexiones asíncronas"""
        return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    
    @property
    def is_production(self) -> bool:
        """Verificar si estamos en producción"""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Verificar si estamos en desarrollo"""
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def upload_path(self) -> str:
        """Ruta completa para uploads"""
        return os.path.join(os.getcwd(), self.UPLOAD_DIR)
    
    @property
    def log_path(self) -> str:
        """Ruta completa para logs"""
        return os.path.join(os.getcwd(), self.LOG_FILE)
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Obtener configuración de la aplicación (cached)
    """
    return Settings()


# Configuraciones específicas por entorno
class DevelopmentSettings(Settings):
    """Configuración para desarrollo"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    CORS_ORIGINS: List[str] = ["*"]  # Más permisivo en desarrollo


class ProductionSettings(Settings):
    """Configuración para producción"""
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("SECRET_KEY debe tener al menos 32 caracteres en producción")
        return v


class TestingSettings(Settings):
    """Configuración para testing"""
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql://test:test@localhost:5432/synthia_test_db"
    LOG_LEVEL: str = "ERROR"


def get_settings_by_environment(environment: str = None) -> Settings:
    """
    Obtener configuración basada en el entorno
    """
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "production")
    
    environment = environment.lower()
    
    if environment == "development":
        return DevelopmentSettings()
    elif environment == "testing":
        return TestingSettings()
    else:
        return ProductionSettings()


# Instancia global de configuración
settings = get_settings()
