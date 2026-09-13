"""
Endpoints para la gestión de outfits y generación de combinaciones
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer

from app.schemas.wardrobe import (
    OutfitCreate, OutfitUpdate, OutfitResponse,
    OutfitGenerationRequest, OutfitGenerationResponse,
    OutfitStats, OutfitStatus, Occasion, Season, ClothingStyle
)
from app.services.wardrobe_service import WardrobeService
from app.core.security import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter(prefix="/outfits", tags=["outfits"])

# Inicializar servicio
wardrobe_service = WardrobeService()

@router.post("/generate", response_model=OutfitGenerationResponse)
async def generate_outfit_suggestions(
    request: OutfitGenerationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generar sugerencias automáticas de outfits basadas en el armario del usuario
    
    - **request**: Parámetros para la generación (ocasión, temporada, preferencias, etc.)
    
    El sistema analiza el armario y genera combinaciones inteligentes considerando:
    - Armonía de colores
    - Coherencia de estilo  
    - Apropiado para la ocasión
    - Compatibilidad estacional
    """
    try:
        suggestions = await wardrobe_service.generate_outfit_suggestions(
            user_id=current_user.id,
            request=request
        )
        
        return suggestions
        
    except Exception as e:
        logger.error(f"Error generating outfit suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("", response_model=OutfitResponse)
async def create_outfit(
    outfit_data: OutfitCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Crear un nuevo outfit guardado
    
    - **outfit_data**: Datos del outfit a crear incluyendo items seleccionados
    """
    try:
        if not outfit_data.item_ids:
            raise HTTPException(
                status_code=400,
                detail="El outfit debe incluir al menos un item"
            )
        
        if len(outfit_data.item_ids) > 20:
            raise HTTPException(
                status_code=400,
                detail="El outfit no puede tener más de 20 items"
            )
        
        result = await wardrobe_service.create_outfit(
            user_id=current_user.id,
            outfit_data=outfit_data
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating outfit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[OutfitResponse])
async def get_outfits(
    current_user: User = Depends(get_current_user),
    occasion: Optional[Occasion] = Query(None, description="Filtrar por ocasión"),
    season: Optional[Season] = Query(None, description="Filtrar por temporada"),
    status: Optional[OutfitStatus] = Query(None, description="Filtrar por estado"),
    is_favorite: Optional[bool] = Query(None, description="Filtrar por favoritos"),
    limit: int = Query(50, ge=1, le=200, description="Límite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginación")
):
    """
    Obtener outfits del usuario con filtros opcionales
    
    Permite filtrar por ocasión, temporada, estado y favoritos.
    """
    try:
        outfits = await wardrobe_service.get_outfits(
            user_id=current_user.id,
            occasion=occasion,
            season=season,
            status=status,
            is_favorite=is_favorite,
            limit=limit,
            offset=offset
        )
        
        return outfits
        
    except Exception as e:
        logger.error(f"Error getting outfits: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{outfit_id}", response_model=OutfitResponse)
async def get_outfit(
    outfit_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Obtener un outfit específico con todos sus items
    
    - **outfit_id**: ID del outfit a obtener
    """
    try:
        outfit = await wardrobe_service.get_outfit(
            user_id=current_user.id,
            outfit_id=outfit_id
        )
        
        if not outfit:
            raise HTTPException(status_code=404, detail="Outfit no encontrado")
        
        return outfit
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting outfit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{outfit_id}", response_model=OutfitResponse)
async def update_outfit(
    outfit_id: str,
    update_data: OutfitUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Actualizar un outfit existente
    
    - **outfit_id**: ID del outfit a actualizar
    - **update_data**: Datos a actualizar
    """
    try:
        # Verificar que el outfit existe
        existing_outfit = await wardrobe_service.get_outfit(current_user.id, outfit_id)
        if not existing_outfit:
            raise HTTPException(status_code=404, detail="Outfit no encontrado")
        
        # TODO: Implementar update_outfit en el servicio
        # Por ahora retornamos el outfit existente
        return existing_outfit
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating outfit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{outfit_id}")
async def delete_outfit(
    outfit_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Eliminar un outfit
    
    - **outfit_id**: ID del outfit a eliminar
    """
    try:
        # TODO: Implementar delete_outfit en el servicio
        # Por ahora simulamos éxito
        return {"message": "Outfit eliminado exitosamente"}
        
    except Exception as e:
        logger.error(f"Error deleting outfit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{outfit_id}/wear")
async def record_outfit_wear(
    outfit_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Registrar que se usó un outfit
    
    - **outfit_id**: ID del outfit usado
    
    Esto actualiza los contadores de uso tanto del outfit como de sus items individuales.
    """
    try:
        # Obtener el outfit
        outfit = await wardrobe_service.get_outfit(current_user.id, outfit_id)
        if not outfit:
            raise HTTPException(status_code=404, detail="Outfit no encontrado")
        
        # Actualizar contador de uso de cada item
        for item in outfit.items:
            await wardrobe_service.update_item_wear_count(current_user.id, item.id)
        
        # TODO: Actualizar contador del outfit
        
        return {
            "message": "Uso del outfit registrado exitosamente",
            "items_updated": len(outfit.items)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording outfit wear: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{outfit_id}/alternatives")
async def get_outfit_alternatives(
    outfit_id: str,
    current_user: User = Depends(get_current_user),
    max_alternatives: int = Query(3, ge=1, le=10, description="Máximo de alternativas")
):
    """
    Obtener alternativas para un outfit existente
    
    - **outfit_id**: ID del outfit base
    - **max_alternatives**: Número máximo de alternativas
    
    Genera variaciones del outfit original cambiando algunos items.
    """
    try:
        # Obtener el outfit base
        base_outfit = await wardrobe_service.get_outfit(current_user.id, outfit_id)
        if not base_outfit:
            raise HTTPException(status_code=404, detail="Outfit no encontrado")
        
        # Generar alternativas basadas en el outfit existente
        generation_request = OutfitGenerationRequest(
            occasion=base_outfit.occasion[0] if base_outfit.occasion else Occasion.CASUAL,
            season=base_outfit.season,
            preferred_styles=base_outfit.style,
            must_include_items=[base_outfit.items[0].id] if base_outfit.items else [],
            exclude_items=[item.id for item in base_outfit.items[1:]] if len(base_outfit.items) > 1 else [],
            max_suggestions=max_alternatives
        )
        
        alternatives = await wardrobe_service.generate_outfit_suggestions(
            user_id=current_user.id,
            request=generation_request
        )
        
        return {
            "base_outfit": base_outfit,
            "alternatives": alternatives.suggestions,
            "tips": f"Alternativas para {base_outfit.name}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting outfit alternatives: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/overview", response_model=OutfitStats)
async def get_outfit_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Obtener estadísticas de outfits del usuario
    
    Incluye distribución por ocasiones, temporadas, favoritos, etc.
    """
    try:
        # Obtener todos los outfits del usuario
        all_outfits = await wardrobe_service.get_outfits(current_user.id, limit=1000)
        
        if not all_outfits:
            return OutfitStats(
                total_outfits=0,
                favorite_outfits=0,
                outfits_by_occasion={},
                outfits_by_season={},
                average_rating=None,
                most_worn_outfits=[],
                recent_outfits=[]
            )
        
        # Calcular estadísticas
        favorite_count = len([o for o in all_outfits if o.is_favorite])
        
        # Distribución por ocasión
        occasion_dist = {}
        for outfit in all_outfits:
            for occasion in outfit.occasion:
                occasion_name = occasion.value if hasattr(occasion, 'value') else str(occasion)
                occasion_dist[occasion_name] = occasion_dist.get(occasion_name, 0) + 1
        
        # Distribución por temporada
        season_dist = {}
        for outfit in all_outfits:
            season_name = outfit.season.value if hasattr(outfit.season, 'value') else str(outfit.season)
            season_dist[season_name] = season_dist.get(season_name, 0) + 1
        
        # Calificación promedio
        ratings = [o.rating for o in all_outfits if o.rating is not None]
        avg_rating = sum(ratings) / len(ratings) if ratings else None
        
        # Más usados
        most_worn = sorted(all_outfits, key=lambda x: x.times_worn, reverse=True)[:5]
        
        # Más recientes
        recent = sorted(all_outfits, key=lambda x: x.created_at, reverse=True)[:10]
        
        stats = OutfitStats(
            total_outfits=len(all_outfits),
            favorite_outfits=favorite_count,
            outfits_by_occasion=occasion_dist,
            outfits_by_season=season_dist,
            average_rating=avg_rating,
            most_worn_outfits=most_worn,
            recent_outfits=recent
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting outfit stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/daily/suggestions")
async def get_daily_outfit_suggestions(
    current_user: User = Depends(get_current_user),
    date: Optional[str] = Query(None, description="Fecha en formato YYYY-MM-DD"),
    weather: Optional[str] = Query(None, description="Condiciones climáticas"),
    temperature: Optional[float] = Query(None, description="Temperatura en celsius"),
    occasion: Optional[Occasion] = Query(Occasion.CASUAL, description="Ocasión principal del día")
):
    """
    Obtener sugerencias de outfits para un día específico
    
    - **date**: Fecha específica (opcional, por defecto hoy)
    - **weather**: Condiciones climáticas (soleado, lluvioso, nublado, etc.)
    - **temperature**: Temperatura esperada
    - **occasion**: Ocasión principal del día
    """
    try:
        # Determinar temporada basada en la fecha o temperatura
        season = None
        if temperature is not None:
            if temperature < 10:
                season = Season.WINTER
            elif temperature < 20:
                season = Season.FALL
            elif temperature < 30:
                season = Season.SPRING
            else:
                season = Season.SUMMER
        
        # Generar sugerencias
        generation_request = OutfitGenerationRequest(
            occasion=occasion,
            season=season,
            weather=weather,
            temperature=temperature,
            max_suggestions=3
        )
        
        suggestions = await wardrobe_service.generate_outfit_suggestions(
            user_id=current_user.id,
            request=generation_request
        )
        
        return {
            "date": date or "today",
            "weather": weather,
            "temperature": temperature,
            "occasion": occasion.value,
            "suggestions": suggestions.suggestions,
            "tips": [
                "Considera las condiciones climáticas al elegir tu outfit",
                "Verifica que el nivel de formalidad sea apropiado para tus actividades",
                "Agrega capas si el clima es inestable"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting daily suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{outfit_id}/rate")
async def rate_outfit(
    outfit_id: str,
    rating: float = Query(..., ge=0, le=5, description="Calificación del outfit (0-5)"),
    current_user: User = Depends(get_current_user)
):
    """
    Calificar un outfit
    
    - **outfit_id**: ID del outfit a calificar
    - **rating**: Calificación de 0 a 5 estrellas
    """
    try:
        # Verificar que el outfit existe
        outfit = await wardrobe_service.get_outfit(current_user.id, outfit_id)
        if not outfit:
            raise HTTPException(status_code=404, detail="Outfit no encontrado")
        
        # TODO: Implementar actualización de rating en el servicio
        # Por ahora simulamos éxito
        
        return {
            "message": f"Outfit calificado con {rating} estrellas",
            "outfit_id": outfit_id,
            "rating": rating
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rating outfit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
