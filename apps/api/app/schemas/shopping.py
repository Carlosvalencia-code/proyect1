"""
Esquemas Pydantic para Shopping y Afiliados B2B
"""

from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class AffiliateStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PENDING = "PENDING"
    SUSPENDED = "SUSPENDED"


class ProductCategory(str, Enum):
    EYEWEAR = "EYEWEAR"
    TOPS = "TOPS"
    BOTTOMS = "BOTTOMS"
    DRESSES = "DRESSES"
    OUTERWEAR = "OUTERWEAR"
    ACCESSORIES = "ACCESSORIES"


class MerchantEnum(str, Enum):
    AMAZON = "amazon"
    ASOS = "asos"
    ZARA = "zara"
    HM = "hm"
    UNIQLO = "uniqlo"


class Merchant(BaseModel):
    id: str = "mch_123"
    name: str = "Tienda Demo"
    domain: Optional[str] = "example.com"
    api_key: Optional[str] = None
    is_active: bool = True


class AffiliateEarningResponse(BaseModel):
    id: str = "earn_1"
    merchant_id: str
    amount: float
    currency: str = "USD"
    commission_rate: float = 0.08
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AffiliateEarningsReport(BaseModel):
    merchant_id: str
    total_earnings: float = 0.0
    period_start: datetime = Field(default_factory=datetime.utcnow)
    period_end: datetime = Field(default_factory=datetime.utcnow)
    earnings: List[AffiliateEarningResponse] = Field(default_factory=list)


class RecommendationType(str, Enum):
    SIMILAR = "SIMILAR"
    COMPLEMENTARY = "COMPLEMENTARY"
    TRENDING = "TRENDING"
    COLOR_HARMONY = "COLOR_HARMONY"
    WARDROBE_GAP = "WARDROBE_GAP"


class ProductRecommendation(BaseModel):
    id: str
    sku: str
    title: str
    category: ProductCategory = ProductCategory.EYEWEAR
    price: float
    image_url: str
    harmony_score: int = 90
    match_reason: str = "Armoniza con tu paleta de otoño y rostro ovalado"


class ShoppingRecommendationCreate(BaseModel):
    user_id: str
    product_id: Optional[str] = None
    sku: str
    recommendation_type: RecommendationType = RecommendationType.COLOR_HARMONY
    match_score: float = 85.0
    reason: Optional[str] = None


class ProductSearchFilters(BaseModel):
    query: Optional[str] = None
    category: Optional[ProductCategory] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    merchant_id: Optional[str] = None
    color: Optional[str] = None
    limit: int = 20
    offset: int = 0


class RecommendationRequest(BaseModel):
    user_id: str
    category: Optional[ProductCategory] = None
    limit: int = 5


class ProductCreate(BaseModel):
    sku: str
    title: str
    price: float
    category: ProductCategory
    merchant_id: str
    image_url: str
    product_url: str
    description: Optional[str] = None


class ProductUpdate(BaseModel):
    title: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    product_url: Optional[str] = None


class ProductResponse(BaseModel):
    id: str = "prod_1"
    sku: str
    title: str
    price: float
    category: ProductCategory
    merchant_id: str
    image_url: str
    product_url: str


class ProductSearchResponse(BaseModel):
    total: int = 0
    items: List[ProductResponse] = Field(default_factory=list)


class AffiliateEarningCreate(BaseModel):
    merchant_id: str
    amount: float
    currency: str = "USD"
    commission_rate: float = 0.08
