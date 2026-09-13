"""
Esquemas Pydantic para Análisis Facial
"""

from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class FaceShapeEnum(str, Enum):
    OVAL = "OVAL"
    ROUND = "ROUND"
    SQUARE = "SQUARE"
    HEART = "HEART"
    DIAMOND = "DIAMOND"
    OBLONG = "OBLONG"


class RecommendationCategory(str, Enum):
    EYEWEAR = "EYEWEAR"
    HAIRSTYLE = "HAIRSTYLE"
    MAKEUP = "MAKEUP"
    ACCESSORIES = "ACCESSORIES"


class FacialRecommendation(BaseModel):
    category: RecommendationCategory
    title: str
    description: str
    confidence: float = 0.85
    tags: List[str] = Field(default_factory=list)


class FacialAnalysisRequest(BaseModel):
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    client_metadata: Optional[Dict[str, Any]] = None


class FacialAnalysisResult(BaseModel):
    face_shape: FaceShapeEnum = FaceShapeEnum.OVAL
    jawline: str = "balanced"
    proportions: Dict[str, float] = Field(default_factory=dict)
    symmetry_score: float = 0.88
    recommended_frames: List[str] = Field(default_factory=list)


class FacialAnalysisResponse(BaseModel):
    id: str = "fa_sample_id"
    user_id: str
    result: FacialAnalysisResult
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FacialAnalysisHistory(BaseModel):
    id: str
    user_id: str
    face_shape: FaceShapeEnum
    created_at: datetime


class FacialAnalysisFilter(BaseModel):
    face_shape: Optional[FaceShapeEnum] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
