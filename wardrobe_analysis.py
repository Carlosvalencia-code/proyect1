"""
Endpoints para análisis del armario y recomendaciones de compras
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer

from app.schemas.wardrobe import (
    WardrobeAnalysisType, WardrobeAnalysisResponse,
    ShoppingRecommendationResponse, StylePreferencesCreate,
    StylePreferencesUpdate, StylePreferencesResponse
)
from app.services.wardrobe_service import WardrobeService
from app.core.security import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter(prefix="/wardrobe", tags=["wardrobe-analysis"])

# Inicializar servicio
wardrobe_service = WardrobeService()

@router.post("/analyze", response_model=WardrobeAnalysisResponse)
async def analyze_wardrobe(
    analysis_type: WardrobeAnalysisType = Query(..., description="Tipo de análisis a realizar"),
    current_user: User = Depends(get_current_user)
):
    """
    Realizar análisis completo del armario
    
    - **analysis_type**: Tipo de análisis:
        - VERSATILITY: Analiza qué tan versátiles son las prendas
        - COLOR_HARMONY: Analiza la armonía de colores del armario
        - GAPS_ANALYSIS: Identifica qué falta en el armario
        - COST_PER_WEAR: Analiza el valor por uso de las prendas
        - SEASONAL_DISTRIBUTION: Analiza distribución por temporadas
        - STYLE_ANALYSIS: Analiza coherencia de estilos
    """
    try:
        analysis = await wardrobe_service.analyze_wardrobe(
            user_id=current_user.id,
            analysis_type=analysis_type
        )
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing wardrobe: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/history", response_model=List[WardrobeAnalysisResponse])
async def get_analysis_history(
    current_user: User = Depends(get_current_user),
    analysis_type: WardrobeAnalysisType = Query(None, description="Filtrar por tipo de análisis"),
    limit: int = Query(10, ge=1, le=50, description="Límite de resultados")
):
    """
    Obtener historial de análisis del armario
    
    - **analysis_type**: Filtrar por tipo específico de análisis (opcional)
    - **limit**: Número máximo de análisis a retornar
    """
    try:
        # TODO: Implementar get_analysis_history en el servicio
        # Por ahora retornamos lista vacía
        return []
        
    except Exception as e:
        logger.error(f"Error getting analysis history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendations/shopping", response_model=List[ShoppingRecommendationResponse])
async def get_shopping_recommendations(
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100, description="Límite de recomendaciones"),
    priority_min: float = Query(0, ge=0, le=10, description="Prioridad mínima"),
    budget_max: float = Query(None, ge=0, description="Presupuesto máximo")
):
    """
    Obtener recomendaciones de compras personalizadas
    
    - **limit**: Número máximo de recomendaciones
    - **priority_min**: Prioridad mínima de las recomendaciones (0-10)
    - **budget_max**: Presupuesto máximo por item
    
    Las recomendaciones se basan en:
    - Análisis de gaps en el armario
    - Preferencias de estilo del usuario
    - Presupuesto y marcas preferidas
    - Tendencias actuales
    """
    try:
        # Primero realizar análisis de gaps si no existe uno reciente
        gaps_analysis = await wardrobe_service.analyze_wardrobe(
            user_id=current_user.id,
            analysis_type=WardrobeAnalysisType.GAPS_ANALYSIS
        )
        
        # TODO: Implementar generación de recomendaciones de compras
        # Por ahora retornamos lista vacía
        return []
        
    except Exception as e:
        logger.error(f"Error getting shopping recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recommendations/shopping/{recommendation_id}/action")
async def update_recommendation_action(
    recommendation_id: str,
    action: str = Query(..., regex="^(viewed|clicked|purchased|rejected)$"),
    current_user: User = Depends(get_current_user)
):
    """
    Actualizar acción realizada en una recomendación
    
    - **recommendation_id**: ID de la recomendación
    - **action**: Acción realizada (viewed, clicked, purchased, rejected)
    
    Esto ayuda al sistema a aprender y mejorar futuras recomendaciones.
    """
    try:
        # TODO: Implementar actualización de acciones en recomendaciones
        return {
            "message": f"Acción '{action}' registrada para recomendación {recommendation_id}",
            "recommendation_id": recommendation_id,
            "action": action
        }
        
    except Exception as e:
        logger.error(f"Error updating recommendation action: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/preferences/style", response_model=StylePreferencesResponse)
async def get_style_preferences(
    current_user: User = Depends(get_current_user)
):
    """
    Obtener preferencias de estilo del usuario
    
    Las preferencias incluyen estilos favoritos, colores preferidos,
    presupuesto, marcas favoritas, etc.
    """
    try:
        # TODO: Implementar get_style_preferences en el servicio
        # Por ahora retornamos preferencias vacías
        from app.schemas.wardrobe import StylePreferencesResponse
        return StylePreferencesResponse(
            id="temp_id",
            user_id=current_user.id,
            preferred_styles=[],
            avoided_styles=[],
            preferred_colors=[],
            avoided_colors=[],
            primary_occasions=[],
            preferred_brands=[],
            budget_range={},
            preferred_fit=[],
            comfort_priority=5.0,
            preferred_seasons=[],
            heat_tolerance=5.0,
            cold_tolerance=5.0,
            adventurousness=5.0,
            brand_loyalty=5.0,
            sustainability_importance=5.0,
            interaction_data=None,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        )
        
    except Exception as e:
        logger.error(f"Error getting style preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/preferences/style", response_model=StylePreferencesResponse)
async def create_style_preferences(
    preferences: StylePreferencesCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Crear o actualizar preferencias de estilo del usuario
    
    - **preferences**: Preferencias de estilo completas
    
    Estas preferencias se usan para:
    - Personalizar recomendaciones de outfits
    - Generar sugerencias de compras más relevantes
    - Mejorar el análisis del armario
    """
    try:
        # TODO: Implementar create_style_preferences en el servicio
        return StylePreferencesResponse(
            id="temp_id",
            user_id=current_user.id,
            **preferences.dict(),
            interaction_data=None,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        )
        
    except Exception as e:
        logger.error(f"Error creating style preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/preferences/style", response_model=StylePreferencesResponse)
async def update_style_preferences(
    preferences: StylePreferencesUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Actualizar preferencias de estilo existentes
    
    - **preferences**: Campos de preferencias a actualizar
    """
    try:
        # TODO: Implementar update_style_preferences en el servicio
        return StylePreferencesResponse(
            id="temp_id",
            user_id=current_user.id,
            preferred_styles=[],
            avoided_styles=[],
            preferred_colors=[],
            avoided_colors=[],
            primary_occasions=[],
            preferred_brands=[],
            budget_range={},
            preferred_fit=[],
            comfort_priority=5.0,
            preferred_seasons=[],
            heat_tolerance=5.0,
            cold_tolerance=5.0,
            adventurousness=5.0,
            brand_loyalty=5.0,
            sustainability_importance=5.0,
            interaction_data=None,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        )
        
    except Exception as e:
        logger.error(f"Error updating style preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights/color-palette")
async def get_color_palette_insights(
    current_user: User = Depends(get_current_user)
):
    """
    Obtener insights sobre la paleta de colores del armario
    
    Analiza los colores dominantes, combinaciones más usadas,
    y sugiere colores que podrían complementar el armario.
    """
    try:
        # Obtener items del armario
        wardrobe_items = await wardrobe_service.get_wardrobe_items(
            user_id=current_user.id,
            limit=1000
        )
        
        if not wardrobe_items:
            return {
                "message": "No hay suficientes items para analizar la paleta de colores",
                "color_distribution": {},
                "suggestions": []
            }
        
        # Analizar distribución de colores
        color_counts = {}
        for item in wardrobe_items:
            color = item.color.lower()
            color_counts[color] = color_counts.get(color, 0) + 1
            
            for secondary in item.secondary_colors:
                color = secondary.lower()
                color_counts[color] = color_counts.get(color, 0) + 0.5
        
        # Colores dominantes
        sorted_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)
        dominant_colors = [color for color, count in sorted_colors[:5]]
        
        # Sugerencias de colores complementarios
        neutral_colors = ["black", "white", "gray", "navy", "beige", "brown"]
        missing_neutrals = [color for color in neutral_colors if color not in color_counts]
        
        suggestions = []
        if missing_neutrals:
            suggestions.append(f"Considera agregar piezas en {missing_neutrals[0]} para mayor versatilidad")
        
        if len(color_counts) < 5:
            suggestions.append("Tu armario tiene pocos colores. Agregar más variedad podría crear más combinaciones")
        
        return {
            "color_distribution": dict(sorted_colors),
            "dominant_colors": dominant_colors,
            "color_diversity_score": min(100, len(color_counts) * 10),
            "missing_neutrals": missing_neutrals,
            "suggestions": suggestions,
            "total_items_analyzed": len(wardrobe_items)
        }
        
    except Exception as e:
        logger.error(f"Error getting color palette insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights/versatility")
async def get_versatility_insights(
    current_user: User = Depends(get_current_user)
):
    """
    Obtener insights sobre la versatilidad del armario
    
    Identifica las piezas más y menos versátiles,
    y sugiere cómo mejorar la versatilidad general.
    """
    try:
        # Obtener items del armario
        wardrobe_items = await wardrobe_service.get_wardrobe_items(
            user_id=current_user.id,
            limit=1000
        )
        
        if not wardrobe_items:
            return {
                "message": "No hay items para analizar versatilidad",
                "versatility_score": 0
            }
        
        # Calcular métricas de versatilidad
        versatility_scores = [item.versatility_score or 50 for item in wardrobe_items]
        avg_versatility = sum(versatility_scores) / len(versatility_scores)
        
        # Items más y menos versátiles
        sorted_by_versatility = sorted(
            wardrobe_items,
            key=lambda x: x.versatility_score or 50,
            reverse=True
        )
        
        most_versatile = sorted_by_versatility[:5]
        least_versatile = sorted_by_versatility[-5:]
        
        # Análisis por categoría
        category_versatility = {}
        for item in wardrobe_items:
            category = item.category.value
            if category not in category_versatility:
                category_versatility[category] = []
            category_versatility[category].append(item.versatility_score or 50)
        
        # Promedio por categoría
        avg_by_category = {
            category: sum(scores) / len(scores)
            for category, scores in category_versatility.items()
        }
        
        # Generar sugerencias
        suggestions = []
        if avg_versatility < 60:
            suggestions.append("Tu armario tiene baja versatilidad. Considera invertir en piezas básicas de calidad")
        
        # Identificar categorías con baja versatilidad
        low_versatility_categories = [
            category for category, score in avg_by_category.items() if score < 50
        ]
        
        if low_versatility_categories:
            suggestions.append(f"Las categorías {', '.join(low_versatility_categories)} necesitan piezas más versátiles")
        
        return {
            "overall_versatility_score": avg_versatility,
            "most_versatile_items": [
                {"name": item.name, "score": item.versatility_score, "category": item.category.value}
                for item in most_versatile
            ],
            "least_versatile_items": [
                {"name": item.name, "score": item.versatility_score, "category": item.category.value}
                for item in least_versatile
            ],
            "versatility_by_category": avg_by_category,
            "suggestions": suggestions,
            "total_items_analyzed": len(wardrobe_items)
        }
        
    except Exception as e:
        logger.error(f"Error getting versatility insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights/cost-efficiency")
async def get_cost_efficiency_insights(
    current_user: User = Depends(get_current_user)
):
    """
    Obtener insights sobre la eficiencia de costos del armario
    
    Analiza el costo por uso, identifica las mejores y peores inversiones,
    y sugiere formas de optimizar futuras compras.
    """
    try:
        # Obtener items del armario
        wardrobe_items = await wardrobe_service.get_wardrobe_items(
            user_id=current_user.id,
            limit=1000
        )
        
        # Filtrar items con datos de precio y uso
        items_with_data = [
            item for item in wardrobe_items
            if item.purchase_price and item.times_worn > 0 and item.cost_per_wear
        ]
        
        if not items_with_data:
            return {
                "message": "No hay suficientes datos de precio y uso para el análisis",
                "suggestions": [
                    "Agrega información de precio de compra a tus items",
                    "Registra cuando uses tus prendas para calcular el costo por uso"
                ]
            }
        
        # Calcular métricas
        total_investment = sum(float(item.purchase_price) for item in items_with_data)
        cost_per_wear_values = [float(item.cost_per_wear) for item in items_with_data]
        avg_cost_per_wear = sum(cost_per_wear_values) / len(cost_per_wear_values)
        
        # Mejores y peores inversiones
        sorted_by_value = sorted(items_with_data, key=lambda x: float(x.cost_per_wear))
        best_investments = sorted_by_value[:5]
        worst_investments = sorted_by_value[-5:]
        
        # Items subutilizados (alto costo por uso)
        underutilized = [item for item in items_with_data if float(item.cost_per_wear) > avg_cost_per_wear * 2]
        
        # Generar sugerencias
        suggestions = []
        if avg_cost_per_wear > 10:
            suggestions.append("Tu costo promedio por uso es alto. Considera usar más tus prendas existentes")
        
        if underutilized:
            suggestions.append(f"Tienes {len(underutilized)} prendas subutilizadas. Intenta incorporarlas más en tus outfits")
        
        suggestions.append("Invierte en piezas básicas de calidad que puedas usar frecuentemente")
        
        return {
            "total_investment": total_investment,
            "average_cost_per_wear": avg_cost_per_wear,
            "best_investments": [
                {
                    "name": item.name,
                    "cost_per_wear": float(item.cost_per_wear),
                    "times_worn": item.times_worn,
                    "purchase_price": float(item.purchase_price)
                }
                for item in best_investments
            ],
            "worst_investments": [
                {
                    "name": item.name,
                    "cost_per_wear": float(item.cost_per_wear),
                    "times_worn": item.times_worn,
                    "purchase_price": float(item.purchase_price)
                }
                for item in worst_investments
            ],
            "underutilized_items": len(underutilized),
            "suggestions": suggestions,
            "items_analyzed": len(items_with_data)
        }
        
    except Exception as e:
        logger.error(f"Error getting cost efficiency insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
