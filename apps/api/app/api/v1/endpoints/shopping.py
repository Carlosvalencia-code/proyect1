"""
Endpoints de Shopping y Recomendaciones de Productos
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer

from app.schemas.shopping import (
    ProductRecommendation,
    RecommendationRequest,
    ProductCategory
)
from app.services.shopping_recommendation_service import ShoppingRecommendationService
from app.services.merchant_integration_service import MerchantIntegrationService
from app.api.v1.dependencies.shopping import (
    get_shopping_recommendation_service,
    get_merchant_integration_service,
    get_cache_service,
    get_gemini_service,
    get_wardrobe_ai_service,
    CacheServiceDep,
    GeminiServiceDep,
    WardrobeAIServiceDep,
    MerchantIntegrationServiceDep,
    ShoppingRecommendationServiceDep
)
from app.core.security import get_current_user_id

router = APIRouter()
security = HTTPBearer()


@router.get("/recommendations", response_model=List[ProductRecommendation])
async def get_shopping_recommendations(
    category: Optional[ProductCategory] = None,
    limit: int = Query(default=5, ge=1, le=20),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Obtener recomendaciones de compras personalizadas
    """
    return [
        ProductRecommendation(
            id="rec_demo_1",
            sku="OPT-CAREY-01",
            title="Gafas de Sol Carey Polarizadas",
            category=category or ProductCategory.EYEWEAR,
            price=289.0,
            image_url="https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=500&q=80",
            harmony_score=95,
            match_reason="Armoniza con tu paleta de otoño y rostro ovalado"
        )
    ]


@router.get("/trending", response_model=List[ProductRecommendation])
async def get_trending_products(
    limit: int = Query(default=5, ge=1, le=20)
):
    """
    Obtener productos en tendencia
    """
    return [
        ProductRecommendation(
            id="rec_demo_2",
            sku="OPT-TITAN-02",
            title="Montura Titanio Minimalista",
            category=ProductCategory.EYEWEAR,
            price=349.0,
            image_url="https://images.unsplash.com/photo-1574258495973-f010dfbb5371?w=500&q=80",
            harmony_score=91,
            match_reason="Top ventas en tendencia minimalista"
        )
    ]
