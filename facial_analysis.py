"""
Esquemas para análisis facial en Synthia Style API
Modelos para análisis de rostro y recomendaciones de estilo
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, validator
from .common import BaseConfig, TimestampMixin, MetadataMixin, ImageMetadata


class FaceShapeEnum(str, Enum):
    """Formas de rostro posibles"""
    OVALADO = "ovalado"
    REDONDO = "redondo"
    CUADRADO = "cuadrado"
    RECTANGULAR = "rectangular"
    CORAZÓN = "corazón"
    DIAMANTE = "diamante"
    TRIANGULAR = "triangular"
    UNKNOWN = "unknown"


class RecommendationCategory(str, Enum):
    """Categorías de recomendaciones"""
    CORTES_PELO = "cortes_pelo"
    GAFAS = "gafas"
    ESCOTES = "escotes"
    ACCESORIOS = "accesorios"
    MAQUILLAJE = "maquillaje"


class FacialAnalysisRequest(BaseModel):
    """Schema para solicitud de análisis facial"""
    image_data: str = Field(..., description="Imagen en base64")
    image_filename: str = Field(..., description="Nombre del archivo")
    analysis_preferences: Optional[Dict[str, Any]] = Field(
        None, 
        description="Preferencias específicas para el análisis"
    )
    
    @validator('image_data')
    def validate_image_data(cls, v):
        """Validar datos de imagen base64"""
        if not v or len(v.strip()) == 0:
            raise ValueError('Los datos de imagen son requeridos')
        
        # Verificar que sea base64 válido básicamente
        import base64
        try:
            base64.b64decode(v, validate=True)
        except Exception:
            raise ValueError('Datos de imagen base64 inválidos')
        
        return v
    
    @validator('image_filename')
    def validate_filename(cls, v):
        """Validar nombre de archivo"""
        if not v or len(v.strip()) == 0:
            raise ValueError('El nombre del archivo es requerido')
        
        # Verificar extensión
        allowed_extensions = ['jpg', 'jpeg', 'png', 'webp']
        extension = v.lower().split('.')[-1] if '.' in v else ''
        
        if extension not in allowed_extensions:
            raise ValueError(f'Extensión no permitida. Permitidas: {allowed_extensions}')
        
        return v
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "image_data": "/9j/4AAQSkZJRgABAQEAAA...",
                "image_filename": "mi_foto.jpg",
                "analysis_preferences": {
                    "include_confidence": True,
                    "detailed_features": True
                }
            }
        }


class FacialFeature(BaseModel):
    """Schema para característica facial específica"""
    name: str = Field(..., description="Nombre de la característica")
    description: str = Field(..., description="Descripción de la característica")
    prominence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Prominencia de la característica (0-1)"
    )
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "name": "pómulos",
                "description": "Pómulos definidos y prominentes",
                "prominence": 0.8
            }
        }


class FacialRecommendation(BaseModel):
    """Schema para recomendación de estilo facial"""
    category: RecommendationCategory = Field(..., description="Categoría de la recomendación")
    name: str = Field(..., description="Nombre de la recomendación")
    description: str = Field(..., description="Descripción breve")
    explanation: str = Field(..., description="Explicación detallada")
    priority: int = Field(default=1, ge=1, le=5, description="Prioridad (1-5)")
    confidence: float = Field(
        default=0.8, 
        ge=0.0, 
        le=1.0, 
        description="Confianza en la recomendación"
    )
    tags: List[str] = Field(default=[], description="Etiquetas adicionales")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadatos adicionales")
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "category": "cortes_pelo",
                "name": "Bob clásico",
                "description": "Corte recto a la altura de la mandíbula",
                "explanation": "Enmarca el rostro resaltando los pómulos sin modificar las proporciones naturales",
                "priority": 1,
                "confidence": 0.9,
                "tags": ["elegante", "versátil", "clásico"],
                "metadata": {
                    "difficulty": "easy",
                    "maintenance": "medium"
                }
            }
        }


class FacialAnalysisResult(BaseModel, TimestampMixin):
    """Schema para resultado de análisis facial"""
    id: str = Field(..., description="ID único del análisis")
    user_id: str = Field(..., description="ID del usuario")
    
    # Imagen analizada
    image_url: str = Field(..., description="URL de la imagen")
    image_metadata: Optional[ImageMetadata] = Field(None, description="Metadatos de la imagen")
    
    # Resultados del análisis
    face_shape: FaceShapeEnum = Field(..., description="Forma del rostro detectada")
    features_highlighted: List[FacialFeature] = Field(
        default=[], 
        description="Características faciales destacadas"
    )
    confidence_level: int = Field(
        ..., 
        ge=1, 
        le=100, 
        description="Nivel de confianza del análisis"
    )
    
    # Proporciones faciales
    facial_proportions: Optional[Dict[str, float]] = Field(
        None, 
        description="Proporciones faciales medidas"
    )
    
    # Análisis detallado de IA
    ai_analysis_data: Optional[Dict[str, Any]] = Field(
        None, 
        description="Datos completos del análisis de IA"
    )
    
    # Recomendaciones
    recommendations: List[FacialRecommendation] = Field(
        default=[], 
        description="Recomendaciones de estilo"
    )
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "id": "analysis_123456789",
                "user_id": "user_123456789",
                "image_url": "/uploads/facial/image_123.jpg",
                "face_shape": "ovalado",
                "features_highlighted": [
                    {
                        "name": "pómulos",
                        "description": "Pómulos definidos",
                        "prominence": 0.8
                    }
                ],
                "confidence_level": 85,
                "facial_proportions": {
                    "width_to_height_ratio": 0.75,
                    "forehead_to_face_ratio": 0.33
                },
                "recommendations": [
                    {
                        "category": "cortes_pelo",
                        "name": "Bob clásico",
                        "description": "Corte recto a la altura de la mandíbula",
                        "explanation": "Enmarca el rostro perfectamente"
                    }
                ]
            }
        }


class FacialAnalysisResponse(BaseModel):
    """Schema para respuesta de análisis facial"""
    status: str = Field(default="success", description="Estado del análisis")
    message: str = Field(default="Análisis completado exitosamente")
    analysis: FacialAnalysisResult = Field(..., description="Resultado del análisis")
    processing_time_ms: Optional[float] = Field(None, description="Tiempo de procesamiento")
    
    class Config(BaseConfig):
        pass


class FacialAnalysisHistory(BaseModel):
    """Schema para historial de análisis facial"""
    analyses: List[FacialAnalysisResult] = Field(..., description="Lista de análisis")
    total_count: int = Field(..., description="Total de análisis")
    date_range: Dict[str, datetime] = Field(..., description="Rango de fechas")
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "analyses": [],
                "total_count": 5,
                "date_range": {
                    "from": "2024-01-01T00:00:00Z",
                    "to": "2024-01-31T23:59:59Z"
                }
            }
        }


class FacialAnalysisComparison(BaseModel):
    """Schema para comparación de análisis faciales"""
    analysis_1: FacialAnalysisResult = Field(..., description="Primer análisis")
    analysis_2: FacialAnalysisResult = Field(..., description="Segundo análisis")
    differences: Dict[str, Any] = Field(..., description="Diferencias encontradas")
    similarity_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Puntuación de similitud"
    )
    
    class Config(BaseConfig):
        pass


class FacialAnalysisStats(BaseModel):
    """Schema para estadísticas de análisis facial"""
    total_analyses: int = Field(..., description="Total de análisis realizados")
    most_common_face_shape: FaceShapeEnum = Field(..., description="Forma de rostro más común")
    average_confidence: float = Field(..., description="Confianza promedio")
    shape_distribution: Dict[FaceShapeEnum, int] = Field(
        ..., 
        description="Distribución de formas de rostro"
    )
    monthly_analysis_count: Dict[str, int] = Field(
        ..., 
        description="Conteo mensual de análisis"
    )
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "total_analyses": 1000,
                "most_common_face_shape": "ovalado",
                "average_confidence": 82.5,
                "shape_distribution": {
                    "ovalado": 300,
                    "redondo": 250,
                    "cuadrado": 200,
                    "corazón": 150,
                    "rectangular": 100
                },
                "monthly_analysis_count": {
                    "2024-01": 100,
                    "2024-02": 120,
                    "2024-03": 150
                }
            }
        }


class RecommendationFeedback(BaseModel, TimestampMixin):
    """Schema para feedback de recomendaciones"""
    analysis_id: str = Field(..., description="ID del análisis")
    recommendation_category: RecommendationCategory = Field(
        ..., 
        description="Categoría de la recomendación"
    )
    recommendation_name: str = Field(..., description="Nombre de la recomendación")
    
    # Feedback
    rating: int = Field(..., ge=1, le=5, description="Calificación (1-5 estrellas)")
    helpful: bool = Field(..., description="¿Fue útil la recomendación?")
    tried: bool = Field(default=False, description="¿Probó la recomendación?")
    comments: Optional[str] = Field(None, description="Comentarios adicionales")
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "analysis_id": "analysis_123456789",
                "recommendation_category": "cortes_pelo",
                "recommendation_name": "Bob clásico",
                "rating": 5,
                "helpful": True,
                "tried": True,
                "comments": "¡Me encantó el resultado! Muy recomendado."
            }
        }


class FacialAnalysisFilter(BaseModel):
    """Schema para filtros de análisis facial"""
    face_shapes: Optional[List[FaceShapeEnum]] = Field(None, description="Filtrar por formas")
    date_from: Optional[datetime] = Field(None, description="Fecha desde")
    date_to: Optional[datetime] = Field(None, description="Fecha hasta")
    min_confidence: Optional[int] = Field(None, ge=1, le=100, description="Confianza mínima")
    has_recommendations: Optional[bool] = Field(None, description="Tiene recomendaciones")
    
    @validator('date_to')
    def validate_date_range(cls, v, values):
        if v and 'date_from' in values and values['date_from']:
            if v < values['date_from']:
                raise ValueError('date_to debe ser posterior a date_from')
        return v
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "face_shapes": ["ovalado", "redondo"],
                "date_from": "2024-01-01T00:00:00Z",
                "date_to": "2024-01-31T23:59:59Z",
                "min_confidence": 80,
                "has_recommendations": True
            }
        }


class BulkFacialAnalysis(BaseModel):
    """Schema para análisis facial en lote"""
    images: List[Dict[str, str]] = Field(
        ..., 
        description="Lista de imágenes con data y filename"
    )
    analysis_preferences: Optional[Dict[str, Any]] = Field(
        None, 
        description="Preferencias para todos los análisis"
    )
    
    @validator('images')
    def validate_images_count(cls, v):
        if len(v) == 0:
            raise ValueError('Debe proporcionar al menos una imagen')
        if len(v) > 10:
            raise ValueError('Máximo 10 imágenes por lote')
        return v
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "images": [
                    {
                        "image_data": "/9j/4AAQSkZJRgABAQEAAA...",
                        "image_filename": "foto1.jpg"
                    },
                    {
                        "image_data": "/9j/4AAQSkZJRgABAQEAAB...",
                        "image_filename": "foto2.jpg"
                    }
                ],
                "analysis_preferences": {
                    "include_confidence": True
                }
            }
        }
