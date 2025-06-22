"""
Esquemas para feedback en Synthia Style API
Modelos para comentarios, valoraciones y sugerencias de usuarios
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, validator
from .common import BaseConfig, TimestampMixin, MetadataMixin


class FeedbackCategory(str, Enum):
    """Categorías de feedback"""
    FACIAL_ANALYSIS = "facial_analysis"
    CHROMATIC_ANALYSIS = "chromatic_analysis"
    RECOMMENDATIONS = "recommendations"
    USER_EXPERIENCE = "user_experience"
    TECHNICAL_ISSUE = "technical_issue"
    FEATURE_REQUEST = "feature_request"
    GENERAL = "general"
    BUG_REPORT = "bug_report"


class FeedbackStatus(str, Enum):
    """Estados del feedback"""
    PENDING = "pending"
    REVIEWED = "reviewed"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REJECTED = "rejected"


class FeedbackPriority(str, Enum):
    """Prioridades del feedback"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FeedbackCreate(BaseModel):
    """Schema para crear feedback"""
    category: FeedbackCategory = Field(..., description="Categoría del feedback")
    title: str = Field(
        ..., 
        min_length=5, 
        max_length=200,
        description="Título del feedback"
    )
    content: str = Field(
        ..., 
        min_length=10, 
        max_length=2000,
        description="Contenido del feedback"
    )
    rating: Optional[int] = Field(
        None, 
        ge=1, 
        le=5, 
        description="Calificación (1-5 estrellas)"
    )
    
    # Contexto específico
    related_analysis_id: Optional[str] = Field(
        None, 
        description="ID del análisis relacionado"
    )
    related_recommendation_id: Optional[str] = Field(
        None, 
        description="ID de la recomendación relacionada"
    )
    
    # Información adicional
    user_agent: Optional[str] = Field(None, description="User agent del navegador")
    page_url: Optional[str] = Field(None, description="URL de la página")
    context_data: Optional[Dict[str, Any]] = Field(
        None, 
        description="Datos adicionales del contexto"
    )
    
    # Metadatos de contacto (opcional)
    contact_email: Optional[str] = Field(None, description="Email de contacto opcional")
    contact_phone: Optional[str] = Field(None, description="Teléfono de contacto opcional")
    
    @validator('title')
    def validate_title(cls, v):
        """Validar título del feedback"""
        if not v or len(v.strip()) == 0:
            raise ValueError('El título es requerido')
        return v.strip()
    
    @validator('content')
    def validate_content(cls, v):
        """Validar contenido del feedback"""
        if not v or len(v.strip()) == 0:
            raise ValueError('El contenido es requerido')
        return v.strip()
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "category": "facial_analysis",
                "title": "Análisis muy preciso",
                "content": "El análisis de mi forma de rostro fue muy acertado y las recomendaciones me encantaron.",
                "rating": 5,
                "related_analysis_id": "analysis_123456789",
                "context_data": {
                    "face_shape_detected": "ovalado",
                    "confidence_level": 85
                }
            }
        }


class FeedbackUpdate(BaseModel):
    """Schema para actualizar feedback"""
    title: Optional[str] = Field(
        None, 
        min_length=5, 
        max_length=200
    )
    content: Optional[str] = Field(
        None, 
        min_length=10, 
        max_length=2000
    )
    rating: Optional[int] = Field(None, ge=1, le=5)
    status: Optional[FeedbackStatus] = None
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "content": "Contenido actualizado del feedback",
                "rating": 4
            }
        }


class FeedbackResponse(BaseModel, TimestampMixin):
    """Schema para respuesta de feedback"""
    id: str = Field(..., description="ID único del feedback")
    user_id: str = Field(..., description="ID del usuario")
    category: FeedbackCategory = Field(..., description="Categoría del feedback")
    title: str = Field(..., description="Título del feedback")
    content: str = Field(..., description="Contenido del feedback")
    rating: Optional[int] = Field(None, description="Calificación")
    status: FeedbackStatus = Field(default=FeedbackStatus.PENDING, description="Estado")
    priority: FeedbackPriority = Field(default=FeedbackPriority.MEDIUM, description="Prioridad")
    
    # Contexto
    related_analysis_id: Optional[str] = None
    related_recommendation_id: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None
    
    # Metadatos de contacto
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    
    # Respuesta del equipo
    admin_response: Optional[str] = Field(None, description="Respuesta del administrador")
    admin_user_id: Optional[str] = Field(None, description="ID del admin que respondió")
    response_date: Optional[datetime] = Field(None, description="Fecha de respuesta")
    
    # Métricas
    helpfulness_votes: int = Field(default=0, description="Votos de utilidad")
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "id": "feedback_123456789",
                "user_id": "user_123456789",
                "category": "facial_analysis",
                "title": "Análisis muy preciso",
                "content": "El análisis fue muy acertado",
                "rating": 5,
                "status": "reviewed",
                "priority": "medium",
                "created_at": "2024-01-01T12:00:00Z"
            }
        }


class FeedbackSummary(BaseModel):
    """Schema para resumen de feedback"""
    total_feedback: int = Field(..., description="Total de feedback recibido")
    average_rating: float = Field(..., description="Calificación promedio")
    category_distribution: Dict[FeedbackCategory, int] = Field(
        ..., 
        description="Distribución por categoría"
    )
    status_distribution: Dict[FeedbackStatus, int] = Field(
        ..., 
        description="Distribución por estado"
    )
    recent_feedback: List[FeedbackResponse] = Field(
        ..., 
        description="Feedback reciente"
    )
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "total_feedback": 150,
                "average_rating": 4.2,
                "category_distribution": {
                    "facial_analysis": 60,
                    "chromatic_analysis": 40,
                    "recommendations": 30,
                    "user_experience": 20
                },
                "status_distribution": {
                    "pending": 10,
                    "reviewed": 80,
                    "resolved": 60
                },
                "recent_feedback": []
            }
        }


class FeedbackFilter(BaseModel):
    """Schema para filtros de feedback"""
    categories: Optional[List[FeedbackCategory]] = Field(None, description="Filtrar por categorías")
    statuses: Optional[List[FeedbackStatus]] = Field(None, description="Filtrar por estados")
    priorities: Optional[List[FeedbackPriority]] = Field(None, description="Filtrar por prioridades")
    min_rating: Optional[int] = Field(None, ge=1, le=5, description="Calificación mínima")
    max_rating: Optional[int] = Field(None, ge=1, le=5, description="Calificación máxima")
    date_from: Optional[datetime] = Field(None, description="Fecha desde")
    date_to: Optional[datetime] = Field(None, description="Fecha hasta")
    has_response: Optional[bool] = Field(None, description="Tiene respuesta del admin")
    search: Optional[str] = Field(None, description="Buscar en título y contenido")
    
    @validator('max_rating')
    def validate_rating_range(cls, v, values):
        if v and 'min_rating' in values and values['min_rating']:
            if v < values['min_rating']:
                raise ValueError('max_rating debe ser mayor o igual que min_rating')
        return v
    
    @validator('date_to')
    def validate_date_range(cls, v, values):
        if v and 'date_from' in values and values['date_from']:
            if v < values['date_from']:
                raise ValueError('date_to debe ser posterior a date_from')
        return v
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "categories": ["facial_analysis", "recommendations"],
                "statuses": ["pending", "reviewed"],
                "min_rating": 4,
                "date_from": "2024-01-01T00:00:00Z",
                "search": "análisis preciso"
            }
        }


class FeedbackAnalytics(BaseModel):
    """Schema para analíticas de feedback"""
    period: str = Field(..., description="Período analizado")
    metrics: Dict[str, Any] = Field(..., description="Métricas calculadas")
    trends: Dict[str, List[float]] = Field(..., description="Tendencias temporales")
    insights: List[str] = Field(..., description="Insights derivados")
    recommendations: List[str] = Field(..., description="Recomendaciones de mejora")
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "period": "last_30_days",
                "metrics": {
                    "total_feedback": 50,
                    "average_rating": 4.3,
                    "satisfaction_rate": 0.86,
                    "response_time_avg_hours": 24
                },
                "trends": {
                    "daily_feedback_count": [2, 3, 1, 4, 2, 3, 5],
                    "daily_average_rating": [4.5, 4.2, 4.0, 4.3, 4.6, 4.1, 4.4]
                },
                "insights": [
                    "El 86% de los usuarios están satisfechos",
                    "Tiempo de respuesta ha mejorado 20%"
                ],
                "recommendations": [
                    "Mantener calidad en análisis facial",
                    "Mejorar tiempo de respuesta a feedback"
                ]
            }
        }


class FeedbackBulkAction(BaseModel):
    """Schema para acciones en lote sobre feedback"""
    feedback_ids: List[str] = Field(..., description="IDs de feedback a procesar")
    action: str = Field(..., description="Acción a realizar")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Parámetros de la acción")
    
    @validator('feedback_ids')
    def validate_feedback_ids(cls, v):
        if len(v) == 0:
            raise ValueError('Debe proporcionar al menos un ID de feedback')
        if len(v) > 100:
            raise ValueError('Máximo 100 feedback por operación en lote')
        return v
    
    @validator('action')
    def validate_action(cls, v):
        allowed_actions = [
            'mark_as_reviewed', 
            'mark_as_resolved', 
            'change_priority', 
            'assign_admin', 
            'bulk_delete'
        ]
        if v not in allowed_actions:
            raise ValueError(f'Acción no permitida. Permitidas: {allowed_actions}')
        return v
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "feedback_ids": ["feedback_1", "feedback_2", "feedback_3"],
                "action": "mark_as_reviewed",
                "parameters": {
                    "admin_user_id": "admin_123"
                }
            }
        }


class AdminResponse(BaseModel):
    """Schema para respuesta de administrador"""
    feedback_id: str = Field(..., description="ID del feedback")
    response_content: str = Field(
        ..., 
        min_length=10, 
        max_length=1000,
        description="Contenido de la respuesta"
    )
    new_status: Optional[FeedbackStatus] = Field(None, description="Nuevo estado del feedback")
    new_priority: Optional[FeedbackPriority] = Field(None, description="Nueva prioridad")
    internal_notes: Optional[str] = Field(None, description="Notas internas")
    
    @validator('response_content')
    def validate_response_content(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('El contenido de la respuesta es requerido')
        return v.strip()
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "feedback_id": "feedback_123456789",
                "response_content": "Gracias por tu feedback. Hemos tomado nota de tu sugerencia.",
                "new_status": "resolved",
                "new_priority": "low",
                "internal_notes": "Usuario muy satisfecho con el análisis"
            }
        }


class FeedbackExport(BaseModel):
    """Schema para exportación de feedback"""
    filters: Optional[FeedbackFilter] = Field(None, description="Filtros a aplicar")
    format: str = Field(default="csv", regex="^(csv|json|xlsx)$", description="Formato de exportación")
    include_personal_data: bool = Field(default=False, description="Incluir datos personales")
    include_context_data: bool = Field(default=True, description="Incluir datos de contexto")
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "filters": {
                    "categories": ["facial_analysis"],
                    "date_from": "2024-01-01T00:00:00Z"
                },
                "format": "csv",
                "include_personal_data": False,
                "include_context_data": True
            }
        }


class FeedbackNotification(BaseModel, TimestampMixin):
    """Schema para notificaciones de feedback"""
    feedback_id: str = Field(..., description="ID del feedback")
    user_id: str = Field(..., description="ID del usuario")
    notification_type: str = Field(..., description="Tipo de notificación")
    title: str = Field(..., description="Título de la notificación")
    message: str = Field(..., description="Mensaje de la notificación")
    is_sent: bool = Field(default=False, description="Notificación enviada")
    delivery_method: str = Field(default="email", description="Método de entrega")
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "feedback_id": "feedback_123456789",
                "user_id": "user_123456789",
                "notification_type": "feedback_response",
                "title": "Respuesta a tu feedback",
                "message": "Hemos respondido a tu feedback sobre el análisis facial",
                "is_sent": True,
                "delivery_method": "email"
            }
        }
