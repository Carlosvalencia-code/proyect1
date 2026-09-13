"""
Servicio principal para el manejo del armario virtual en Synthia Style
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, and_, or_
from sqlalchemy.orm import selectinload

from app.db.database import get_database
from app.models.user import User
from app.schemas.wardrobe import *
from app.services.wardrobe_ai_service import WardrobeAIService
from app.services.file_service import FileService
from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)

class WardrobeService:
    """Servicio principal para el armario virtual"""
    
    def __init__(self):
        self.ai_service = WardrobeAIService()
        self.file_service = FileService()
        self.cache_service = CacheService()
    
    # =============================================================================
    # GESTIÓN DE ITEMS DEL ARMARIO
    # =============================================================================
    
    async def create_wardrobe_item(
        self,
        user_id: str,
        item_data: WardrobeItemCreate,
        image_files: List[Any] = None
    ) -> WardrobeItemResponse:
        """Crear un nuevo item en el armario"""
        
        try:
            async with get_database() as db:
                # Verificar límites de suscripción
                await self._check_wardrobe_limits(user_id, db)
                
                # Procesar imágenes si las hay
                image_urls = []
                thumbnail_url = None
                
                if image_files:
                    upload_results = await self._process_item_images(user_id, image_files)
                    image_urls = upload_results.get("image_urls", [])
                    thumbnail_url = upload_results.get("thumbnail_url")
                    
                    # Analizar la primera imagen con IA si está disponible
                    if image_urls:
                        ai_analysis = await self.ai_service.analyze_garment_from_image(
                            image_urls[0], {"user_id": user_id}
                        )
                    else:
                        ai_analysis = None
                else:
                    ai_analysis = None
                
                # Crear el item en la base de datos
                item_dict = item_data.dict()
                item_dict.update({
                    "user_id": user_id,
                    "image_url": image_urls,
                    "thumbnail_url": thumbnail_url,
                    "ai_analysis": ai_analysis,
                    "ai_tags": self._extract_ai_tags(ai_analysis) if ai_analysis else []
                })
                
                # Convertir enums a strings para la base de datos
                item_dict = self._prepare_item_for_db(item_dict)
                
                # Insertar en la base de datos usando SQL directo
                query = """
                INSERT INTO wardrobe_items (
                    id, user_id, name, description, brand, size, color, secondary_colors,
                    category, subcategory, style, material, care_instructions, fit_type,
                    season, occasions, purchase_date, purchase_price, purchase_store,
                    image_url, thumbnail_url, tags, ai_tags, ai_analysis, is_favorite,
                    created_at, updated_at
                ) VALUES (
                    gen_random_uuid(), :user_id, :name, :description, :brand, :size, :color, 
                    :secondary_colors, :category, :subcategory, :style, :material, 
                    :care_instructions, :fit_type, :season, :occasions, :purchase_date, 
                    :purchase_price, :purchase_store, :image_url, :thumbnail_url, :tags, 
                    :ai_tags, :ai_analysis, :is_favorite, NOW(), NOW()
                ) RETURNING *
                """
                
                result = await db.execute(query, item_dict)
                new_item = result.fetchone()
                
                # Limpiar caché del usuario
                await self._invalidate_user_wardrobe_cache(user_id)
                
                # Convertir a response schema
                response = WardrobeItemResponse(**dict(new_item))
                
                logger.info(f"Created wardrobe item {response.id} for user {user_id}")
                return response
                
        except Exception as e:
            logger.error(f"Error creating wardrobe item: {str(e)}")
            raise Exception(f"Error al crear el item del armario: {str(e)}")
    
    async def get_wardrobe_items(
        self,
        user_id: str,
        category: Optional[ClothingCategory] = None,
        style: Optional[ClothingStyle] = None,
        season: Optional[Season] = None,
        occasion: Optional[Occasion] = None,
        color: Optional[str] = None,
        is_favorite: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[WardrobeItemResponse]:
        """Obtener items del armario con filtros"""
        
        try:
            # Intentar obtener desde caché
            cache_key = f"wardrobe_items:{user_id}:{category}:{style}:{season}:{occasion}:{color}:{is_favorite}:{limit}:{offset}"
            cached_result = await self.cache_service.get(cache_key)
            
            if cached_result:
                return [WardrobeItemResponse(**item) for item in cached_result]
            
            async with get_database() as db:
                # Construir query con filtros
                query = "SELECT * FROM wardrobe_items WHERE user_id = :user_id AND is_active = true"
                params = {"user_id": user_id}
                
                if category:
                    query += " AND category = :category"
                    params["category"] = category.value
                
                if style:
                    query += " AND :style = ANY(style)"
                    params["style"] = style.value
                
                if season:
                    query += " AND :season = ANY(season)"
                    params["season"] = season.value
                
                if occasion:
                    query += " AND :occasion = ANY(occasions)"
                    params["occasion"] = occasion.value
                
                if color:
                    query += " AND (LOWER(color) LIKE :color OR :color = ANY(ARRAY(SELECT LOWER(unnest(secondary_colors)))))"
                    params["color"] = f"%{color.lower()}%"
                
                if is_favorite is not None:
                    query += " AND is_favorite = :is_favorite"
                    params["is_favorite"] = is_favorite
                
                query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
                params["limit"] = limit
                params["offset"] = offset
                
                result = await db.execute(query, params)
                items = result.fetchall()
                
                # Convertir a response schemas
                response_items = [WardrobeItemResponse(**dict(item)) for item in items]
                
                # Cachear resultado
                await self.cache_service.set(
                    cache_key,
                    [item.dict() for item in response_items],
                    expire=300  # 5 minutos
                )
                
                return response_items
                
        except Exception as e:
            logger.error(f"Error getting wardrobe items: {str(e)}")
            raise Exception(f"Error al obtener items del armario: {str(e)}")
    
    async def get_wardrobe_item(self, user_id: str, item_id: str) -> Optional[WardrobeItemResponse]:
        """Obtener un item específico del armario"""
        
        try:
            async with get_database() as db:
                query = """
                SELECT * FROM wardrobe_items 
                WHERE id = :item_id AND user_id = :user_id AND is_active = true
                """
                
                result = await db.execute(query, {"item_id": item_id, "user_id": user_id})
                item = result.fetchone()
                
                if not item:
                    return None
                
                return WardrobeItemResponse(**dict(item))
                
        except Exception as e:
            logger.error(f"Error getting wardrobe item: {str(e)}")
            return None
    
    async def update_wardrobe_item(
        self,
        user_id: str,
        item_id: str,
        update_data: WardrobeItemUpdate
    ) -> Optional[WardrobeItemResponse]:
        """Actualizar un item del armario"""
        
        try:
            async with get_database() as db:
                # Verificar que el item pertenezca al usuario
                existing_item = await self.get_wardrobe_item(user_id, item_id)
                if not existing_item:
                    return None
                
                # Preparar datos de actualización
                update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
                update_dict["updated_at"] = datetime.now()
                
                # Convertir enums a strings
                update_dict = self._prepare_item_for_db(update_dict)
                
                # Construir query de actualización dinámicamente
                set_clauses = []
                params = {"item_id": item_id, "user_id": user_id}
                
                for key, value in update_dict.items():
                    set_clauses.append(f"{key} = :{key}")
                    params[key] = value
                
                if not set_clauses:
                    return existing_item
                
                query = f"""
                UPDATE wardrobe_items 
                SET {', '.join(set_clauses)}
                WHERE id = :item_id AND user_id = :user_id
                RETURNING *
                """
                
                result = await db.execute(query, params)
                updated_item = result.fetchone()
                
                if not updated_item:
                    return None
                
                # Limpiar caché
                await self._invalidate_user_wardrobe_cache(user_id)
                
                return WardrobeItemResponse(**dict(updated_item))
                
        except Exception as e:
            logger.error(f"Error updating wardrobe item: {str(e)}")
            raise Exception(f"Error al actualizar el item: {str(e)}")
    
    async def delete_wardrobe_item(self, user_id: str, item_id: str) -> bool:
        """Eliminar un item del armario"""
        
        try:
            async with get_database() as db:
                # Soft delete - marcar como inactivo
                query = """
                UPDATE wardrobe_items 
                SET is_active = false, updated_at = NOW()
                WHERE id = :item_id AND user_id = :user_id
                """
                
                result = await db.execute(query, {"item_id": item_id, "user_id": user_id})
                
                # Limpiar caché
                await self._invalidate_user_wardrobe_cache(user_id)
                
                return result.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error deleting wardrobe item: {str(e)}")
            return False
    
    async def update_item_wear_count(self, user_id: str, item_id: str) -> bool:
        """Actualizar contador de uso de un item"""
        
        try:
            async with get_database() as db:
                query = """
                UPDATE wardrobe_items 
                SET times_worn = times_worn + 1, 
                    last_worn = NOW(),
                    cost_per_wear = CASE 
                        WHEN purchase_price IS NOT NULL AND times_worn > 0 
                        THEN purchase_price / (times_worn + 1)
                        ELSE cost_per_wear
                    END,
                    updated_at = NOW()
                WHERE id = :item_id AND user_id = :user_id
                """
                
                result = await db.execute(query, {"item_id": item_id, "user_id": user_id})
                
                # Limpiar caché
                await self._invalidate_user_wardrobe_cache(user_id)
                
                return result.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error updating wear count: {str(e)}")
            return False
    
    # =============================================================================
    # GESTIÓN DE OUTFITS
    # =============================================================================
    
    async def generate_outfit_suggestions(
        self,
        user_id: str,
        request: OutfitGenerationRequest
    ) -> OutfitGenerationResponse:
        """Generar sugerencias de outfits para el usuario"""
        
        try:
            # Obtener items del armario del usuario
            wardrobe_items = await self.get_wardrobe_items(user_id, limit=1000)
            
            if not wardrobe_items:
                return OutfitGenerationResponse(
                    suggestions=[],
                    analysis={"message": "No hay suficientes items en el armario"},
                    alternatives=["Agrega más prendas a tu armario"],
                    gaps_identified=["Armario vacío"]
                )
            
            # Generar sugerencias con IA
            suggestions = await self.ai_service.generate_outfit_suggestions(
                wardrobe_items=wardrobe_items,
                occasion=request.occasion,
                season=request.season,
                weather=request.weather,
                temperature=request.temperature,
                preferred_styles=request.preferred_styles,
                color_preferences=request.color_preferences,
                must_include_items=request.must_include_items,
                exclude_items=request.exclude_items,
                max_suggestions=request.max_suggestions
            )
            
            # Analizar armario para identificar gaps
            wardrobe_analysis = await self.ai_service.analyze_wardrobe_gaps(wardrobe_items)
            
            # Generar alternativas
            alternatives = self._generate_alternatives(suggestions, request)
            
            response = OutfitGenerationResponse(
                suggestions=suggestions,
                analysis={
                    "total_items_analyzed": len(wardrobe_items),
                    "occasion": request.occasion.value,
                    "season": request.season.value if request.season else None,
                    "suggestions_generated": len(suggestions)
                },
                alternatives=alternatives,
                gaps_identified=wardrobe_analysis.get("missing_basics", [])
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating outfit suggestions: {str(e)}")
            return OutfitGenerationResponse(
                suggestions=[],
                analysis={"error": str(e)},
                alternatives=[],
                gaps_identified=[]
            )
    
    async def create_outfit(self, user_id: str, outfit_data: OutfitCreate) -> OutfitResponse:
        """Crear un nuevo outfit"""
        
        try:
            async with get_database() as db:
                # Verificar que todos los items pertenezcan al usuario
                valid_items = await self._verify_items_ownership(user_id, outfit_data.item_ids, db)
                
                if len(valid_items) != len(outfit_data.item_ids):
                    raise Exception("Algunos items no pertenecen al usuario")
                
                # Crear el outfit
                outfit_dict = outfit_data.dict(exclude={"item_ids"})
                outfit_dict.update({
                    "user_id": user_id,
                    "status": OutfitStatus.SAVED
                })
                
                # Preparar para base de datos
                outfit_dict = self._prepare_outfit_for_db(outfit_dict)
                
                # Insertar outfit
                outfit_query = """
                INSERT INTO outfits (
                    id, user_id, name, description, style, occasion, season, status,
                    tags, notes, created_at, updated_at
                ) VALUES (
                    gen_random_uuid(), :user_id, :name, :description, :style, :occasion, 
                    :season, :status, :tags, :notes, NOW(), NOW()
                ) RETURNING *
                """
                
                result = await db.execute(outfit_query, outfit_dict)
                new_outfit = result.fetchone()
                outfit_id = new_outfit.id
                
                # Insertar items del outfit
                for item_id in outfit_data.item_ids:
                    item_query = """
                    INSERT INTO outfit_items (id, outfit_id, item_id, created_at)
                    VALUES (gen_random_uuid(), :outfit_id, :item_id, NOW())
                    """
                    await db.execute(item_query, {"outfit_id": outfit_id, "item_id": item_id})
                
                # Obtener outfit completo con items
                complete_outfit = await self.get_outfit(user_id, outfit_id)
                
                logger.info(f"Created outfit {outfit_id} for user {user_id}")
                return complete_outfit
                
        except Exception as e:
            logger.error(f"Error creating outfit: {str(e)}")
            raise Exception(f"Error al crear el outfit: {str(e)}")
    
    async def get_outfits(
        self,
        user_id: str,
        occasion: Optional[Occasion] = None,
        season: Optional[Season] = None,
        status: Optional[OutfitStatus] = None,
        is_favorite: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[OutfitResponse]:
        """Obtener outfits del usuario con filtros"""
        
        try:
            async with get_database() as db:
                # Construir query con filtros
                query = "SELECT * FROM outfits WHERE user_id = :user_id AND is_active = true"
                params = {"user_id": user_id}
                
                if occasion:
                    query += " AND :occasion = ANY(occasion)"
                    params["occasion"] = occasion.value
                
                if season:
                    query += " AND season = :season"
                    params["season"] = season.value
                
                if status:
                    query += " AND status = :status"
                    params["status"] = status.value
                
                if is_favorite is not None:
                    query += " AND is_favorite = :is_favorite"
                    params["is_favorite"] = is_favorite
                
                query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
                params["limit"] = limit
                params["offset"] = offset
                
                result = await db.execute(query, params)
                outfits = result.fetchall()
                
                # Obtener items para cada outfit
                outfit_responses = []
                for outfit in outfits:
                    outfit_dict = dict(outfit)
                    
                    # Obtener items del outfit
                    items_query = """
                    SELECT wi.* FROM wardrobe_items wi
                    JOIN outfit_items oi ON wi.id = oi.item_id
                    WHERE oi.outfit_id = :outfit_id
                    """
                    
                    items_result = await db.execute(items_query, {"outfit_id": outfit.id})
                    items = [WardrobeItemResponse(**dict(item)) for item in items_result.fetchall()]
                    
                    outfit_dict["items"] = items
                    outfit_responses.append(OutfitResponse(**outfit_dict))
                
                return outfit_responses
                
        except Exception as e:
            logger.error(f"Error getting outfits: {str(e)}")
            return []
    
    async def get_outfit(self, user_id: str, outfit_id: str) -> Optional[OutfitResponse]:
        """Obtener un outfit específico"""
        
        try:
            async with get_database() as db:
                # Obtener outfit
                outfit_query = """
                SELECT * FROM outfits 
                WHERE id = :outfit_id AND user_id = :user_id AND is_active = true
                """
                
                result = await db.execute(outfit_query, {"outfit_id": outfit_id, "user_id": user_id})
                outfit = result.fetchone()
                
                if not outfit:
                    return None
                
                # Obtener items del outfit
                items_query = """
                SELECT wi.* FROM wardrobe_items wi
                JOIN outfit_items oi ON wi.id = oi.item_id
                WHERE oi.outfit_id = :outfit_id
                """
                
                items_result = await db.execute(items_query, {"outfit_id": outfit_id})
                items = [WardrobeItemResponse(**dict(item)) for item in items_result.fetchall()]
                
                outfit_dict = dict(outfit)
                outfit_dict["items"] = items
                
                return OutfitResponse(**outfit_dict)
                
        except Exception as e:
            logger.error(f"Error getting outfit: {str(e)}")
            return None
    
    # =============================================================================
    # ANÁLISIS Y ESTADÍSTICAS
    # =============================================================================
    
    async def analyze_wardrobe(self, user_id: str, analysis_type: WardrobeAnalysisType) -> WardrobeAnalysisResponse:
        """Realizar análisis del armario"""
        
        try:
            # Obtener items del armario
            wardrobe_items = await self.get_wardrobe_items(user_id, limit=1000)
            
            if analysis_type == WardrobeAnalysisType.GAPS_ANALYSIS:
                analysis_result = await self.ai_service.analyze_wardrobe_gaps(wardrobe_items)
            else:
                # Otros tipos de análisis
                analysis_result = await self._perform_specific_analysis(wardrobe_items, analysis_type)
            
            # Guardar análisis en la base de datos
            async with get_database() as db:
                analysis_dict = {
                    "user_id": user_id,
                    "analysis_type": analysis_type.value,
                    "results": analysis_result,
                    "score": analysis_result.get("wardrobe_score", 50),
                    "insights": analysis_result.get("insights", []),
                    "recommendations": [rec["description"] for rec in analysis_result.get("recommendations", [])],
                    "priorities": analysis_result.get("missing_basics", []),
                    "total_items": len(wardrobe_items),
                    "items_by_category": analysis_result.get("category_distribution", {}),
                    "items_by_color": analysis_result.get("color_distribution", {}),
                    "items_by_season": {},  # Calcular si es necesario
                    "missing_basics": analysis_result.get("missing_basics", []),
                    "color_gaps": analysis_result.get("color_gaps", []),
                    "occasion_gaps": analysis_result.get("occasion_gaps", [])
                }
                
                query = """
                INSERT INTO wardrobe_analyses (
                    id, user_id, analysis_type, results, score, insights, recommendations,
                    priorities, total_items, items_by_category, items_by_color, 
                    items_by_season, missing_basics, color_gaps, occasion_gaps, analysis_date
                ) VALUES (
                    gen_random_uuid(), :user_id, :analysis_type, :results, :score, :insights,
                    :recommendations, :priorities, :total_items, :items_by_category,
                    :items_by_color, :items_by_season, :missing_basics, :color_gaps,
                    :occasion_gaps, NOW()
                ) RETURNING *
                """
                
                result = await db.execute(query, analysis_dict)
                saved_analysis = result.fetchone()
                
                return WardrobeAnalysisResponse(**dict(saved_analysis))
                
        except Exception as e:
            logger.error(f"Error analyzing wardrobe: {str(e)}")
            raise Exception(f"Error al analizar el armario: {str(e)}")
    
    async def get_wardrobe_stats(self, user_id: str) -> WardrobeStats:
        """Obtener estadísticas del armario"""
        
        try:
            # Obtener todos los items
            all_items = await self.get_wardrobe_items(user_id, limit=1000)
            
            if not all_items:
                return WardrobeStats(
                    total_items=0,
                    items_by_category={},
                    items_by_color={},
                    items_by_season={},
                    items_by_style={},
                    total_value=None,
                    average_cost_per_wear=None,
                    most_worn_items=[],
                    least_worn_items=[],
                    favorite_items=[],
                    recent_additions=[]
                )
            
            # Calcular estadísticas
            stats = WardrobeStats(
                total_items=len(all_items),
                items_by_category=self._count_by_attribute(all_items, "category"),
                items_by_color=self._count_by_attribute(all_items, "color"),
                items_by_season=self._count_by_list_attribute(all_items, "season"),
                items_by_style=self._count_by_list_attribute(all_items, "style"),
                total_value=self._calculate_total_value(all_items),
                average_cost_per_wear=self._calculate_avg_cost_per_wear(all_items),
                most_worn_items=sorted(all_items, key=lambda x: x.times_worn, reverse=True)[:5],
                least_worn_items=sorted(all_items, key=lambda x: x.times_worn)[:5],
                favorite_items=[item for item in all_items if item.is_favorite],
                recent_additions=sorted(all_items, key=lambda x: x.created_at, reverse=True)[:10]
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting wardrobe stats: {str(e)}")
            raise Exception(f"Error al obtener estadísticas: {str(e)}")
    
    # =============================================================================
    # MÉTODOS AUXILIARES PRIVADOS
    # =============================================================================
    
    async def _check_wardrobe_limits(self, user_id: str, db: AsyncSession):
        """Verificar límites de armario según suscripción"""
        
        # Obtener usuario y su suscripción
        user_query = "SELECT subscription_tier FROM users WHERE id = :user_id"
        result = await db.execute(user_query, {"user_id": user_id})
        user = result.fetchone()
        
        if not user:
            raise Exception("Usuario no encontrado")
        
        # Contar items actuales
        count_query = "SELECT COUNT(*) FROM wardrobe_items WHERE user_id = :user_id AND is_active = true"
        count_result = await db.execute(count_query, {"user_id": user_id})
        current_count = count_result.scalar()
        
        # Verificar límites según suscripción
        limits = {
            "FREE": 50,
            "PREMIUM": 200,
            "PRO": 500,
            "ENTERPRISE": 1000
        }
        
        limit = limits.get(user.subscription_tier, 50)
        
        if current_count >= limit:
            raise Exception(f"Has alcanzado el límite de {limit} items para tu suscripción {user.subscription_tier}")
    
    async def _process_item_images(self, user_id: str, image_files: List[Any]) -> Dict[str, Any]:
        """Procesar y subir imágenes de items"""
        
        try:
            image_urls = []
            thumbnail_url = None
            
            for i, image_file in enumerate(image_files[:5]):  # Máximo 5 imágenes
                # Subir imagen original
                upload_result = await self.file_service.upload_file(
                    file=image_file,
                    folder=f"wardrobe/{user_id}",
                    filename_prefix=f"item_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}"
                )
                
                if upload_result.get("success"):
                    image_urls.append(upload_result["url"])
                    
                    # Crear thumbnail para la primera imagen
                    if i == 0:
                        thumbnail_result = await self.file_service.create_thumbnail(
                            image_url=upload_result["url"],
                            size=(300, 300)
                        )
                        if thumbnail_result.get("success"):
                            thumbnail_url = thumbnail_result["url"]
            
            return {
                "image_urls": image_urls,
                "thumbnail_url": thumbnail_url
            }
            
        except Exception as e:
            logger.error(f"Error processing item images: {str(e)}")
            return {"image_urls": [], "thumbnail_url": None}
    
    def _extract_ai_tags(self, ai_analysis: Dict[str, Any]) -> List[str]:
        """Extraer tags relevantes del análisis de IA"""
        
        if not ai_analysis:
            return []
        
        tags = []
        
        # Agregar categoría detectada
        if ai_analysis.get("category_detected"):
            tags.append(ai_analysis["category_detected"])
        
        # Agregar estilo detectado
        style_analysis = ai_analysis.get("style_analysis", {})
        if style_analysis.get("primary_style"):
            tags.append(style_analysis["primary_style"])
        
        # Agregar color principal
        color_analysis = ai_analysis.get("color_analysis", {})
        if color_analysis.get("primary_color"):
            tags.append(color_analysis["primary_color"])
        
        # Agregar material detectado
        if ai_analysis.get("material_detected"):
            tags.append(ai_analysis["material_detected"])
        
        return tags[:10]  # Máximo 10 tags
    
    def _prepare_item_for_db(self, item_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Preparar datos del item para inserción en la base de datos"""
        
        # Convertir enums a strings
        if "category" in item_dict and hasattr(item_dict["category"], "value"):
            item_dict["category"] = item_dict["category"].value
        
        if "subcategory" in item_dict and item_dict["subcategory"] and hasattr(item_dict["subcategory"], "value"):
            item_dict["subcategory"] = item_dict["subcategory"].value
        
        if "fit_type" in item_dict and item_dict["fit_type"] and hasattr(item_dict["fit_type"], "value"):
            item_dict["fit_type"] = item_dict["fit_type"].value
        
        # Convertir listas de enums
        for list_field in ["style", "season", "occasions"]:
            if list_field in item_dict and item_dict[list_field]:
                item_dict[list_field] = [
                    item.value if hasattr(item, "value") else item 
                    for item in item_dict[list_field]
                ]
        
        return item_dict
    
    def _prepare_outfit_for_db(self, outfit_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Preparar datos del outfit para inserción en la base de datos"""
        
        # Convertir enums a strings
        if "season" in outfit_dict and hasattr(outfit_dict["season"], "value"):
            outfit_dict["season"] = outfit_dict["season"].value
        
        if "status" in outfit_dict and hasattr(outfit_dict["status"], "value"):
            outfit_dict["status"] = outfit_dict["status"].value
        
        # Convertir listas de enums
        for list_field in ["style", "occasion"]:
            if list_field in outfit_dict and outfit_dict[list_field]:
                outfit_dict[list_field] = [
                    item.value if hasattr(item, "value") else item 
                    for item in outfit_dict[list_field]
                ]
        
        return outfit_dict
    
    async def _verify_items_ownership(self, user_id: str, item_ids: List[str], db: AsyncSession) -> List[str]:
        """Verificar que los items pertenezcan al usuario"""
        
        if not item_ids:
            return []
        
        placeholders = ','.join([f':item_{i}' for i in range(len(item_ids))])
        query = f"""
        SELECT id FROM wardrobe_items 
        WHERE user_id = :user_id AND id IN ({placeholders}) AND is_active = true
        """
        
        params = {"user_id": user_id}
        for i, item_id in enumerate(item_ids):
            params[f"item_{i}"] = item_id
        
        result = await db.execute(query, params)
        valid_ids = [row.id for row in result.fetchall()]
        
        return valid_ids
    
    async def _invalidate_user_wardrobe_cache(self, user_id: str):
        """Invalidar caché del armario del usuario"""
        
        try:
            # Invalidar patrones de caché relacionados
            patterns = [
                f"wardrobe_items:{user_id}:*",
                f"outfits:{user_id}:*",
                f"wardrobe_stats:{user_id}"
            ]
            
            for pattern in patterns:
                await self.cache_service.delete_pattern(pattern)
                
        except Exception as e:
            logger.warning(f"Error invalidating cache: {str(e)}")
    
    def _generate_alternatives(self, suggestions: List[OutfitSuggestion], request: OutfitGenerationRequest) -> List[str]:
        """Generar alternativas basadas en las sugerencias"""
        
        alternatives = []
        
        if len(suggestions) < request.max_suggestions:
            alternatives.append("Considera agregar más prendas a tu armario para más opciones")
        
        if request.occasion == Occasion.WORK:
            alternatives.append("Prueba con colores más neutros para looks profesionales")
        elif request.occasion == Occasion.PARTY:
            alternatives.append("Agrega un accesorio statement para destacar")
        
        if not request.preferred_styles:
            alternatives.append("Define tus estilos preferidos para sugerencias más personalizadas")
        
        return alternatives[:3]
    
    async def _perform_specific_analysis(self, items: List[WardrobeItemResponse], analysis_type: WardrobeAnalysisType) -> Dict[str, Any]:
        """Realizar análisis específico según el tipo"""
        
        if analysis_type == WardrobeAnalysisType.VERSATILITY:
            return self._analyze_versatility(items)
        elif analysis_type == WardrobeAnalysisType.COLOR_HARMONY:
            return self._analyze_color_harmony(items)
        elif analysis_type == WardrobeAnalysisType.COST_PER_WEAR:
            return self._analyze_cost_per_wear(items)
        else:
            return {"analysis_type": analysis_type.value, "items_analyzed": len(items)}
    
    def _analyze_versatility(self, items: List[WardrobeItemResponse]) -> Dict[str, Any]:
        """Analizar versatilidad del armario"""
        
        if not items:
            return {"average_versatility": 0, "most_versatile": [], "least_versatile": []}
        
        versatility_scores = [item.versatility_score or 50 for item in items]
        avg_versatility = sum(versatility_scores) / len(versatility_scores)
        
        sorted_by_versatility = sorted(items, key=lambda x: x.versatility_score or 50, reverse=True)
        
        return {
            "average_versatility": avg_versatility,
            "most_versatile": sorted_by_versatility[:5],
            "least_versatile": sorted_by_versatility[-5:],
            "versatility_distribution": {
                "high": len([s for s in versatility_scores if s > 70]),
                "medium": len([s for s in versatility_scores if 40 <= s <= 70]),
                "low": len([s for s in versatility_scores if s < 40])
            }
        }
    
    def _analyze_color_harmony(self, items: List[WardrobeItemResponse]) -> Dict[str, Any]:
        """Analizar armonía de colores del armario"""
        
        color_counts = {}
        for item in items:
            color = item.color.lower()
            color_counts[color] = color_counts.get(color, 0) + 1
            
            for secondary in item.secondary_colors:
                color = secondary.lower()
                color_counts[color] = color_counts.get(color, 0) + 0.5
        
        # Identificar colores dominantes
        sorted_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "color_distribution": dict(sorted_colors),
            "dominant_colors": [color for color, count in sorted_colors[:5]],
            "color_diversity": len(color_counts),
            "harmony_score": min(100, len(color_counts) * 10)  # Más colores = más diversidad
        }
    
    def _analyze_cost_per_wear(self, items: List[WardrobeItemResponse]) -> Dict[str, Any]:
        """Analizar costo por uso"""
        
        items_with_price = [item for item in items if item.purchase_price and item.times_worn > 0]
        
        if not items_with_price:
            return {"message": "No hay suficientes datos de precio y uso"}
        
        cost_per_wear_values = [float(item.cost_per_wear) for item in items_with_price if item.cost_per_wear]
        
        if not cost_per_wear_values:
            return {"message": "No se puede calcular costo por uso"}
        
        avg_cost_per_wear = sum(cost_per_wear_values) / len(cost_per_wear_values)
        
        sorted_by_cost = sorted(items_with_price, key=lambda x: float(x.cost_per_wear or 0))
        
        return {
            "average_cost_per_wear": avg_cost_per_wear,
            "best_value_items": sorted_by_cost[:5],
            "worst_value_items": sorted_by_cost[-5:],
            "total_value": sum(float(item.purchase_price) for item in items_with_price),
            "items_analyzed": len(items_with_price)
        }
    
    def _count_by_attribute(self, items: List[WardrobeItemResponse], attribute: str) -> Dict[str, int]:
        """Contar items por atributo"""
        
        counts = {}
        for item in items:
            value = getattr(item, attribute)
            if hasattr(value, "value"):
                value = value.value
            counts[str(value)] = counts.get(str(value), 0) + 1
        
        return counts
    
    def _count_by_list_attribute(self, items: List[WardrobeItemResponse], attribute: str) -> Dict[str, int]:
        """Contar items por atributo de lista"""
        
        counts = {}
        for item in items:
            values = getattr(item, attribute, [])
            for value in values:
                if hasattr(value, "value"):
                    value = value.value
                counts[str(value)] = counts.get(str(value), 0) + 1
        
        return counts
    
    def _calculate_total_value(self, items: List[WardrobeItemResponse]) -> Optional[Decimal]:
        """Calcular valor total del armario"""
        
        items_with_price = [item for item in items if item.purchase_price]
        
        if not items_with_price:
            return None
        
        return sum(item.purchase_price for item in items_with_price)
    
    def _calculate_avg_cost_per_wear(self, items: List[WardrobeItemResponse]) -> Optional[Decimal]:
        """Calcular costo promedio por uso"""
        
        items_with_cost = [item for item in items if item.cost_per_wear]
        
        if not items_with_cost:
            return None
        
        total_cost = sum(item.cost_per_wear for item in items_with_cost)
        return total_cost / len(items_with_cost)
