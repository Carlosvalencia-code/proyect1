"""
Esquemas Pydantic para Análisis Cromático (Colorimetría)
"""

from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class ColorSeasonEnum(str, Enum):
    SPRING = "SPRING"
    SUMMER = "SUMMER"
    AUTUMN = "AUTUMN"
    WINTER = "WINTER"


class SkinUndertoneEnum(str, Enum):
    WARM = "WARM"
    COOL = "COOL"
    NEUTRAL = "NEUTRAL"


class ColorRecommendationType(str, Enum):
    BEST = "BEST"
    ACCENT = "ACCENT"
    NEUTRAL = "NEUTRAL"
    AVOID = "AVOID"


class SeasonCharacteristics(BaseModel):
    name: str
    description: str
    undertone: SkinUndertoneEnum
    palette: List[str] = Field(default_factory=list)


class QuizResponse(BaseModel):
    season: ColorSeasonEnum
    confidence: float = 0.85
    answers_summary: Dict[str, Any] = Field(default_factory=dict)


class ColorRecommendation(BaseModel):
    color_hex: str
    color_name: str
    category: ColorRecommendationType = ColorRecommendationType.BEST


class ChromaticAnalysisRequest(BaseModel):
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    quiz_answers: Optional[Dict[str, Any]] = None


class ChromaticAnalysisResult(BaseModel):
    season: ColorSeasonEnum = ColorSeasonEnum.AUTUMN
    sub_season: str = "DEEP_AUTUMN"
    undertone: SkinUndertoneEnum = SkinUndertoneEnum.WARM
    confidence: float = 0.90
    palette: List[str] = Field(default_factory=list)


class ChromaticAnalysisResponse(BaseModel):
    id: str = "ca_sample_id"
    user_id: str
    result: ChromaticAnalysisResult
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChromaticAnalysisFilter(BaseModel):
    season: Optional[ColorSeasonEnum] = None
    undertone: Optional[SkinUndertoneEnum] = None
