"""
Esquemas Pydantic para Armario y Outfits
"""

from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class ClothingCategory(str, Enum):
    TOPS = "TOPS"
    BOTTOMS = "BOTTOMS"
    DRESSES = "DRESSES"
    OUTERWEAR = "OUTERWEAR"
    FOOTWEAR = "FOOTWEAR"
    ACCESSORIES = "ACCESSORIES"
    EYEWEAR = "EYEWEAR"


class ClothingSubcategory(str, Enum):
    T_SHIRT = "T_SHIRT"
    SHIRT = "SHIRT"
    BLOUSE = "BLOUSE"
    SWEATER = "SWEATER"
    JEANS = "JEANS"
    TROUSERS = "TROUSERS"
    SKIRT = "SKIRT"
    JACKET = "JACKET"
    COAT = "COAT"
    SNEAKERS = "SNEAKERS"
    BOOTS = "BOOTS"
    OPTICAL = "OPTICAL"
    SUNGLASSES = "SUNGLASSES"
    OTHER = "OTHER"


class FitType(str, Enum):
    SLIM = "SLIM"
    REGULAR = "REGULAR"
    OVERSIZED = "OVERSIZED"
    TIGHT = "TIGHT"
    LOOSE = "LOOSE"


class ClothingStyle(str, Enum):
    CASUAL = "CASUAL"
    FORMAL = "FORMAL"
    BUSINESS = "BUSINESS"
    BUSINESS_CASUAL = "BUSINESS_CASUAL"
    SPORT = "SPORT"
    SPORTY = "SPORTY"
    ELEGANT = "ELEGANT"
    BOHEMIAN = "BOHEMIAN"
    MINIMALIST = "MINIMALIST"
    VINTAGE = "VINTAGE"
    TRENDY = "TRENDY"
    CLASSIC = "CLASSIC"
    EDGY = "EDGY"
    ROMANTIC = "ROMANTIC"


class Season(str, Enum):
    SPRING = "SPRING"
    SUMMER = "SUMMER"
    AUTUMN = "AUTUMN"
    WINTER = "WINTER"
    ALL_SEASON = "ALL_SEASON"


class Occasion(str, Enum):
    WORK = "WORK"
    CASUAL = "CASUAL"
    FORMAL = "FORMAL"
    PARTY = "PARTY"
    DATE = "DATE"
    VACATION = "VACATION"
    EXERCISE = "EXERCISE"
    HOME = "HOME"
    SPECIAL_EVENT = "SPECIAL_EVENT"
    TRAVEL = "TRAVEL"


class OutfitStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    DRAFT = "DRAFT"


class WardrobeItemCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    category: ClothingCategory
    color: str
    image_url: Optional[str] = None
    brand: Optional[str] = None
    style: ClothingStyle = ClothingStyle.CASUAL
    season: Season = Season.ALL_SEASON


class WardrobeItemUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[ClothingCategory] = None
    color: Optional[str] = None
    brand: Optional[str] = None


class WardrobeAnalysisType(str, Enum):
    GAPS_ANALYSIS = "GAPS_ANALYSIS"
    COLOR_HARMONY = "COLOR_HARMONY"
    VERSATILITY = "VERSATILITY"
    STYLE_CONSISTENCY = "STYLE_CONSISTENCY"


class WardrobeItemResponse(BaseModel):
    id: str = "item_demo_1"
    user_id: str = "usr_demo_123"
    title: str
    category: ClothingCategory
    color: str
    image_url: Optional[Any] = None
    brand: Optional[str] = None
    times_worn: int = 0
    is_favorite: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WardrobeStats(BaseModel):
    total_items: int = 0
    by_category: Dict[str, int] = Field(default_factory=dict)
    by_color: Dict[str, int] = Field(default_factory=dict)
    items_by_category: Dict[str, int] = Field(default_factory=dict)
    items_by_color: Dict[str, int] = Field(default_factory=dict)
    items_by_season: Dict[str, int] = Field(default_factory=dict)
    items_by_style: Dict[str, int] = Field(default_factory=dict)
    total_value: Optional[float] = None
    average_cost_per_wear: Optional[float] = None
    most_worn_items: List[Any] = Field(default_factory=list)
    least_worn_items: List[Any] = Field(default_factory=list)
    favorite_items: List[Any] = Field(default_factory=list)
    recent_additions: List[Any] = Field(default_factory=list)


class WardrobeAnalysisResponse(BaseModel):
    id: str = "wa_demo_1"
    user_id: str
    analysis_type: str = "GAPS_ANALYSIS"
    results: Dict[str, Any] = Field(default_factory=dict)
    score: float = 85.0
    insights: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    priorities: List[str] = Field(default_factory=list)
    total_items: int = 0
    items_by_category: Dict[str, Any] = Field(default_factory=dict)
    items_by_color: Dict[str, Any] = Field(default_factory=dict)
    items_by_season: Dict[str, Any] = Field(default_factory=dict)
    missing_basics: List[str] = Field(default_factory=list)
    color_gaps: List[str] = Field(default_factory=list)
    occasion_gaps: List[str] = Field(default_factory=list)


class OutfitGenerationRequest(BaseModel):
    occasion: Occasion = Occasion.CASUAL
    season: Optional[Season] = None
    preferred_colors: List[str] = Field(default_factory=list)


class OutfitCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    item_ids: List[str] = Field(default_factory=list)
    occasion: Occasion = Occasion.CASUAL
    season: Optional[Season] = None


class OutfitUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    item_ids: Optional[List[str]] = None
    occasion: Optional[Occasion] = None
    season: Optional[Season] = None


class OutfitStats(BaseModel):
    total_outfits: int = 0
    by_occasion: Dict[str, int] = Field(default_factory=dict)
    by_season: Dict[str, int] = Field(default_factory=dict)
    favorite_count: int = 0


class OutfitResponse(BaseModel):
    id: str = "outfit_demo_1"
    title: str = "Outfit Recomendado"
    items: List[WardrobeItemResponse] = Field(default_factory=list)
    confidence: float = 0.92
    styling_tips: str = "Combinación armónica de contrastes."


class StylePreferencesCreate(BaseModel):
    dominant_palette: Optional[str] = "AUTUMN"
    preferred_styles: List[ClothingStyle] = Field(default_factory=list)


class StylePreferencesUpdate(BaseModel):
    dominant_palette: Optional[str] = None
    preferred_styles: Optional[List[ClothingStyle]] = None


class StylePreferencesResponse(BaseModel):
    user_id: str
    dominant_palette: str = "AUTUMN"
    preferred_styles: List[ClothingStyle] = Field(default_factory=list)


class ShoppingRecommendationResponse(BaseModel):
    id: str = "rec_1"
    sku: str = "SKU-001"
    title: str = "Recomendación de Compra"
    price: float = 199.0
    image_url: Optional[str] = None
    reason: str = "Complementa tu guardarropa"
    harmony_score: int = 88


class OutfitSuggestion(BaseModel):
    id: str = "sugg_1"
    name: str = "Outfit sugerido"
    occasion: Occasion = Occasion.CASUAL
    score: float = 0.90
    items: List[WardrobeItemResponse] = Field(default_factory=list)
    stylist_advice: Optional[str] = None


class OutfitGenerationResponse(BaseModel):
    suggestions: List[OutfitSuggestion] = Field(default_factory=list)
    analysis: Dict[str, Any] = Field(default_factory=dict)
