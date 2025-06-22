"""
Esquemas para análisis cromático en Synthia Style API
Modelos para análisis de colores y recomendaciones de paleta
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, validator
from .common import BaseConfig, TimestampMixin, MetadataMixin


class ColorSeasonEnum(str, Enum):
    """Estaciones de color posibles"""
    INVIERNO = "invierno"
    PRIMAVERA = "primavera"
    VERANO = "verano"
    OTOÑO = "otoño"
    UNKNOWN = "unknown"


class SkinUndertoneEnum(str, Enum):
    """Subtonos de piel posibles"""
    FRIO = "frío"
    CALIDO = "cálido"
    NEUTRO = "neutro"
    UNKNOWN = "unknown"


class VeinColorEnum(str, Enum):
    """Color de venas para el quiz"""
    BLUE = "blue"
    GREEN = "green"
    BOTH = "both"
    UNCLEAR = "unclear"


class SunReactionEnum(str, Enum):
    """Reacción al sol para el quiz"""
    BURN_EASILY = "burn"
    TAN_GRADUALLY = "tan"
    TAN_QUICKLY = "tan_quick"
    RARELY_BURN = "rarely_burn"


class JewelryPreferenceEnum(str, Enum):
    """Preferencia de joyería para el quiz"""
    GOLD = "gold"
    SILVER = "silver"
    BOTH = "both"
    NEITHER = "neither"


class ColorRecommendationType(str, Enum):
    """Tipos de recomendaciones de color"""
    PRIMARY_PALETTE = "primary_palette"
    COLORS_TO_AVOID = "colors_to_avoid"
    ACCENT_COLORS = "accent_colors"
    NEUTRAL_COLORS = "neutral_colors"


class QuizResponse(BaseModel):
    """Schema para respuesta individual del quiz cromático"""
    question_id: str = Field(..., description="ID de la pregunta")
    answer: str = Field(..., description="Respuesta seleccionada")
    confidence: Optional[int] = Field(
        None, 
        ge=1, 
        le=5, 
        description="Confianza en la respuesta (1-5)"
    )
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "question_id": "vein_color",
                "answer": "blue",
                "confidence": 4
            }
        }


class ChromaticAnalysisRequest(BaseModel):
    """Schema para solicitud de análisis cromático"""
    quiz_responses: List[QuizResponse] = Field(
        ..., 
        description="Respuestas del quiz cromático"
    )
    additional_info: Optional[Dict[str, Any]] = Field(
        None, 
        description="Información adicional opcional"
    )
    analysis_preferences: Optional[Dict[str, Any]] = Field(
        None, 
        description="Preferencias específicas para el análisis"
    )
    
    @validator('quiz_responses')
    def validate_quiz_responses(cls, v):
        """Validar respuestas del quiz"""
        if len(v) == 0:
            raise ValueError('Debe proporcionar al menos una respuesta')
        
        # Verificar que no hay duplicados de question_id
        question_ids = [response.question_id for response in v]
        if len(question_ids) != len(set(question_ids)):
            raise ValueError('No se permiten respuestas duplicadas para la misma pregunta')
        
        return v
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "quiz_responses": [
                    {
                        "question_id": "vein_color",
                        "answer": "blue",
                        "confidence": 4
                    },
                    {
                        "question_id": "sun_reaction",
                        "answer": "burn",
                        "confidence": 5
                    },
                    {
                        "question_id": "jewelry_preference",
                        "answer": "silver",
                        "confidence": 3
                    }
                ],
                "additional_info": {
                    "skin_description": "Piel clara con tendencia a quemarse",
                    "eye_color": "azul"
                }
            }
        }


class ColorRecommendation(BaseModel):
    """Schema para recomendación de color"""
    type: ColorRecommendationType = Field(..., description="Tipo de recomendación")
    color_name: str = Field(..., description="Nombre del color")
    hex_code: str = Field(..., regex="^#[0-9A-Fa-f]{6}$", description="Código hexadecimal")
    explanation: str = Field(..., description="Explicación de por qué es recomendado/evitado")
    priority: int = Field(default=1, ge=1, le=5, description="Prioridad (1-5)")
    confidence: float = Field(
        default=0.8, 
        ge=0.0, 
        le=1.0, 
        description="Confianza en la recomendación"
    )
    tags: List[str] = Field(default=[], description="Etiquetas del color")
    usage_contexts: List[str] = Field(
        default=[], 
        description="Contextos de uso (ropa, maquillaje, etc.)"
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadatos adicionales")
    
    @validator('hex_code')
    def validate_hex_code(cls, v):
        """Validar código hexadecimal"""
        if not v.startswith('#'):
            v = f"#{v}"
        
        if len(v) != 7:
            raise ValueError('Código hexadecimal debe tener 7 caracteres (#RRGGBB)')
        
        try:
            int(v[1:], 16)
        except ValueError:
            raise ValueError('Código hexadecimal inválido')
        
        return v.upper()
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "type": "primary_palette",
                "color_name": "Azul royal",
                "hex_code": "#4169E1",
                "explanation": "Complementa el subtono frío de tu piel, aportando luminosidad",
                "priority": 1,
                "confidence": 0.9,
                "tags": ["intenso", "frío", "elegante"],
                "usage_contexts": ["ropa_formal", "accesorios"],
                "metadata": {
                    "rgb": [65, 105, 225],
                    "season_match": 0.95
                }
            }
        }


class SeasonCharacteristics(BaseModel):
    """Schema para características de una estación de color"""
    season: ColorSeasonEnum = Field(..., description="Estación de color")
    undertone: SkinUndertoneEnum = Field(..., description="Subtono de piel")
    description: str = Field(..., description="Descripción general de la estación")
    key_characteristics: List[str] = Field(
        ..., 
        description="Características clave de la estación"
    )
    contrast_level: str = Field(..., description="Nivel de contraste (alto, medio, bajo)")
    intensity_level: str = Field(..., description="Nivel de intensidad de colores")
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "season": "invierno",
                "undertone": "frío",
                "description": "Contraste alto, colores intensos con base azul",
                "key_characteristics": [
                    "Piel con subtono frío",
                    "Contraste marcado entre piel, cabello y ojos",
                    "Colores intensos y puros"
                ],
                "contrast_level": "alto",
                "intensity_level": "alto"
            }
        }


class ChromaticAnalysisResult(BaseModel, TimestampMixin):
    """Schema para resultado de análisis cromático"""
    id: str = Field(..., description="ID único del análisis")
    user_id: str = Field(..., description="ID del usuario")
    
    # Respuestas del quiz
    quiz_responses: List[QuizResponse] = Field(
        ..., 
        description="Respuestas originales del quiz"
    )
    
    # Resultados del análisis
    color_season: ColorSeasonEnum = Field(..., description="Estación de color determinada")
    skin_undertone: SkinUndertoneEnum = Field(..., description="Subtono de piel")
    confidence_level: int = Field(
        ..., 
        ge=1, 
        le=100, 
        description="Nivel de confianza del análisis"
    )
    
    # Características de la estación
    season_characteristics: SeasonCharacteristics = Field(
        ..., 
        description="Características de la estación determinada"
    )
    
    # Análisis detallado de IA
    ai_analysis_data: Optional[Dict[str, Any]] = Field(
        None, 
        description="Datos completos del análisis de IA"
    )
    
    # Recomendaciones de color
    color_recommendations: List[ColorRecommendation] = Field(
        default=[], 
        description="Recomendaciones de colores"
    )
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "id": "chromatic_123456789",
                "user_id": "user_123456789",
                "quiz_responses": [
                    {
                        "question_id": "vein_color",
                        "answer": "blue"
                    }
                ],
                "color_season": "invierno",
                "skin_undertone": "frío",
                "confidence_level": 88,
                "season_characteristics": {
                    "season": "invierno",
                    "undertone": "frío",
                    "description": "Contraste alto, colores intensos"
                },
                "color_recommendations": [
                    {
                        "type": "primary_palette",
                        "color_name": "Azul royal",
                        "hex_code": "#4169E1",
                        "explanation": "Complementa tu subtono frío"
                    }
                ]
            }
        }


class ChromaticAnalysisResponse(BaseModel):
    """Schema para respuesta de análisis cromático"""
    status: str = Field(default="success", description="Estado del análisis")
    message: str = Field(default="Análisis cromático completado exitosamente")
    analysis: ChromaticAnalysisResult = Field(..., description="Resultado del análisis")
    processing_time_ms: Optional[float] = Field(None, description="Tiempo de procesamiento")
    
    class Config(BaseConfig):
        pass


class ChromaticAnalysisHistory(BaseModel):
    """Schema para historial de análisis cromático"""
    analyses: List[ChromaticAnalysisResult] = Field(..., description="Lista de análisis")
    total_count: int = Field(..., description="Total de análisis")
    date_range: Dict[str, datetime] = Field(..., description="Rango de fechas")
    most_common_season: Optional[ColorSeasonEnum] = Field(
        None, 
        description="Estación más común en el historial"
    )
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "analyses": [],
                "total_count": 3,
                "date_range": {
                    "from": "2024-01-01T00:00:00Z",
                    "to": "2024-01-31T23:59:59Z"
                },
                "most_common_season": "invierno"
            }
        }


class ChromaticAnalysisStats(BaseModel):
    """Schema para estadísticas de análisis cromático"""
    total_analyses: int = Field(..., description="Total de análisis realizados")
    season_distribution: Dict[ColorSeasonEnum, int] = Field(
        ..., 
        description="Distribución de estaciones de color"
    )
    undertone_distribution: Dict[SkinUndertoneEnum, int] = Field(
        ..., 
        description="Distribución de subtonos"
    )
    average_confidence: float = Field(..., description="Confianza promedio")
    monthly_analysis_count: Dict[str, int] = Field(
        ..., 
        description="Conteo mensual de análisis"
    )
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "total_analyses": 800,
                "season_distribution": {
                    "invierno": 200,
                    "primavera": 180,
                    "verano": 220,
                    "otoño": 200
                },
                "undertone_distribution": {
                    "frío": 420,
                    "cálido": 300,
                    "neutro": 80
                },
                "average_confidence": 84.2,
                "monthly_analysis_count": {
                    "2024-01": 80,
                    "2024-02": 95,
                    "2024-03": 110
                }
            }
        }


class ColorPalette(BaseModel):
    """Schema para paleta de colores"""
    name: str = Field(..., description="Nombre de la paleta")
    season: ColorSeasonEnum = Field(..., description="Estación asociada")
    colors: List[ColorRecommendation] = Field(..., description="Colores de la paleta")
    description: str = Field(..., description="Descripción de la paleta")
    use_cases: List[str] = Field(default=[], description="Casos de uso")
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "name": "Paleta Invierno Clásico",
                "season": "invierno",
                "colors": [
                    {
                        "color_name": "Blanco puro",
                        "hex_code": "#FFFFFF",
                        "explanation": "Color base perfecto"
                    }
                ],
                "description": "Paleta clásica para personas de estación invierno",
                "use_cases": ["trabajo", "eventos_formales", "diario"]
            }
        }


class ChromaticQuizQuestion(BaseModel):
    """Schema para pregunta del quiz cromático"""
    id: str = Field(..., description="ID único de la pregunta")
    question: str = Field(..., description="Texto de la pregunta")
    type: str = Field(..., description="Tipo de pregunta (single_choice, multiple_choice)")
    options: List[Dict[str, str]] = Field(..., description="Opciones de respuesta")
    help_text: Optional[str] = Field(None, description="Texto de ayuda")
    image_url: Optional[str] = Field(None, description="URL de imagen de ayuda")
    weight: float = Field(default=1.0, description="Peso de la pregunta en el análisis")
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "id": "vein_color",
                "question": "¿De qué color se ven las venas en tu muñeca?",
                "type": "single_choice",
                "options": [
                    {"value": "blue", "label": "Azul/Púrpura"},
                    {"value": "green", "label": "Verde/Oliva"},
                    {"value": "both", "label": "Ambos"},
                    {"value": "unclear", "label": "No estoy segura"}
                ],
                "help_text": "Mira las venas en la parte interna de tu muñeca bajo luz natural",
                "weight": 1.5
            }
        }


class ChromaticAnalysisFilter(BaseModel):
    """Schema para filtros de análisis cromático"""
    seasons: Optional[List[ColorSeasonEnum]] = Field(None, description="Filtrar por estaciones")
    undertones: Optional[List[SkinUndertoneEnum]] = Field(None, description="Filtrar por subtonos")
    date_from: Optional[datetime] = Field(None, description="Fecha desde")
    date_to: Optional[datetime] = Field(None, description="Fecha hasta")
    min_confidence: Optional[int] = Field(None, ge=1, le=100, description="Confianza mínima")
    
    @validator('date_to')
    def validate_date_range(cls, v, values):
        if v and 'date_from' in values and values['date_from']:
            if v < values['date_from']:
                raise ValueError('date_to debe ser posterior a date_from')
        return v
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "seasons": ["invierno", "verano"],
                "undertones": ["frío"],
                "date_from": "2024-01-01T00:00:00Z",
                "date_to": "2024-01-31T23:59:59Z",
                "min_confidence": 80
            }
        }


class ColorMatch(BaseModel):
    """Schema para coincidencia de color"""
    color: ColorRecommendation = Field(..., description="Color recomendado")
    match_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Puntuación de coincidencia"
    )
    context: str = Field(..., description="Contexto de la coincidencia")
    
    class Config(BaseConfig):
        pass


class ColorAnalysisComparison(BaseModel):
    """Schema para comparación de análisis cromáticos"""
    analysis_1: ChromaticAnalysisResult = Field(..., description="Primer análisis")
    analysis_2: ChromaticAnalysisResult = Field(..., description="Segundo análisis")
    consistency_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Puntuación de consistencia"
    )
    differences: Dict[str, Any] = Field(..., description="Diferencias encontradas")
    
    class Config(BaseConfig):
        pass
