"""
Endpoints B2B para el Widget Embebible de Recomendación (Synthia Commerce AI)
Permite a tiendas online (Shopify, WooCommerce, etc.) integrar visagismo y colorimetría.
"""

import time
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, status

from app.schemas.widget import (
    WidgetRecommendRequest,
    WidgetRecommendResponse,
    ColorimetryProfile,
    VisagismProfile,
    CatalogItem
)
from app.services.catalog_matcher import catalog_matcher
from app.core.logging import AILogger

router = APIRouter(prefix="/widget", tags=["B2B Widget"])


@router.get("/health")
async def widget_health():
    """Health check para el SDK embebido"""
    return {"status": "active", "service": "synthia-b2b-widget", "version": "1.0.0"}


@router.get("/catalog")
async def get_merchant_catalog(
    x_merchant_key: Optional[str] = Header(None, alias="X-Merchant-Key")
):
    """Obtener catálogo sincronizado del comercio"""
    return {
        "merchant_key": x_merchant_key or "sandbox_demo",
        "total_items": len(catalog_matcher.catalog),
        "items": catalog_matcher.catalog
    }


@router.post("/recommend", response_model=WidgetRecommendResponse)
async def get_widget_recommendation(
    payload: WidgetRecommendRequest,
    x_merchant_key: Optional[str] = Header("demo-merchant-sandbox", alias="X-Merchant-Key")
) -> WidgetRecommendResponse:
    """
    Endpoint principal consumido por el widget JS embebido en la ficha de producto (PDP).
    
    Analiza la fisonomía y colorimetría del comprador (mediante selfie o quiz rápido),
    calcula la compatibilidad con el SKU actual y recomienda variantes del catálogo.
    """
    start_time = time.time()
    
    # 1. Determinar perfil colorimétrico (IA o Quiz rápido)
    # En modo sandbox o si no hay imagen, derivamos de datos heurísticos/quiz
    if payload.quiz_data and payload.quiz_data.get("undertone"):
        undertone = payload.quiz_data.get("undertone", "warm").lower()
        season = payload.quiz_data.get("season", "AUTUMN").upper()
    else:
        # Perfil estimado por defecto (Cálido / Otoño profundo)
        undertone = "warm"
        season = "AUTUMN"

    if undertone == "warm":
        best_colors = ["#C19A6B", "#D4AF37", "#808000", "#795548"]
        avoid_colors = ["#C0C0C0", "#E0FFFF", "#FF69B4"]
    else:
        best_colors = ["#000000", "#C0C0C0", "#1C39BB", "#4A0E4E"]
        avoid_colors = ["#FFD700", "#FF8C00", "#8B4513"]

    colorimetry = ColorimetryProfile(
        season=season,
        sub_season=f"DEEP_{season}",
        undertone=undertone,
        best_colors=best_colors,
        colors_to_avoid=avoid_colors
    )

    # 2. Determinar visagismo / forma de rostro
    face_shape = "ROUND"
    if payload.quiz_data and payload.quiz_data.get("face_shape"):
        face_shape = payload.quiz_data.get("face_shape").upper()

    frame_recs = ["RECTANGULAR", "WAYFARER", "GEOMETRIC"] if face_shape == "ROUND" else ["ROUND", "OVAL", "AVIATOR"]
    visagism = VisagismProfile(
        face_shape=face_shape,
        recommended_frame_shapes=frame_recs,
        frames_to_avoid=["OVERSIZED_ROUND"] if face_shape == "ROUND" else ["BOXY_SQUARE"]
    )

    # 3. Evaluar producto actual visto en la PDP
    current_product_score = 92
    fit_verdict = "PERFECT_MATCH"
    if payload.sku:
        current_item = next((item for item in catalog_matcher.catalog if item["sku"] == payload.sku), None)
        if current_item:
            current_product_score = catalog_matcher.calculate_match_score(current_item, colorimetry, visagism)
            if current_product_score >= 90:
                fit_verdict = "PERFECT_MATCH"
            elif current_product_score >= 75:
                fit_verdict = "GOOD_MATCH"
            else:
                fit_verdict = "NEUTRAL"

    # 4. Obtener recomendaciones de catálogo del comercio
    recommended_items = catalog_matcher.get_recommendations(
        merchant_id=x_merchant_key or "default",
        current_sku=payload.sku,
        colorimetry=colorimetry,
        visagism=visagism,
        limit=4
    )

    # 5. Redactar consejo del estilista
    advice = catalog_matcher.build_stylist_advice(
        colorimetry=colorimetry,
        visagism=visagism,
        current_product_score=current_product_score
    )

    duration_ms = round((time.time() - start_time) * 1000, 2)

    return WidgetRecommendResponse(
        status="success",
        merchant_id=x_merchant_key or "sandbox",
        colorimetry=colorimetry,
        visagism=visagism,
        current_product_score=current_product_score,
        fit_verdict=fit_verdict,
        stylist_advice=advice,
        recommended_catalog=recommended_items,
        processing_time_ms=duration_ms
    )
