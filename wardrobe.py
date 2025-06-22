"""
Endpoints para la gestión de items del armario virtual
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query
from fastapi.security import HTTPBearer

from app.schemas.wardrobe import (
    WardrobeItemCreate, WardrobeItemUpdate, WardrobeItemResponse,
    ClothingCategory, ClothingStyle, Season, Occasion,
    WardrobeStats
)
from app.services.wardrobe_service import WardrobeService
from app.core.security import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter(prefix="/wardrobe", tags=["wardrobe"])

# Inicializar servicio
wardrobe_service = WardrobeService()

@router.post("/items", response_model=WardrobeItemResponse)
async def create_wardrobe_item(
    item_data: WardrobeItemCreate,
    current_user: User = Depends(get_current_user),
    images: List[UploadFile] = File(default=[])
):
    """
    Crear un nuevo item en el armario virtual
    
    - **item_data**: Datos del item a crear
    - **images**: Imágenes del item (máximo 5)
    """
    try:
        # Validar imágenes si se proporcionan
        if images and len(images) > 5:
            raise HTTPException(
                status_code=400,
                detail="Máximo 5 imágenes permitidas por item"
            )
        
        # Validar tipos de archivo
        allowed_types = {"image/jpeg", "image/png", "image/webp"}
        for image in images:
            if image.content_type not in allowed_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Tipo de archivo no soportado: {image.content_type}. "
                          f"Tipos permitidos: {', '.join(allowed_types)}"
                )
        
        result = await wardrobe_service.create_wardrobe_item(
            user_id=current_user.id,
            item_data=item_data,
            image_files=images if images else None
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error creating wardrobe item: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/items", response_model=List[WardrobeItemResponse])
async def get_wardrobe_items(
    current_user: User = Depends(get_current_user),
    category: Optional[ClothingCategory] = Query(None, description="Filtrar por categoría"),
    style: Optional[ClothingStyle] = Query(None, description="Filtrar por estilo"),
    season: Optional[Season] = Query(None, description="Filtrar por temporada"),
    occasion: Optional[Occasion] = Query(None, description="Filtrar por ocasión"),
    color: Optional[str] = Query(None, description="Filtrar por color"),
    is_favorite: Optional[bool] = Query(None, description="Filtrar por favoritos"),
    limit: int = Query(100, ge=1, le=500, description="Límite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginación")
):
    """
    Obtener items del armario con filtros opcionales
    
    Permite filtrar por múltiples criterios para encontrar prendas específicas.
    """
    try:
        items = await wardrobe_service.get_wardrobe_items(
            user_id=current_user.id,
            category=category,
            style=style,
            season=season,
            occasion=occasion,
            color=color,
            is_favorite=is_favorite,
            limit=limit,
            offset=offset
        )
        
        return items
        
    except Exception as e:
        logger.error(f"Error getting wardrobe items: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/items/{item_id}", response_model=WardrobeItemResponse)
async def get_wardrobe_item(
    item_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Obtener un item específico del armario
    
    - **item_id**: ID del item a obtener
    """
    try:
        item = await wardrobe_service.get_wardrobe_item(
            user_id=current_user.id,
            item_id=item_id
        )
        
        if not item:
            raise HTTPException(status_code=404, detail="Item no encontrado")
        
        return item
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting wardrobe item: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/items/{item_id}", response_model=WardrobeItemResponse)
async def update_wardrobe_item(
    item_id: str,
    update_data: WardrobeItemUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Actualizar un item del armario
    
    - **item_id**: ID del item a actualizar
    - **update_data**: Datos a actualizar
    """
    try:
        updated_item = await wardrobe_service.update_wardrobe_item(
            user_id=current_user.id,
            item_id=item_id,
            update_data=update_data
        )
        
        if not updated_item:
            raise HTTPException(status_code=404, detail="Item no encontrado")
        
        return updated_item
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating wardrobe item: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/items/{item_id}")
async def delete_wardrobe_item(
    item_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Eliminar un item del armario
    
    - **item_id**: ID del item a eliminar
    """
    try:
        success = await wardrobe_service.delete_wardrobe_item(
            user_id=current_user.id,
            item_id=item_id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Item no encontrado")
        
        return {"message": "Item eliminado exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting wardrobe item: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/items/{item_id}/wear")
async def record_item_wear(
    item_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Registrar que se usó un item (incrementar contador de uso)
    
    - **item_id**: ID del item usado
    """
    try:
        success = await wardrobe_service.update_item_wear_count(
            user_id=current_user.id,
            item_id=item_id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Item no encontrado")
        
        return {"message": "Uso registrado exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording item wear: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=WardrobeStats)
async def get_wardrobe_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Obtener estadísticas completas del armario
    
    Incluye distribución por categorías, colores, items más usados, etc.
    """
    try:
        stats = await wardrobe_service.get_wardrobe_stats(current_user.id)
        return stats
        
    except Exception as e:
        logger.error(f"Error getting wardrobe stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories")
async def get_clothing_categories():
    """
    Obtener todas las categorías de ropa disponibles
    """
    return {
        "categories": [category.value for category in ClothingCategory],
        "styles": [style.value for style in ClothingStyle],
        "seasons": [season.value for season in Season],
        "occasions": [occasion.value for occasion in Occasion]
    }

@router.post("/items/{item_id}/analyze")
async def analyze_item_ai(
    item_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Re-analizar un item con IA para actualizar tags y análisis
    
    - **item_id**: ID del item a analizar
    """
    try:
        # Obtener el item
        item = await wardrobe_service.get_wardrobe_item(current_user.id, item_id)
        
        if not item:
            raise HTTPException(status_code=404, detail="Item no encontrado")
        
        if not item.image_url:
            raise HTTPException(status_code=400, detail="Item no tiene imágenes para analizar")
        
        # Realizar nuevo análisis con IA
        from app.services.wardrobe_ai_service import WardrobeAIService
        ai_service = WardrobeAIService()
        
        new_analysis = await ai_service.analyze_garment_from_image(
            image_url=item.image_url[0],
            user_context={"user_id": current_user.id}
        )
        
        # Actualizar el item con el nuevo análisis
        update_data = WardrobeItemUpdate(
            ai_analysis=new_analysis,
            ai_tags=ai_service._extract_ai_tags(new_analysis)
        )
        
        updated_item = await wardrobe_service.update_wardrobe_item(
            user_id=current_user.id,
            item_id=item_id,
            update_data=update_data
        )
        
        return {
            "message": "Análisis actualizado exitosamente",
            "analysis": new_analysis,
            "item": updated_item
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing item: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/items/{item_id}/suggestions")
async def get_item_combinations(
    item_id: str,
    current_user: User = Depends(get_current_user),
    occasion: Optional[Occasion] = Query(None, description="Ocasión específica"),
    max_suggestions: int = Query(5, ge=1, le=10, description="Máximo de sugerencias")
):
    """
    Obtener sugerencias de cómo combinar un item específico
    
    - **item_id**: ID del item base
    - **occasion**: Ocasión para las sugerencias (opcional)
    - **max_suggestions**: Número máximo de sugerencias
    """
    try:
        # Obtener el item base
        base_item = await wardrobe_service.get_wardrobe_item(current_user.id, item_id)
        
        if not base_item:
            raise HTTPException(status_code=404, detail="Item no encontrado")
        
        # Generar sugerencias de outfits que incluyan este item
        from app.schemas.wardrobe import OutfitGenerationRequest
        
        generation_request = OutfitGenerationRequest(
            occasion=occasion or Occasion.CASUAL,
            must_include_items=[item_id],
            max_suggestions=max_suggestions
        )
        
        suggestions = await wardrobe_service.generate_outfit_suggestions(
            user_id=current_user.id,
            request=generation_request
        )
        
        return {
            "base_item": base_item,
            "outfit_suggestions": suggestions.suggestions,
            "tips": f"Sugerencias para combinar {base_item.name}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting item combinations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
