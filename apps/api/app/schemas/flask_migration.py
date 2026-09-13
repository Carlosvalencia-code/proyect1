"""
Esquemas Pydantic para compatibilidad con migración Flask
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserSignup(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    name: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class LogoutResponse(BaseModel):
    message: str = "Logged out successfully"


class FacialAnalysisRequest(BaseModel):
    image_base64: Optional[str] = None
    image_url: Optional[str] = None


class FacialAnalysisResult(BaseModel):
    face_shape: str = "OVAL"
    confidence: float = 0.88


class FacialAnalysisResponse(BaseModel):
    id: str = "fa_sample_1"
    result: FacialAnalysisResult


class ChromaticQuizAnswers(BaseModel):
    answers: Dict[str, Any] = Field(default_factory=dict)


class ChromaticAnalysisResult(BaseModel):
    season: str = "AUTUMN"
    confidence: float = 0.90


class ChromaticAnalysisResponse(BaseModel):
    id: str = "ca_sample_1"
    result: ChromaticAnalysisResult


class FeedbackSubmission(BaseModel):
    rating: int = 5
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    status: str = "received"


class DashboardData(BaseModel):
    total_users: int = 0
    total_analyses: int = 0


class DashboardResponse(BaseModel):
    data: DashboardData


class AnalysisHistory(BaseModel):
    items: List[Dict[str, Any]] = Field(default_factory=list)


class FlaskMigrationInfo(BaseModel):
    migrated: bool = True
    fastapi_version: str = "0.104.1"


class HealthCheck(BaseModel):
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ReactFacialAnalysisData(BaseModel):
    data: Dict[str, Any] = Field(default_factory=dict)


class ReactChromaticAnalysisData(BaseModel):
    data: Dict[str, Any] = Field(default_factory=dict)


class FaceShape(BaseModel):
    shape: str = "OVAL"
    confidence: float = 0.88


class ColorSeason(BaseModel):
    season: str = "AUTUMN"
    confidence: float = 0.90


class SkinUndertone(BaseModel):
    undertone: str = "WARM"
    confidence: float = 0.85


class UserSession(BaseModel):
    session_id: str
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


class HaircutRecommendation(BaseModel):
    name: str
    description: str
    reason: str


class GlassesRecommendation(BaseModel):
    frame_type: str
    reason: str


class NecklineRecommendation(BaseModel):
    neckline_type: str
    reason: str


class FacialRecommendations(BaseModel):
    haircuts: List[HaircutRecommendation] = Field(default_factory=list)
    glasses: List[GlassesRecommendation] = Field(default_factory=list)
    necklines: List[NecklineRecommendation] = Field(default_factory=list)


class ColorRecommendation(BaseModel):
    color_name: str
    hex_code: str
    reason: str
