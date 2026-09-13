"""
Esquemas Pydantic para el Widget B2B de Recomendación de Comercio (Synthia B2B)
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ColorimetryProfile(BaseModel):
    season: str = Field(..., description="Estación cromática: SPRING, SUMMER, AUTUMN, WINTER")
    sub_season: Optional[str] = Field(None, description="Sub-estación: DEEP_AUTUMN, COOL_WINTER, etc.")
    undertone: str = Field("neutral", description="Subtono: warm, cool, neutral")
    best_colors: List[str] = Field(default_factory=list, description="Lista de códigos hex o nombres de colores recomendados")
    colors_to_avoid: List[str] = Field(default_factory=list, description="Colores menos favorecedores")


class VisagismProfile(BaseModel):
    face_shape: str = Field(..., description="Forma de rostro: OVAL, ROUND, SQUARE, HEART, DIAMOND, OBLONG")
    recommended_frame_shapes: List[str] = Field(default_factory=list, description="Formas de montura sugeridas")
    frames_to_avoid: List[str] = Field(default_factory=list, description="Formas de montura a evitar")


class CatalogItem(BaseModel):
    sku: str
    title: str
    category: str
    price: float
    currency: str = "USD"
    image_url: str
    product_url: Optional[str] = None
    color_family: Optional[str] = None
    frame_shape: Optional[str] = None
    harmony_score: int = Field(..., ge=0, le=100)
    match_tag: str = Field("Favorecedor", description="Badge en UI: Match Perfecto, Top Colorimetría, etc.")


class WidgetRecommendRequest(BaseModel):
    sku: Optional[str] = Field(None, description="SKU del producto que el usuario está viendo actualmente en la PDP")
    category: Optional[str] = Field("eyewear", description="Categoría: eyewear, apparel, cosmetics")
    image_base64: Optional[str] = Field(None, description="Selfie del usuario en Base64 o URL de imagen")
    image_url: Optional[str] = Field(None, description="URL pública del selfie")
    quiz_data: Optional[Dict[str, Any]] = Field(None, description="Respuestas rápidas si el usuario no usa cámara")
    client_session_id: Optional[str] = Field(None, description="ID de sesión anónima para tracking de conversión")


class WidgetRecommendResponse(BaseModel):
    status: str = "success"
    merchant_id: str
    colorimetry: ColorimetryProfile
    visagism: VisagismProfile
    current_product_score: Optional[int] = Field(None, description="Puntuación de compatibilidad del producto actual visto")
    fit_verdict: str = Field("GOOD_MATCH", description="Veredicto: PERFECT_MATCH, GOOD_MATCH, NEUTRAL, NOT_RECOMMENDED")
    stylist_advice: str = Field(..., description="Explicación humana y técnica de por qué favorece sus facciones")
    recommended_catalog: List[CatalogItem] = Field(default_factory=list, description="Productos alternativos o complementarios del catálogo del comercio")
    processing_time_ms: float
