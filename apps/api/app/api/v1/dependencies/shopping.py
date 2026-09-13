# =============================================================================
# SYNTHIA STYLE - SHOPPING DEPENDENCIES
# =============================================================================
# Dependencias para inyección de servicios de shopping

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.services.shopping_recommendation_service import ShoppingRecommendationService
from app.services.merchant_integration_service import MerchantIntegrationService
from app.services.gemini_service import GeminiService
from app.services.cache_service import CacheService
from app.services.wardrobe_ai_service import WardrobeAIService


@lru_cache()
def get_cache_service() -> CacheService:
    """
    Obtiene instancia del servicio de cache
    """
    return CacheService()


@lru_cache()
def get_gemini_service() -> GeminiService:
    """
    Obtiene instancia del servicio de Gemini
    """
    return GeminiService()


@lru_cache()
def get_wardrobe_ai_service(
    gemini_service: Annotated[GeminiService, Depends(get_gemini_service)],
    cache_service: Annotated[CacheService, Depends(get_cache_service)]
) -> WardrobeAIService:
    """
    Obtiene instancia del servicio de AI para armario
    """
    return WardrobeAIService(
        gemini_service=gemini_service,
        cache_service=cache_service
    )


@lru_cache()
def get_merchant_integration_service(
    cache_service: Annotated[CacheService, Depends(get_cache_service)]
) -> MerchantIntegrationService:
    """
    Obtiene instancia del servicio de integración con merchants
    """
    return MerchantIntegrationService(cache_service=cache_service)


@lru_cache()
def get_shopping_recommendation_service(
    gemini_service: Annotated[GeminiService, Depends(get_gemini_service)],
    cache_service: Annotated[CacheService, Depends(get_cache_service)],
    wardrobe_ai_service: Annotated[WardrobeAIService, Depends(get_wardrobe_ai_service)]
) -> ShoppingRecommendationService:
    """
    Obtiene instancia del servicio de recomendaciones de shopping
    """
    return ShoppingRecommendationService(
        gemini_service=gemini_service,
        cache_service=cache_service,
        wardrobe_ai_service=wardrobe_ai_service
    )


# Aliases para facilitar su uso en los endpoints
CacheServiceDep = Annotated[CacheService, Depends(get_cache_service)]
GeminiServiceDep = Annotated[GeminiService, Depends(get_gemini_service)]
WardrobeAIServiceDep = Annotated[WardrobeAIService, Depends(get_wardrobe_ai_service)]
MerchantIntegrationServiceDep = Annotated[MerchantIntegrationService, Depends(get_merchant_integration_service)]
ShoppingRecommendationServiceDep = Annotated[ShoppingRecommendationService, Depends(get_shopping_recommendation_service)]
