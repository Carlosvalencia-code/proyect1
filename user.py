"""
Esquemas de usuario para Synthia Style API
Modelos para gestión de usuarios y preferencias
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, date
from enum import Enum

from pydantic import BaseModel, Field, validator, EmailStr
from .common import BaseConfig, TimestampMixin, MetadataMixin


class ProfileVisibility(str, Enum):
    """Opciones de visibilidad del perfil"""
    PRIVATE = "private"
    PUBLIC = "public"
    FRIENDS = "friends"


class SubscriptionTier(str, Enum):
    """Niveles de suscripción"""
    FREE = "FREE"
    PREMIUM = "PREMIUM"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"


class UserRole(str, Enum):
    """Roles de usuario"""
    USER = "USER"
    MODERATOR = "MODERATOR"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"


class SkinTone(str, Enum):
    """Tonos de piel"""
    VERY_LIGHT = "VERY_LIGHT"
    LIGHT = "LIGHT"
    LIGHT_MEDIUM = "LIGHT_MEDIUM"
    MEDIUM = "MEDIUM"
    MEDIUM_DARK = "MEDIUM_DARK"
    DARK = "DARK"
    VERY_DARK = "VERY_DARK"


class HairColor(str, Enum):
    """Colores de cabello"""
    BLONDE = "BLONDE"
    BROWN = "BROWN"
    BLACK = "BLACK"
    RED = "RED"
    GRAY = "GRAY"
    WHITE = "WHITE"
    OTHER = "OTHER"


class EyeColor(str, Enum):
    """Colores de ojos"""
    BLUE = "BLUE"
    GREEN = "GREEN"
    BROWN = "BROWN"
    HAZEL = "HAZEL"
    GRAY = "GRAY"
    AMBER = "AMBER"
    OTHER = "OTHER"


class Gender(str, Enum):
    """Opciones de género"""
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non-binary"
    PREFER_NOT_TO_SAY = "prefer-not-to-say"


class BodyType(str, Enum):
    """Tipos de cuerpo"""
    PEAR = "pear"
    APPLE = "apple"
    HOURGLASS = "hourglass"
    RECTANGLE = "rectangle"
    INVERTED_TRIANGLE = "inverted-triangle"


class BudgetRange(str, Enum):
    """Rangos de presupuesto"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    LUXURY = "luxury"


class Theme(str, Enum):
    """Temas de interfaz"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class ChurnRisk(str, Enum):
    """Nivel de riesgo de abandono"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class UserBase(BaseModel):
    """Schema base para usuario"""
    email: EmailStr = Field(..., description="Email del usuario")
    first_name: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=50,
        description="Nombre"
    )
    last_name: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=50,
        description="Apellido"
    )
    is_active: bool = Field(default=True, description="Usuario activo")
    
    # Nuevos campos básicos
    date_of_birth: Optional[date] = Field(None, description="Fecha de nacimiento")
    gender: Optional[Gender] = Field(None, description="Género")
    location: Optional[str] = Field(None, max_length=100, description="Ubicación")
    skin_tone: Optional[SkinTone] = Field(None, description="Tono de piel")
    hair_color: Optional[HairColor] = Field(None, description="Color de cabello")
    eye_color: Optional[EyeColor] = Field(None, description="Color de ojos")
    
    @validator('email')
    def normalize_email(cls, v):
        return v.lower()
    
    @validator('date_of_birth')
    def validate_birth_date(cls, v):
        if v and v > date.today():
            raise ValueError('La fecha de nacimiento no puede ser futura')
        if v and (date.today() - v).days < 365 * 13:  # Mínimo 13 años
            raise ValueError('Debe ser mayor de 13 años')
        return v
    
    class Config(BaseConfig):
        pass


class UserCreate(UserBase):
    """Schema para creación de usuario"""
    password: str = Field(
        ..., 
        min_length=8, 
        max_length=128,
        description="Contraseña"
    )
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        
        has_letter = any(c.isalpha() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not has_letter:
            raise ValueError('La contraseña debe contener al menos una letra')
        if not has_digit:
            raise ValueError('La contraseña debe contener al menos un número')
        
        return v
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "email": "maria@example.com",
                "password": "miContraseñaSegura123",
                "first_name": "María",
                "last_name": "García"
            }
        }


class UserUpdate(BaseModel):
    """Schema para actualización de usuario"""
    first_name: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=50
    )
    last_name: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=50
    )
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "first_name": "María Isabel",
                "last_name": "García López"
            }
        }


class UserResponse(UserBase, TimestampMixin):
    """Schema para respuesta de usuario (sin password)"""
    id: str = Field(..., description="ID único del usuario")
    preferences: Optional["UserPreferences"] = None
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "id": "user_123456789",
                "email": "maria@example.com",
                "first_name": "María",
                "last_name": "García",
                "is_active": True,
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z"
            }
        }


class UserPreferences(BaseModel, TimestampMixin):
    """Schema para preferencias de usuario"""
    id: str = Field(..., description="ID de las preferencias")
    user_id: str = Field(..., description="ID del usuario")
    
    # Preferencias de notificaciones
    email_notifications: bool = Field(default=True, description="Notificaciones por email")
    push_notifications: bool = Field(default=True, description="Notificaciones push")
    
    # Preferencias de privacidad
    share_analytics: bool = Field(default=False, description="Compartir datos analíticos")
    profile_visibility: ProfileVisibility = Field(
        default=ProfileVisibility.PRIVATE,
        description="Visibilidad del perfil"
    )
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "id": "pref_123456789",
                "user_id": "user_123456789",
                "email_notifications": True,
                "push_notifications": True,
                "share_analytics": False,
                "profile_visibility": "private"
            }
        }


class UserPreferencesUpdate(BaseModel):
    """Schema para actualización de preferencias"""
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    share_analytics: Optional[bool] = None
    profile_visibility: Optional[ProfileVisibility] = None
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "email_notifications": False,
                "push_notifications": True,
                "share_analytics": True,
                "profile_visibility": "public"
            }
        }


class UserStats(BaseModel):
    """Schema para estadísticas de usuario"""
    total_facial_analyses: int = Field(default=0, description="Total de análisis faciales")
    total_chromatic_analyses: int = Field(default=0, description="Total de análisis cromáticos")
    last_analysis_date: Optional[datetime] = Field(None, description="Fecha del último análisis")
    favorite_recommendations: int = Field(default=0, description="Recomendaciones favoritas")
    feedback_count: int = Field(default=0, description="Cantidad de feedback dado")
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "total_facial_analyses": 3,
                "total_chromatic_analyses": 2,
                "last_analysis_date": "2024-01-01T12:00:00Z",
                "favorite_recommendations": 5,
                "feedback_count": 2
            }
        }


class UserProfile(UserResponse):
    """Schema completo del perfil de usuario"""
    preferences: Optional[UserPreferences] = None
    stats: Optional[UserStats] = None
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "id": "user_123456789",
                "email": "maria@example.com",
                "first_name": "María",
                "last_name": "García",
                "is_active": True,
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
                "preferences": {
                    "email_notifications": True,
                    "push_notifications": True,
                    "share_analytics": False,
                    "profile_visibility": "private"
                },
                "stats": {
                    "total_facial_analyses": 3,
                    "total_chromatic_analyses": 2,
                    "favorite_recommendations": 5
                }
            }
        }


class UserSearch(BaseModel):
    """Schema para búsqueda de usuarios"""
    query: str = Field(..., min_length=2, description="Término de búsqueda")
    include_inactive: bool = Field(default=False, description="Incluir usuarios inactivos")
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "query": "maria garcia",
                "include_inactive": False
            }
        }


class UserActivity(BaseModel, TimestampMixin):
    """Schema para actividad de usuario"""
    user_id: str = Field(..., description="ID del usuario")
    activity_type: str = Field(..., description="Tipo de actividad")
    description: str = Field(..., description="Descripción de la actividad")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadatos adicionales")
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "user_id": "user_123456789",
                "activity_type": "facial_analysis",
                "description": "Realizó análisis facial",
                "metadata": {
                    "face_shape": "ovalado",
                    "confidence": 85
                },
                "created_at": "2024-01-01T12:00:00Z"
            }
        }


class UserDeletion(BaseModel):
    """Schema para eliminación de usuario"""
    confirm_deletion: bool = Field(..., description="Confirmar eliminación")
    reason: Optional[str] = Field(None, description="Razón de la eliminación")
    delete_all_data: bool = Field(default=True, description="Eliminar todos los datos")
    
    @validator('confirm_deletion')
    def validate_confirmation(cls, v):
        if not v:
            raise ValueError('Debe confirmar la eliminación')
        return v
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "confirm_deletion": True,
                "reason": "Ya no necesito el servicio",
                "delete_all_data": True
            }
        }


class UserExport(BaseModel):
    """Schema para exportación de datos de usuario"""
    include_analyses: bool = Field(default=True, description="Incluir análisis")
    include_recommendations: bool = Field(default=True, description="Incluir recomendaciones")
    include_feedback: bool = Field(default=True, description="Incluir feedback")
    format: str = Field(default="json", regex="^(json|csv|pdf)$", description="Formato de exportación")
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "include_analyses": True,
                "include_recommendations": True,
                "include_feedback": True,
                "format": "json"
            }
        }


class UserInvitation(BaseModel, TimestampMixin):
    """Schema para invitación de usuario"""
    email: EmailStr = Field(..., description="Email del invitado")
    invited_by: str = Field(..., description="ID del usuario que invita")
    status: str = Field(default="pending", description="Estado de la invitación")
    expires_at: datetime = Field(..., description="Fecha de expiración")
    message: Optional[str] = Field(None, description="Mensaje personalizado")
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "email": "amiga@example.com",
                "invited_by": "user_123456789",
                "status": "pending",
                "expires_at": "2024-01-08T12:00:00Z",
                "message": "¡Te invito a probar Synthia Style!"
            }
        }


class UserNotification(BaseModel, TimestampMixin):
    """Schema para notificaciones de usuario"""
    user_id: str = Field(..., description="ID del usuario")
    title: str = Field(..., description="Título de la notificación")
    message: str = Field(..., description="Mensaje de la notificación")
    type: str = Field(..., description="Tipo de notificación")
    is_read: bool = Field(default=False, description="Notificación leída")
    action_url: Optional[str] = Field(None, description="URL de acción")
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "user_id": "user_123456789",
                "title": "Nuevo análisis disponible",
                "message": "Tu análisis facial ha sido completado",
                "type": "analysis_complete",
                "is_read": False,
                "action_url": "/analysis/results/123"
            }
        }


# ================ NUEVOS MODELOS PARA SISTEMA AVANZADO ================

class UserProfileExtended(BaseModel, TimestampMixin):
    """Perfil extendido del usuario"""
    id: str = Field(..., description="ID del perfil")
    user_id: str = Field(..., description="ID del usuario")
    
    # Información personal adicional
    bio: Optional[str] = Field(None, max_length=500, description="Biografía")
    website: Optional[str] = Field(None, description="Sitio web")
    profession: Optional[str] = Field(None, max_length=100, description="Profesión")
    interests: List[str] = Field(default=[], description="Intereses")
    
    # Preferencias de estilo
    style_preferences: Optional[Dict[str, Any]] = Field(None, description="Preferencias de estilo")
    favorite_colors: List[str] = Field(default=[], description="Colores favoritos")
    fashion_goals: List[str] = Field(default=[], description="Objetivos de moda")
    budget_range: Optional[BudgetRange] = Field(None, description="Rango de presupuesto")
    
    # Información física
    height: Optional[float] = Field(None, gt=0, le=300, description="Altura en cm")
    weight: Optional[float] = Field(None, gt=0, le=500, description="Peso en kg")
    body_type: Optional[BodyType] = Field(None, description="Tipo de cuerpo")
    
    # Redes sociales
    instagram_handle: Optional[str] = Field(None, max_length=30)
    tiktok_handle: Optional[str] = Field(None, max_length=30)
    linkedin_profile: Optional[str] = Field(None)
    
    # Configuración de privacidad
    allow_public_profile: bool = Field(default=False)
    show_stats_publicly: bool = Field(default=False)
    show_recommendations_publicly: bool = Field(default=False)
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "bio": "Apasionada por la moda y el estilo personal",
                "profession": "Diseñadora Gráfica",
                "interests": ["moda", "arte", "fotografía"],
                "favorite_colors": ["azul", "rosa", "blanco"],
                "budget_range": "medium",
                "height": 165.0,
                "body_type": "hourglass"
            }
        }


class UserPreferencesExtended(BaseModel, TimestampMixin):
    """Preferencias extendidas del usuario"""
    id: str = Field(..., description="ID de las preferencias")
    user_id: str = Field(..., description="ID del usuario")
    
    # Notificaciones
    email_notifications: bool = Field(default=True)
    push_notifications: bool = Field(default=True)
    marketing_emails: bool = Field(default=False)
    analysis_reminders: bool = Field(default=True)
    weekly_digest: bool = Field(default=True)
    
    # Privacidad
    share_analytics: bool = Field(default=False)
    profile_visibility: ProfileVisibility = Field(default=ProfileVisibility.PRIVATE)
    show_analysis_history: bool = Field(default=True)
    allow_data_export: bool = Field(default=True)
    data_retention_days: int = Field(default=365, ge=30, le=3650)
    
    # Análisis
    auto_save_results: bool = Field(default=True)
    detailed_recommendations: bool = Field(default=True)
    include_confidence_score: bool = Field(default=True)
    preferred_language: str = Field(default="es", regex="^(es|en|fr|de|it|pt)$")
    
    # Interfaz
    theme: Theme = Field(default=Theme.LIGHT)
    currency: str = Field(default="USD", regex="^[A-Z]{3}$")
    timezone: str = Field(default="UTC")
    
    class Config(BaseConfig):
        pass


class UserAnalyticsData(BaseModel, TimestampMixin):
    """Analytics del usuario"""
    id: str = Field(..., description="ID de analytics")
    user_id: str = Field(..., description="ID del usuario")
    
    # Estadísticas de uso
    total_sessions: int = Field(default=0, ge=0)
    total_time_spent: int = Field(default=0, ge=0, description="Tiempo en minutos")
    average_session_time: float = Field(default=0.0, ge=0.0)
    
    # Análisis realizados
    total_facial_analyses: int = Field(default=0, ge=0)
    total_chromatic_analyses: int = Field(default=0, ge=0)
    most_frequent_analysis_day: Optional[str] = Field(None)
    most_active_hour: Optional[int] = Field(None, ge=0, le=23)
    
    # Engagement
    feedback_given: int = Field(default=0, ge=0)
    recommendations_shared: int = Field(default=0, ge=0)
    profile_views: int = Field(default=0, ge=0)
    
    # Patrones de comportamiento
    preferred_analysis_type: Optional[str] = Field(None)
    average_confidence_score: float = Field(default=0.0, ge=0.0, le=100.0)
    improvement_trend: float = Field(default=0.0)
    
    # Conversión y retención
    onboarding_completion: float = Field(default=0.0, ge=0.0, le=100.0)
    retention_score: float = Field(default=0.0, ge=0.0, le=100.0)
    churn_risk: ChurnRisk = Field(default=ChurnRisk.LOW)
    
    # Datos recientes (30 días)
    recent_analyses: int = Field(default=0, ge=0)
    recent_sessions: int = Field(default=0, ge=0)
    recent_engagement: float = Field(default=0.0, ge=0.0)
    
    # Timing
    last_calculated: datetime = Field(default_factory=datetime.utcnow)
    
    class Config(BaseConfig):
        pass


class UserOnboardingData(BaseModel, TimestampMixin):
    """Datos de onboarding del usuario"""
    id: str = Field(..., description="ID de onboarding")
    user_id: str = Field(..., description="ID del usuario")
    
    # Pasos completados
    welcome_completed: bool = Field(default=False)
    profile_setup_completed: bool = Field(default=False)
    preferences_set_completed: bool = Field(default=False)
    first_analysis_completed: bool = Field(default=False)
    tutorial_completed: bool = Field(default=False)
    
    # Progreso
    current_step: int = Field(default=0, ge=0)
    total_steps: int = Field(default=5, ge=1)
    completion_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    
    # Personalización
    detected_preferences: Optional[Dict[str, Any]] = Field(None)
    initial_style_goals: List[str] = Field(default=[])
    onboarding_path: str = Field(default="standard", regex="^(standard|quick|detailed)$")
    
    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None)
    last_step_completed_at: Optional[datetime] = Field(None)
    time_to_complete: Optional[int] = Field(None, ge=0, description="Minutos para completar")
    
    class Config(BaseConfig):
        pass


class SubscriptionFeaturesData(BaseModel, TimestampMixin):
    """Features disponibles por tier de suscripción"""
    tier: SubscriptionTier = Field(..., description="Tier de suscripción")
    
    # Límites de análisis
    monthly_analysis_limit: int = Field(..., ge=0)
    daily_analysis_limit: int = Field(default=3, ge=0)
    
    # Features principales
    advanced_recommendations: bool = Field(default=False)
    personalized_tips: bool = Field(default=False)
    export_results: bool = Field(default=False)
    priority_support: bool = Field(default=False)
    custom_reports: bool = Field(default=False)
    
    # Features de IA
    detailed_ai_analysis: bool = Field(default=False)
    multiple_photo_analysis: bool = Field(default=False)
    video_analysis: bool = Field(default=False)
    realtime_consultation: bool = Field(default=False)
    
    # Features sociales
    public_profile: bool = Field(default=False)
    share_results: bool = Field(default=False)
    follow_users: bool = Field(default=False)
    
    # Almacenamiento
    history_retention_days: int = Field(default=30, ge=1)
    max_stored_analyses: int = Field(default=10, ge=1)
    
    # Soporte
    live_chat_support: bool = Field(default=False)
    phone_support: bool = Field(default=False)
    personal_stylist_access: bool = Field(default=False)
    
    # Precios
    monthly_price: float = Field(default=0.0, ge=0.0)
    yearly_price: float = Field(default=0.0, ge=0.0)
    currency: str = Field(default="USD")
    
    # Estado
    is_active: bool = Field(default=True)
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "tier": "PREMIUM",
                "monthly_analysis_limit": 25,
                "daily_analysis_limit": 5,
                "advanced_recommendations": True,
                "monthly_price": 9.99,
                "yearly_price": 99.99
            }
        }


class DailyUsageData(BaseModel, TimestampMixin):
    """Datos de uso diario del usuario"""
    id: str = Field(..., description="ID de uso diario")
    user_id: str = Field(..., description="ID del usuario")
    date: date = Field(..., description="Fecha del tracking")
    
    # Contadores de análisis
    facial_analyses_count: int = Field(default=0, ge=0)
    chromatic_analyses_count: int = Field(default=0, ge=0)
    total_analyses_count: int = Field(default=0, ge=0)
    
    # Otras métricas
    sessions_count: int = Field(default=0, ge=0)
    time_spent_minutes: int = Field(default=0, ge=0)
    features_used: List[str] = Field(default=[])
    
    # Límites
    daily_limit_reached: bool = Field(default=False)
    limit_reached_at: Optional[datetime] = Field(None)
    
    class Config(BaseConfig):
        pass


class UserSubscriptionHistory(BaseModel, TimestampMixin):
    """Historial de suscripciones del usuario"""
    id: str = Field(..., description="ID del historial")
    user_id: str = Field(..., description="ID del usuario")
    
    # Detalles de suscripción
    tier: SubscriptionTier = Field(..., description="Tier de suscripción")
    start_date: datetime = Field(..., description="Fecha de inicio")
    end_date: Optional[datetime] = Field(None, description="Fecha de fin")
    is_active: bool = Field(default=True)
    
    # Información de pago
    amount: Optional[float] = Field(None, ge=0.0)
    currency: str = Field(default="USD")
    payment_method: Optional[str] = Field(None)
    transaction_id: Optional[str] = Field(None)
    
    # Contexto del cambio
    change_reason: Optional[str] = Field(None)
    previous_tier: Optional[SubscriptionTier] = Field(None)
    
    class Config(BaseConfig):
        pass


class UserDashboard(BaseModel):
    """Dashboard completo del usuario"""
    user: "UserExtended"
    profile: Optional[UserProfileExtended] = None
    preferences: Optional[UserPreferencesExtended] = None
    analytics: Optional[UserAnalyticsData] = None
    onboarding: Optional[UserOnboardingData] = None
    subscription_features: Optional[SubscriptionFeaturesData] = None
    recent_usage: Optional[DailyUsageData] = None
    
    class Config(BaseConfig):
        pass


class UserExtended(UserBase, TimestampMixin):
    """Usuario extendido con toda la información"""
    id: str = Field(..., description="ID del usuario")
    
    # Información de suscripción
    role: UserRole = Field(default=UserRole.USER)
    subscription_tier: SubscriptionTier = Field(default=SubscriptionTier.FREE)
    subscription_expiry: Optional[datetime] = Field(None)
    
    # Tracking de actividad
    last_active: Optional[datetime] = Field(None)
    onboarding_completed: bool = Field(default=False)
    onboarding_step: int = Field(default=0, ge=0)
    login_count: int = Field(default=0, ge=0)
    
    # Límites de uso
    monthly_analysis_count: int = Field(default=0, ge=0)
    monthly_analysis_limit: int = Field(default=5, ge=0)
    last_analysis_reset: datetime = Field(default_factory=datetime.utcnow)
    
    # Estado
    is_verified: bool = Field(default=False)
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "id": "user_123456789",
                "email": "maria@example.com",
                "first_name": "María",
                "last_name": "García",
                "subscription_tier": "PREMIUM",
                "role": "USER",
                "onboarding_completed": True,
                "is_verified": True
            }
        }


# Esquemas de actualización
class UserProfileUpdate(BaseModel):
    """Schema para actualizar perfil extendido"""
    bio: Optional[str] = Field(None, max_length=500)
    website: Optional[str] = Field(None)
    profession: Optional[str] = Field(None, max_length=100)
    interests: Optional[List[str]] = Field(None)
    favorite_colors: Optional[List[str]] = Field(None)
    fashion_goals: Optional[List[str]] = Field(None)
    budget_range: Optional[BudgetRange] = Field(None)
    height: Optional[float] = Field(None, gt=0, le=300)
    weight: Optional[float] = Field(None, gt=0, le=500)
    body_type: Optional[BodyType] = Field(None)
    instagram_handle: Optional[str] = Field(None, max_length=30)
    tiktok_handle: Optional[str] = Field(None, max_length=30)
    linkedin_profile: Optional[str] = Field(None)
    allow_public_profile: Optional[bool] = Field(None)
    show_stats_publicly: Optional[bool] = Field(None)
    show_recommendations_publicly: Optional[bool] = Field(None)
    
    class Config(BaseConfig):
        pass


class UserAdvancedUpdate(BaseModel):
    """Schema para actualización avanzada de usuario"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    date_of_birth: Optional[date] = Field(None)
    gender: Optional[Gender] = Field(None)
    location: Optional[str] = Field(None, max_length=100)
    skin_tone: Optional[SkinTone] = Field(None)
    hair_color: Optional[HairColor] = Field(None)
    eye_color: Optional[EyeColor] = Field(None)
    
    class Config(BaseConfig):
        pass


# Esquemas de respuesta para onboarding
class OnboardingStepResponse(BaseModel):
    """Respuesta de paso de onboarding"""
    step: int = Field(..., description="Número de paso")
    title: str = Field(..., description="Título del paso")
    description: str = Field(..., description="Descripción del paso")
    is_completed: bool = Field(..., description="Si está completado")
    fields_required: List[str] = Field(default=[], description="Campos requeridos")
    
    class Config(BaseConfig):
        pass


class OnboardingFlowResponse(BaseModel):
    """Respuesta completa del flujo de onboarding"""
    current_step: int = Field(..., description="Paso actual")
    total_steps: int = Field(..., description="Total de pasos")
    completion_percentage: float = Field(..., description="Porcentaje completado")
    steps: List[OnboardingStepResponse] = Field(..., description="Lista de pasos")
    recommended_path: str = Field(..., description="Ruta recomendada")
    
    class Config(BaseConfig):
        pass


# Esquemas para sistema de suscripciones
class SubscriptionUpgrade(BaseModel):
    """Schema para upgrade de suscripción"""
    target_tier: SubscriptionTier = Field(..., description="Tier objetivo")
    payment_method: str = Field(..., description="Método de pago")
    billing_cycle: str = Field(default="monthly", regex="^(monthly|yearly)$")
    
    class Config(BaseConfig):
        pass


class UsageLimitsResponse(BaseModel):
    """Respuesta de límites de uso"""
    current_tier: SubscriptionTier = Field(..., description="Tier actual")
    monthly_analyses_used: int = Field(..., description="Análisis usados este mes")
    monthly_analyses_limit: int = Field(..., description="Límite mensual")
    daily_analyses_used: int = Field(..., description="Análisis usados hoy")
    daily_analyses_limit: int = Field(..., description="Límite diario")
    can_analyze: bool = Field(..., description="Si puede hacer más análisis")
    time_until_reset: Optional[int] = Field(None, description="Minutos hasta reset diario")
    
    class Config(BaseConfig):
        pass


# Actualizar forward references
UserResponse.model_rebuild()
UserProfile.model_rebuild()
UserDashboard.model_rebuild()
