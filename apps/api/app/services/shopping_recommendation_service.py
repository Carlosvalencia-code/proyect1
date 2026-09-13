# =============================================================================
# SYNTHIA STYLE - SHOPPING RECOMMENDATION SERVICE
# =============================================================================
# Motor de recomendaciones inteligentes de compras con análisis de armario y IA

import asyncio
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Any, Tuple
from collections import defaultdict, Counter
import logging

from app.core.config import get_settings
from app.services.gemini_service import GeminiService
from app.services.cache_service import CacheService
from app.services.wardrobe_ai_service import WardrobeAIService
from app.schemas.shopping import (
    RecommendationType, 
    ShoppingRecommendationCreate,
    ProductSearchFilters,
    RecommendationRequest
)
from app.schemas.wardrobe import ClothingCategory, ClothingStyle, Season, Occasion

logger = logging.getLogger(__name__)
settings = get_settings()

class ShoppingRecommendationService:
    """
    Servicio principal para generar recomendaciones inteligentes de compras
    """
    
    def __init__(
        self,
        gemini_service: GeminiService,
        cache_service: CacheService,
        wardrobe_ai_service: WardrobeAIService
    ):
        self.gemini_service = gemini_service
        self.cache_service = cache_service
        self.wardrobe_ai_service = wardrobe_ai_service
        
        # Configuración de recomendaciones
        self.max_recommendations_per_type = 5
        self.min_confidence_score = 6.0
        self.cache_ttl = 3600  # 1 hora
        
    async def generate_personalized_recommendations(
        self,
        user_id: str,
        user_wardrobe: List[Dict[str, Any]],
        user_preferences: Dict[str, Any],
        facial_analysis: Optional[Dict[str, Any]] = None,
        chromatic_analysis: Optional[Dict[str, Any]] = None,
        request_params: Optional[RecommendationRequest] = None
    ) -> List[ShoppingRecommendationCreate]:
        """
        Genera recomendaciones personalizadas basadas en análisis completo del usuario
        """
        try:
            # Configuración por defecto
            if request_params is None:
                request_params = RecommendationRequest()
            
            logger.info(f"Generating recommendations for user {user_id}")
            
            # Cache key para recomendaciones
            cache_key = f"recommendations:{user_id}:{hash(str(request_params))}"
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                logger.info(f"Returning cached recommendations for user {user_id}")
                return [ShoppingRecommendationCreate(**rec) for rec in cached_result]
            
            # Análisis del armario actual
            wardrobe_analysis = await self._analyze_current_wardrobe(
                user_wardrobe, user_preferences
            )
            
            # Generar recomendaciones por tipo
            all_recommendations = []
            
            if not request_params.recommendation_types:
                # Tipos por defecto basados en análisis
                recommendation_types = await self._determine_recommendation_types(
                    wardrobe_analysis, user_preferences
                )
            else:
                recommendation_types = request_params.recommendation_types
            
            # Generar para cada tipo
            for rec_type in recommendation_types:
                recs = await self._generate_by_type(
                    rec_type,
                    user_id,
                    wardrobe_analysis,
                    user_preferences,
                    facial_analysis,
                    chromatic_analysis,
                    request_params
                )
                all_recommendations.extend(recs)
            
            # Filtrar y rankear recomendaciones
            filtered_recs = await self._filter_and_rank_recommendations(
                all_recommendations,
                wardrobe_analysis,
                user_preferences,
                request_params
            )
            
            # Aplicar límite final
            final_recs = filtered_recs[:request_params.max_recommendations]
            
            # Cache del resultado
            cache_data = [rec.dict() for rec in final_recs]
            await self.cache_service.set(cache_key, cache_data, ttl=self.cache_ttl)
            
            logger.info(f"Generated {len(final_recs)} recommendations for user {user_id}")
            return final_recs
            
        except Exception as e:
            logger.error(f"Error generating recommendations for user {user_id}: {e}")
            return []
    
    async def _analyze_current_wardrobe(
        self,
        wardrobe_items: List[Dict[str, Any]],
        user_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analiza el armario actual para identificar gaps y patrones
        """
        if not wardrobe_items:
            return {
                "total_items": 0,
                "categories": {},
                "colors": {},
                "styles": {},
                "occasions": {},
                "seasons": {},
                "gaps": {
                    "critical": ["TOPS", "BOTTOMS", "SHOES"],
                    "important": ["OUTERWEAR", "DRESSES"],
                    "nice_to_have": ["ACCESSORIES", "BAGS"]
                },
                "recommendations_priority": "basic_wardrobe"
            }
        
        # Análisis de distribución
        analysis = {
            "total_items": len(wardrobe_items),
            "categories": defaultdict(int),
            "colors": defaultdict(int),
            "styles": defaultdict(int),
            "occasions": defaultdict(int),
            "seasons": defaultdict(int),
            "usage_patterns": {},
            "value_metrics": {}
        }
        
        total_uses = 0
        total_value = Decimal(0)
        underutilized_items = 0
        
        for item in wardrobe_items:
            # Categorías
            analysis["categories"][item.get("category", "OTHER")] += 1
            
            # Colores
            color = item.get("color", "unknown").lower()
            analysis["colors"][color] += 1
            
            # Estilos
            styles = item.get("style", [])
            if isinstance(styles, list):
                for style in styles:
                    analysis["styles"][style] += 1
            
            # Ocasiones
            occasions = item.get("occasions", [])
            if isinstance(occasions, list):
                for occasion in occasions:
                    analysis["occasions"][occasion] += 1
            
            # Temporadas
            seasons = item.get("season", [])
            if isinstance(seasons, list):
                for season in seasons:
                    analysis["seasons"][season] += 1
            
            # Métricas de uso
            uses = item.get("times_worn", 0)
            total_uses += uses
            if uses < 2:  # Items poco utilizados
                underutilized_items += 1
            
            # Valor
            price = item.get("purchase_price")
            if price:
                total_value += Decimal(str(price))
        
        # Calcular gaps críticos
        gaps = await self._identify_wardrobe_gaps(analysis, user_preferences)
        analysis["gaps"] = gaps
        
        # Métricas de valor
        analysis["value_metrics"] = {
            "total_value": float(total_value),
            "average_value": float(total_value / len(wardrobe_items)) if wardrobe_items else 0,
            "underutilized_percentage": (underutilized_items / len(wardrobe_items)) * 100 if wardrobe_items else 0,
            "average_uses": total_uses / len(wardrobe_items) if wardrobe_items else 0
        }
        
        # Prioridad de recomendaciones
        if len(wardrobe_items) < 10:
            analysis["recommendations_priority"] = "basic_wardrobe"
        elif gaps["critical"]:
            analysis["recommendations_priority"] = "gap_filling"
        elif analysis["value_metrics"]["underutilized_percentage"] > 50:
            analysis["recommendations_priority"] = "versatility_improvement"
        else:
            analysis["recommendations_priority"] = "style_enhancement"
        
        return dict(analysis)
    
    async def _identify_wardrobe_gaps(
        self,
        wardrobe_analysis: Dict[str, Any],
        user_preferences: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        Identifica gaps críticos en el armario
        """
        essential_categories = {
            ClothingCategory.TOPS: 5,      # Mínimo 5 tops
            ClothingCategory.BOTTOMS: 3,   # Mínimo 3 bottoms
            ClothingCategory.SHOES: 3,     # Mínimo 3 pares
            ClothingCategory.OUTERWEAR: 2, # Mínimo 2 abrigos
            ClothingCategory.DRESSES: 1,   # Mínimo 1 vestido (si usa)
        }
        
        # Colores esenciales basados en análisis cromático
        essential_colors = ["negro", "blanco", "azul marino", "gris"]
        
        # Estilos básicos
        essential_styles = [ClothingStyle.CASUAL, ClothingStyle.FORMAL]
        
        gaps = {
            "critical": [],
            "important": [],
            "nice_to_have": []
        }
        
        categories = wardrobe_analysis.get("categories", {})
        colors = wardrobe_analysis.get("colors", {})
        styles = wardrobe_analysis.get("styles", {})
        occasions = wardrobe_analysis.get("occasions", {})
        
        # Gaps por categoría
        for category, min_count in essential_categories.items():
            current_count = categories.get(category.value, 0)
            if current_count < min_count:
                if current_count == 0:
                    gaps["critical"].append(category.value)
                elif current_count < min_count // 2:
                    gaps["important"].append(category.value)
                else:
                    gaps["nice_to_have"].append(category.value)
        
        # Gaps por color (si falta más del 75% de colores esenciales)
        missing_colors = [color for color in essential_colors if color not in colors]
        if len(missing_colors) > len(essential_colors) * 0.75:
            gaps["important"].extend([f"COLOR_{color.upper()}" for color in missing_colors[:2]])
        
        # Gaps por estilo
        missing_styles = [style for style in essential_styles if style.value not in styles]
        if missing_styles:
            gaps["important"].extend([f"STYLE_{style.value}" for style in missing_styles])
        
        # Gaps por ocasión
        work_items = occasions.get(Occasion.WORK.value, 0)
        formal_items = occasions.get(Occasion.FORMAL.value, 0)
        
        if work_items == 0:
            gaps["important"].append("OCCASION_WORK")
        if formal_items == 0:
            gaps["nice_to_have"].append("OCCASION_FORMAL")
        
        return gaps
    
    async def _determine_recommendation_types(
        self,
        wardrobe_analysis: Dict[str, Any],
        user_preferences: Dict[str, Any]
    ) -> List[RecommendationType]:
        """
        Determina qué tipos de recomendaciones generar basado en el análisis
        """
        recommendation_types = []
        
        priority = wardrobe_analysis.get("recommendations_priority", "basic_wardrobe")
        gaps = wardrobe_analysis.get("gaps", {})
        
        if priority == "basic_wardrobe":
            recommendation_types.extend([
                RecommendationType.BASIC_ITEM,
                RecommendationType.OUTFIT_COMPLETION
            ])
        
        if gaps.get("critical") or gaps.get("important"):
            recommendation_types.append(RecommendationType.BASIC_ITEM)
        
        # Siempre incluir recomendaciones estacionales
        current_season = self._get_current_season()
        recommendation_types.append(RecommendationType.SEASONAL_REFRESH)
        
        # Incluir presupuesto consciente si aplica
        budget_range = user_preferences.get("budget_range", {})
        if budget_range and budget_range.get("max", 1000) < 100:
            recommendation_types.append(RecommendationType.BUDGET_CONSCIOUS)
        
        # Limitar a 3 tipos principales para no sobrecargar
        return recommendation_types[:3]
    
    async def _generate_by_type(
        self,
        recommendation_type: RecommendationType,
        user_id: str,
        wardrobe_analysis: Dict[str, Any],
        user_preferences: Dict[str, Any],
        facial_analysis: Optional[Dict[str, Any]],
        chromatic_analysis: Optional[Dict[str, Any]],
        request_params: RecommendationRequest
    ) -> List[ShoppingRecommendationCreate]:
        """
        Genera recomendaciones específicas por tipo
        """
        try:
            if recommendation_type == RecommendationType.BASIC_ITEM:
                return await self._generate_basic_item_recommendations(
                    wardrobe_analysis, user_preferences, chromatic_analysis
                )
            
            elif recommendation_type == RecommendationType.OUTFIT_COMPLETION:
                return await self._generate_outfit_completion_recommendations(
                    wardrobe_analysis, user_preferences
                )
            
            elif recommendation_type == RecommendationType.SEASONAL_REFRESH:
                return await self._generate_seasonal_recommendations(
                    wardrobe_analysis, user_preferences, request_params
                )
            
            elif recommendation_type == RecommendationType.BUDGET_CONSCIOUS:
                return await self._generate_budget_recommendations(
                    wardrobe_analysis, user_preferences, request_params
                )
            
            elif recommendation_type == RecommendationType.SPECIAL_OCCASION:
                return await self._generate_special_occasion_recommendations(
                    wardrobe_analysis, user_preferences, request_params
                )
            
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error generating {recommendation_type} recommendations: {e}")
            return []
    
    async def _generate_basic_item_recommendations(
        self,
        wardrobe_analysis: Dict[str, Any],
        user_preferences: Dict[str, Any],
        chromatic_analysis: Optional[Dict[str, Any]]
    ) -> List[ShoppingRecommendationCreate]:
        """
        Genera recomendaciones de items básicos faltantes
        """
        recommendations = []
        gaps = wardrobe_analysis.get("gaps", {})
        
        # Mapeo de gaps a recomendaciones específicas
        gap_to_recommendations = {
            "TOPS": {
                "item_type": ClothingCategory.TOPS,
                "recommended_name": "Camiseta básica",
                "description": "Camiseta versátil para uso diario y combinaciones",
                "priority": 9.0,
                "estimated_uses": 50
            },
            "BOTTOMS": {
                "item_type": ClothingCategory.BOTTOMS,
                "recommended_name": "Jeans clásicos",
                "description": "Jeans de corte clásico que combina con todo",
                "priority": 9.0,
                "estimated_uses": 40
            },
            "SHOES": {
                "item_type": ClothingCategory.SHOES,
                "recommended_name": "Zapatillas básicas",
                "description": "Zapatillas versátiles para uso diario",
                "priority": 8.5,
                "estimated_uses": 100
            },
            "OUTERWEAR": {
                "item_type": ClothingCategory.OUTERWEAR,
                "recommended_name": "Chaqueta básica",
                "description": "Chaqueta ligera para cambios de temperatura",
                "priority": 7.5,
                "estimated_uses": 30
            }
        }
        
        # Generar para gaps críticos e importantes
        for gap_list in [gaps.get("critical", []), gaps.get("important", [])]:
            for gap in gap_list:
                if gap in gap_to_recommendations:
                    rec_data = gap_to_recommendations[gap]
                    
                    # Personalizar con análisis cromático
                    color_suggestion = "negro"  # Default
                    if chromatic_analysis:
                        palette = chromatic_analysis.get("paleta_primaria", [])
                        if palette:
                            color_suggestion = palette[0].get("color", "negro")
                    
                    # Crear recomendación
                    recommendation = ShoppingRecommendationCreate(
                        item_type=rec_data["item_type"],
                        recommended_name=rec_data["recommended_name"],
                        description=rec_data["description"],
                        recommendation_type=RecommendationType.BASIC_ITEM,
                        reason=f"Tu armario necesita más {gap.lower()}. Este item básico completará tu colección y te dará más opciones de combinación.",
                        priority=rec_data["priority"],
                        confidence=8.5,
                        estimated_uses=rec_data["estimated_uses"],
                        wardrobe_gap=f"Falta de {gap.lower()} básicos",
                        stylist_notes=f"Color recomendado: {color_suggestion} por su versatilidad",
                        color=color_suggestion
                    )
                    
                    recommendations.append(recommendation)
        
        return recommendations[:self.max_recommendations_per_type]
    
    async def _generate_outfit_completion_recommendations(
        self,
        wardrobe_analysis: Dict[str, Any],
        user_preferences: Dict[str, Any]
    ) -> List[ShoppingRecommendationCreate]:
        """
        Genera recomendaciones para completar outfits existentes
        """
        recommendations = []
        
        # Analizar combinaciones faltantes
        categories = wardrobe_analysis.get("categories", {})
        
        # Si tiene muchos tops pero pocos bottoms
        tops_count = categories.get(ClothingCategory.TOPS.value, 0)
        bottoms_count = categories.get(ClothingCategory.BOTTOMS.value, 0)
        
        if tops_count > bottoms_count * 2:
            recommendation = ShoppingRecommendationCreate(
                item_type=ClothingCategory.BOTTOMS,
                recommended_name="Pantalón versátil",
                description="Pantalón que combina con múltiples tops de tu armario",
                recommendation_type=RecommendationType.OUTFIT_COMPLETION,
                reason=f"Tienes {tops_count} tops pero solo {bottoms_count} bottoms. Un pantalón adicional te dará {tops_count} nuevas combinaciones.",
                priority=8.0,
                confidence=8.0,
                estimated_uses=tops_count,
                wardrobe_gap="Desequilibrio tops/bottoms",
                stylist_notes="Busca un color neutro que combine con la mayoría de tus tops"
            )
            recommendations.append(recommendation)
        
        # Lógica similar para otras combinaciones
        return recommendations[:self.max_recommendations_per_type]
    
    async def _generate_seasonal_recommendations(
        self,
        wardrobe_analysis: Dict[str, Any],
        user_preferences: Dict[str, Any],
        request_params: RecommendationRequest
    ) -> List[ShoppingRecommendationCreate]:
        """
        Genera recomendaciones estacionales
        """
        recommendations = []
        current_season = request_params.season_context or self._get_current_season()
        
        seasonal_needs = {
            Season.SPRING: {
                "categories": [ClothingCategory.TOPS, ClothingCategory.OUTERWEAR],
                "colors": ["verde", "rosa", "azul claro"],
                "description": "Ropa ligera y fresca para la primavera"
            },
            Season.SUMMER: {
                "categories": [ClothingCategory.TOPS, ClothingCategory.DRESSES, ClothingCategory.SHOES],
                "colors": ["blanco", "amarillo", "coral"],
                "description": "Prendas ligeras y transpirables para el verano"
            },
            Season.FALL: {
                "categories": [ClothingCategory.OUTERWEAR, ClothingCategory.BOTTOMS],
                "colors": ["marrón", "naranja", "verde oliva"],
                "description": "Capas y tonos otoñales"
            },
            Season.WINTER: {
                "categories": [ClothingCategory.OUTERWEAR, ClothingCategory.ACCESSORIES],
                "colors": ["negro", "gris", "azul marino"],
                "description": "Prendas abrigadas para el invierno"
            }
        }
        
        if current_season in seasonal_needs:
            season_data = seasonal_needs[current_season]
            seasons_items = wardrobe_analysis.get("seasons", {})
            current_season_count = seasons_items.get(current_season.value, 0)
            
            if current_season_count < 3:  # Necesita más ropa estacional
                for category in season_data["categories"][:2]:  # Máximo 2 categorías
                    recommendation = ShoppingRecommendationCreate(
                        item_type=category,
                        recommended_name=f"{category.value.title()} de {current_season.value}",
                        description=f"{season_data['description']} - {category.value.lower()}",
                        recommendation_type=RecommendationType.SEASONAL_REFRESH,
                        reason=f"Se acerca {current_season.value} y tu armario tiene pocas opciones para esta temporada.",
                        priority=7.0,
                        confidence=7.5,
                        estimated_uses=20,
                        wardrobe_gap=f"Falta ropa de {current_season.value}",
                        stylist_notes=f"Colores recomendados para {current_season.value}: {', '.join(season_data['colors'])}",
                        color=season_data["colors"][0]
                    )
                    recommendations.append(recommendation)
        
        return recommendations[:self.max_recommendations_per_type]
    
    async def _generate_budget_recommendations(
        self,
        wardrobe_analysis: Dict[str, Any],
        user_preferences: Dict[str, Any],
        request_params: RecommendationRequest
    ) -> List[ShoppingRecommendationCreate]:
        """
        Genera recomendaciones conscientes del presupuesto
        """
        recommendations = []
        budget_range = request_params.budget_range or user_preferences.get("budget_range", {})
        max_budget = budget_range.get("max", 50)  # Presupuesto bajo por defecto
        
        # Ítems de alto impacto con bajo costo
        budget_items = [
            {
                "item_type": ClothingCategory.ACCESSORIES,
                "name": "Bufanda versátil",
                "description": "Accesorio que transforma cualquier outfit básico",
                "estimated_price": 15,
                "impact_score": 8.0
            },
            {
                "item_type": ClothingCategory.TOPS,
                "name": "Camiseta básica de calidad",
                "description": "Camiseta que se puede usar en múltiples ocasiones",
                "estimated_price": 25,
                "impact_score": 9.0
            },
            {
                "item_type": ClothingCategory.ACCESSORIES,
                "name": "Cinturón clásico",
                "description": "Define la silueta y añade estilo a cualquier outfit",
                "estimated_price": 20,
                "impact_score": 7.5
            }
        ]
        
        for item in budget_items:
            if item["estimated_price"] <= max_budget:
                recommendation = ShoppingRecommendationCreate(
                    item_type=item["item_type"],
                    recommended_name=item["name"],
                    description=item["description"],
                    recommendation_type=RecommendationType.BUDGET_CONSCIOUS,
                    reason=f"Máximo impacto por tu presupuesto de ${max_budget}. Este item te dará múltiples looks nuevos.",
                    priority=item["impact_score"],
                    confidence=8.0,
                    estimated_uses=30,
                    price=Decimal(str(item["estimated_price"])),
                    roi_score=85.0,
                    wardrobe_gap="Optimización presupuesto/impacto",
                    stylist_notes=f"Excelente relación calidad-precio por ${item['estimated_price']}"
                )
                recommendations.append(recommendation)
        
        return recommendations[:self.max_recommendations_per_type]
    
    async def _generate_special_occasion_recommendations(
        self,
        wardrobe_analysis: Dict[str, Any],
        user_preferences: Dict[str, Any],
        request_params: RecommendationRequest
    ) -> List[ShoppingRecommendationCreate]:
        """
        Genera recomendaciones para ocasiones especiales
        """
        recommendations = []
        occasions = wardrobe_analysis.get("occasions", {})
        
        # Verificar si faltan opciones para ocasiones importantes
        special_occasions = {
            Occasion.FORMAL: {
                "name": "Vestido formal",
                "description": "Vestido elegante para eventos especiales",
                "category": ClothingCategory.DRESSES
            },
            Occasion.WORK: {
                "name": "Blazer profesional",
                "description": "Blazer versátil para el ambiente laboral",
                "category": ClothingCategory.OUTERWEAR
            },
            Occasion.PARTY: {
                "name": "Top de fiesta",
                "description": "Top llamativo para fiestas y celebraciones",
                "category": ClothingCategory.TOPS
            }
        }
        
        for occasion, data in special_occasions.items():
            if occasions.get(occasion.value, 0) == 0:  # No tiene nada para esa ocasión
                recommendation = ShoppingRecommendationCreate(
                    item_type=data["category"],
                    recommended_name=data["name"],
                    description=data["description"],
                    recommendation_type=RecommendationType.SPECIAL_OCCASION,
                    reason=f"No tienes opciones para {occasion.value.lower()}. Esta prenda te preparará para esas ocasiones especiales.",
                    priority=6.5,
                    confidence=7.0,
                    estimated_uses=8,
                    wardrobe_gap=f"Falta ropa para {occasion.value}",
                    stylist_notes=f"Busca un diseño atemporal que puedas usar en múltiples {occasion.value.lower()}s"
                )
                recommendations.append(recommendation)
        
        return recommendations[:self.max_recommendations_per_type]
    
    async def _filter_and_rank_recommendations(
        self,
        recommendations: List[ShoppingRecommendationCreate],
        wardrobe_analysis: Dict[str, Any],
        user_preferences: Dict[str, Any],
        request_params: RecommendationRequest
    ) -> List[ShoppingRecommendationCreate]:
        """
        Filtra y rankea las recomendaciones por relevancia y calidad
        """
        if not recommendations:
            return []
        
        # Aplicar filtros de presupuesto
        if request_params.budget_range:
            max_budget = request_params.budget_range.get("max")
            if max_budget:
                recommendations = [
                    rec for rec in recommendations
                    if not rec.price or rec.price <= max_budget
                ]
        
        # Filtrar por categorías específicas si se solicitan
        if request_params.specific_categories:
            recommendations = [
                rec for rec in recommendations
                if rec.item_type in request_params.specific_categories
            ]
        
        # Filtrar por confianza mínima
        recommendations = [
            rec for rec in recommendations
            if rec.confidence >= self.min_confidence_score
        ]
        
        # Rankear por puntuación combinada
        def calculate_score(rec: ShoppingRecommendationCreate) -> float:
            score = 0.0
            
            # Peso por prioridad (40%)
            score += (rec.priority / 10.0) * 0.4
            
            # Peso por confianza (30%)
            score += (rec.confidence / 10.0) * 0.3
            
            # Peso por ROI si existe (20%)
            if rec.roi_score:
                score += (rec.roi_score / 100.0) * 0.2
            
            # Peso por usos estimados (10%)
            if rec.estimated_uses:
                # Normalizar usos estimados (máximo 100 usos = score 1.0)
                uses_score = min(rec.estimated_uses / 100.0, 1.0)
                score += uses_score * 0.1
            
            return score
        
        # Ordenar por score descendente
        recommendations.sort(key=calculate_score, reverse=True)
        
        # Diversificar por tipo y categoría
        final_recommendations = self._diversify_recommendations(recommendations)
        
        return final_recommendations
    
    def _diversify_recommendations(
        self,
        recommendations: List[ShoppingRecommendationCreate]
    ) -> List[ShoppingRecommendationCreate]:
        """
        Diversifica las recomendaciones para evitar repetición de tipos/categorías
        """
        seen_types = set()
        seen_categories = set()
        diversified = []
        
        for rec in recommendations:
            # Clave única por tipo y categoría
            type_key = rec.recommendation_type
            category_key = rec.item_type
            
            # Permitir máximo 2 del mismo tipo
            type_count = sum(1 for r in diversified if r.recommendation_type == type_key)
            # Permitir máximo 2 de la misma categoría
            category_count = sum(1 for r in diversified if r.item_type == category_key)
            
            if type_count < 2 and category_count < 2:
                diversified.append(rec)
                seen_types.add(type_key)
                seen_categories.add(category_key)
        
        return diversified
    
    def _get_current_season(self) -> Season:
        """
        Determina la temporada actual basada en la fecha
        """
        month = datetime.now().month
        
        if month in [12, 1, 2]:
            return Season.WINTER
        elif month in [3, 4, 5]:
            return Season.SPRING
        elif month in [6, 7, 8]:
            return Season.SUMMER
        else:  # 9, 10, 11
            return Season.FALL
    
    async def analyze_recommendation_performance(
        self,
        user_id: str,
        timeframe_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analiza el rendimiento de las recomendaciones pasadas
        """
        try:
            # Este método se implementaría con acceso a la base de datos
            # para analizar clicks, conversiones, etc.
            
            # Placeholder para métricas básicas
            return {
                "total_recommendations": 0,
                "click_through_rate": 0.0,
                "conversion_rate": 0.0,
                "top_performing_types": [],
                "user_satisfaction_score": 0.0,
                "timeframe_days": timeframe_days
            }
            
        except Exception as e:
            logger.error(f"Error analyzing recommendation performance: {e}")
            return {}
