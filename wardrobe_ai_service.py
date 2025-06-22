"""
Servicio de IA para análisis de prendas y generación de outfits en Synthia Style
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
import colorsys
import re
from datetime import datetime

from app.services.gemini_service import GeminiService
from app.schemas.wardrobe import (
    ClothingCategory, ClothingSubcategory, ClothingStyle, Season, Occasion,
    FitType, WardrobeItemResponse, OutfitSuggestion
)

logger = logging.getLogger(__name__)

class WardrobeAIService:
    """Servicio de IA para análisis de armario virtual"""
    
    def __init__(self):
        self.gemini_service = GeminiService()
        
        # Definir reglas de armonía de colores
        self.color_harmony_rules = {
            "complementary": ["opposite"],
            "analogous": ["adjacent"],
            "triadic": ["triangle"],
            "split_complementary": ["split"],
            "monochromatic": ["same_hue"]
        }
        
        # Mapeo de estilos compatibles
        self.compatible_styles = {
            ClothingStyle.FORMAL: [ClothingStyle.BUSINESS, ClothingStyle.ELEGANT, ClothingStyle.CLASSIC],
            ClothingStyle.CASUAL: [ClothingStyle.SPORTY, ClothingStyle.MINIMALIST, ClothingStyle.TRENDY],
            ClothingStyle.BUSINESS: [ClothingStyle.FORMAL, ClothingStyle.CLASSIC, ClothingStyle.MINIMALIST],
            ClothingStyle.ELEGANT: [ClothingStyle.FORMAL, ClothingStyle.ROMANTIC, ClothingStyle.CLASSIC],
            ClothingStyle.SPORTY: [ClothingStyle.CASUAL, ClothingStyle.TRENDY],
            ClothingStyle.BOHEMIAN: [ClothingStyle.ROMANTIC, ClothingStyle.VINTAGE],
            ClothingStyle.MINIMALIST: [ClothingStyle.CASUAL, ClothingStyle.BUSINESS, ClothingStyle.CLASSIC],
            ClothingStyle.VINTAGE: [ClothingStyle.ROMANTIC, ClothingStyle.BOHEMIAN, ClothingStyle.CLASSIC],
            ClothingStyle.TRENDY: [ClothingStyle.CASUAL, ClothingStyle.EDGY, ClothingStyle.SPORTY],
            ClothingStyle.CLASSIC: [ClothingStyle.FORMAL, ClothingStyle.BUSINESS, ClothingStyle.ELEGANT],
            ClothingStyle.EDGY: [ClothingStyle.TRENDY, ClothingStyle.VINTAGE],
            ClothingStyle.ROMANTIC: [ClothingStyle.ELEGANT, ClothingStyle.BOHEMIAN, ClothingStyle.VINTAGE]
        }
        
        # Reglas de ocasión y estilo
        self.occasion_style_mapping = {
            Occasion.WORK: [ClothingStyle.BUSINESS, ClothingStyle.FORMAL, ClothingStyle.CLASSIC],
            Occasion.CASUAL: [ClothingStyle.CASUAL, ClothingStyle.MINIMALIST, ClothingStyle.TRENDY],
            Occasion.FORMAL: [ClothingStyle.FORMAL, ClothingStyle.ELEGANT, ClothingStyle.CLASSIC],
            Occasion.PARTY: [ClothingStyle.ELEGANT, ClothingStyle.TRENDY, ClothingStyle.EDGY],
            Occasion.DATE: [ClothingStyle.ROMANTIC, ClothingStyle.ELEGANT, ClothingStyle.TRENDY],
            Occasion.VACATION: [ClothingStyle.CASUAL, ClothingStyle.BOHEMIAN, ClothingStyle.SPORTY],
            Occasion.EXERCISE: [ClothingStyle.SPORTY],
            Occasion.HOME: [ClothingStyle.CASUAL, ClothingStyle.MINIMALIST],
            Occasion.SPECIAL_EVENT: [ClothingStyle.FORMAL, ClothingStyle.ELEGANT],
            Occasion.TRAVEL: [ClothingStyle.CASUAL, ClothingStyle.MINIMALIST, ClothingStyle.SPORTY]
        }

    async def analyze_garment_from_image(self, image_url: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analizar una prenda desde una imagen usando Gemini Vision"""
        try:
            # Prompt especializado para análisis de prendas
            analysis_prompt = """
            Analiza esta prenda de vestir en detalle. Proporciona información sobre:

            1. CATEGORÍA Y TIPO:
            - Categoría principal (tops, bottoms, dresses, outerwear, shoes, accessories, etc.)
            - Subcategoría específica (t-shirt, jeans, blazer, etc.)
            - Tipo de prenda exacto

            2. CARACTERÍSTICAS VISUALES:
            - Color principal y colores secundarios
            - Patrón o estampado (sólido, rayas, puntos, floral, etc.)
            - Textura aparente (algodón, denim, seda, etc.)
            - Fit aparente (ajustado, regular, holgado, oversized)

            3. ESTILO Y OCASIÓN:
            - Estilo principal (casual, formal, business, sporty, etc.)
            - Ocasiones apropiadas
            - Temporadas recomendadas

            4. CARACTERÍSTICAS TÉCNICAS:
            - Material estimado
            - Cuidado probable requerido
            - Calidad aparente (básica, media, premium)

            5. VERSATILIDAD:
            - Puntuación de versatilidad (0-100)
            - Con qué otras prendas combinaría bien
            - Ocasiones múltiples de uso

            6. ANÁLISIS DE COLORES:
            - Temperatura del color (cálido/frío)
            - Intensidad (pastel, vibrante, neutro)
            - Compatibilidad con otros colores

            Responde en formato JSON estructurado.
            """

            # Hacer el análisis con Gemini
            result = await self.gemini_service.analyze_image_with_prompt(
                image_url=image_url,
                prompt=analysis_prompt
            )

            # Procesar y estructurar la respuesta
            analysis = self._process_garment_analysis(result, user_context)
            
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing garment: {str(e)}")
            return self._get_default_analysis()

    def _process_garment_analysis(self, ai_result: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Procesar el resultado del análisis de IA"""
        try:
            # Intentar parsear JSON desde la respuesta
            analysis_data = self._extract_json_from_text(ai_result)
            
            if not analysis_data:
                # Si no hay JSON válido, extraer información con regex
                analysis_data = self._extract_info_with_regex(ai_result)

            # Enriquecer con análisis adicional
            analysis = {
                "category_detected": analysis_data.get("category", "unknown"),
                "subcategory_detected": analysis_data.get("subcategory", "unknown"),
                "color_analysis": self._analyze_colors(analysis_data.get("colors", [])),
                "style_analysis": self._analyze_style(analysis_data.get("style", [])),
                "versatility_score": analysis_data.get("versatility_score", 50),
                "style_score": analysis_data.get("style_score", 50),
                "occasion_recommendations": analysis_data.get("occasions", []),
                "season_recommendations": analysis_data.get("seasons", []),
                "material_detected": analysis_data.get("material", "unknown"),
                "fit_detected": analysis_data.get("fit", "regular"),
                "care_instructions": analysis_data.get("care", []),
                "styling_tips": analysis_data.get("styling_tips", []),
                "color_harmony": self._calculate_color_harmony(analysis_data.get("colors", [])),
                "confidence_score": analysis_data.get("confidence", 75),
                "analysis_timestamp": datetime.now().isoformat()
            }

            return analysis

        except Exception as e:
            logger.error(f"Error processing garment analysis: {str(e)}")
            return self._get_default_analysis()

    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """Extraer JSON válido del texto de respuesta"""
        try:
            # Buscar JSON en el texto
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        return {}

    def _extract_info_with_regex(self, text: str) -> Dict[str, Any]:
        """Extraer información usando regex cuando no hay JSON válido"""
        extracted = {}
        
        # Patrones para extraer información
        patterns = {
            "category": r"categoría[:\s]+([^\n]+)",
            "color": r"color[:\s]+([^\n]+)",
            "style": r"estilo[:\s]+([^\n]+)",
            "material": r"material[:\s]+([^\n]+)",
            "occasions": r"ocasion[es]*[:\s]+([^\n]+)"
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted[key] = match.group(1).strip()
        
        return extracted

    def _analyze_colors(self, colors: List[str]) -> Dict[str, Any]:
        """Analizar los colores de una prenda"""
        color_analysis = {
            "primary_color": colors[0] if colors else "unknown",
            "secondary_colors": colors[1:] if len(colors) > 1 else [],
            "color_temperature": "neutral",
            "color_intensity": "medium",
            "neutral_rating": 0,
            "versatility": 50
        }
        
        if colors:
            # Determinar temperatura de color
            warm_colors = ["red", "orange", "yellow", "pink", "brown"]
            cool_colors = ["blue", "green", "purple", "gray", "black"]
            
            primary = colors[0].lower()
            if any(warm in primary for warm in warm_colors):
                color_analysis["color_temperature"] = "warm"
            elif any(cool in primary for cool in cool_colors):
                color_analysis["color_temperature"] = "cool"
            
            # Calcular rating de neutralidad
            neutral_colors = ["black", "white", "gray", "beige", "navy", "brown"]
            neutral_score = sum(1 for color in colors if any(neutral in color.lower() for neutral in neutral_colors))
            color_analysis["neutral_rating"] = (neutral_score / len(colors)) * 100
            
            # Versatilidad basada en neutralidad
            color_analysis["versatility"] = min(100, color_analysis["neutral_rating"] + 30)
        
        return color_analysis

    def _analyze_style(self, styles: List[str]) -> Dict[str, Any]:
        """Analizar el estilo de una prenda"""
        return {
            "primary_style": styles[0] if styles else "casual",
            "secondary_styles": styles[1:] if len(styles) > 1 else [],
            "formality_level": self._calculate_formality(styles),
            "trend_factor": self._calculate_trend_factor(styles),
            "classic_score": self._calculate_classic_score(styles)
        }

    def _calculate_formality(self, styles: List[str]) -> int:
        """Calcular nivel de formalidad (0-100)"""
        formal_styles = ["formal", "business", "elegant", "classic"]
        casual_styles = ["casual", "sporty", "bohemian"]
        
        formal_score = sum(1 for style in styles if style.lower() in formal_styles)
        casual_score = sum(1 for style in styles if style.lower() in casual_styles)
        
        if formal_score > casual_score:
            return min(100, 60 + (formal_score * 15))
        elif casual_score > formal_score:
            return max(0, 40 - (casual_score * 15))
        else:
            return 50

    def _calculate_trend_factor(self, styles: List[str]) -> int:
        """Calcular factor de tendencia (0-100)"""
        trendy_styles = ["trendy", "edgy", "contemporary"]
        classic_styles = ["classic", "vintage", "traditional"]
        
        trendy_score = sum(1 for style in styles if style.lower() in trendy_styles)
        classic_score = sum(1 for style in styles if style.lower() in classic_styles)
        
        return min(100, (trendy_score * 30) + 20)

    def _calculate_classic_score(self, styles: List[str]) -> int:
        """Calcular puntuación clásica (0-100)"""
        classic_indicators = ["classic", "timeless", "traditional", "elegant"]
        return min(100, sum(20 for style in styles if any(indicator in style.lower() for indicator in classic_indicators)))

    def _calculate_color_harmony(self, colors: List[str]) -> Dict[str, Any]:
        """Calcular armonía de colores"""
        if not colors:
            return {"harmony_score": 0, "harmony_type": "none"}
        
        # Análisis simplificado de armonía
        harmony_score = 70  # Score base
        harmony_type = "complementary"
        
        if len(colors) == 1:
            harmony_score = 100
            harmony_type = "monochromatic"
        elif len(colors) == 2:
            # Analizar si son complementarios
            harmony_score = 85
            harmony_type = "complementary"
        else:
            # Múltiples colores - verificar si son análogos
            harmony_score = 60
            harmony_type = "analogous"
        
        return {
            "harmony_score": harmony_score,
            "harmony_type": harmony_type,
            "color_distribution": len(colors),
            "dominant_color": colors[0] if colors else None
        }

    def _get_default_analysis(self) -> Dict[str, Any]:
        """Obtener análisis por defecto en caso de error"""
        return {
            "category_detected": "unknown",
            "subcategory_detected": "unknown",
            "color_analysis": {
                "primary_color": "unknown",
                "secondary_colors": [],
                "color_temperature": "neutral",
                "versatility": 50
            },
            "style_analysis": {
                "primary_style": "casual",
                "formality_level": 50
            },
            "versatility_score": 50,
            "style_score": 50,
            "confidence_score": 25,
            "analysis_timestamp": datetime.now().isoformat()
        }

    async def generate_outfit_suggestions(
        self,
        wardrobe_items: List[WardrobeItemResponse],
        occasion: Occasion,
        season: Season = None,
        weather: str = None,
        temperature: float = None,
        preferred_styles: List[ClothingStyle] = None,
        color_preferences: List[str] = None,
        must_include_items: List[str] = None,
        exclude_items: List[str] = None,
        max_suggestions: int = 5
    ) -> List[OutfitSuggestion]:
        """Generar sugerencias de outfits basadas en el armario del usuario"""
        
        try:
            logger.info(f"Generating outfit suggestions for occasion: {occasion}")
            
            # Filtrar items disponibles
            available_items = self._filter_available_items(
                wardrobe_items, season, weather, exclude_items
            )
            
            # Obtener estilos apropiados para la ocasión
            appropriate_styles = self.occasion_style_mapping.get(occasion, [ClothingStyle.CASUAL])
            if preferred_styles:
                appropriate_styles = list(set(appropriate_styles) & set(preferred_styles))
            
            # Generar combinaciones
            outfit_combinations = self._generate_outfit_combinations(
                available_items, must_include_items, appropriate_styles, max_suggestions * 2
            )
            
            # Evaluar y rankear combinaciones
            evaluated_outfits = []
            for combination in outfit_combinations:
                evaluation = await self._evaluate_outfit_combination(
                    combination, occasion, season, weather, temperature, color_preferences
                )
                if evaluation["confidence"] > 50:  # Filtrar combinaciones de baja calidad
                    evaluated_outfits.append(evaluation)
            
            # Ordenar por puntuación y tomar las mejores
            evaluated_outfits.sort(key=lambda x: x["total_score"], reverse=True)
            top_outfits = evaluated_outfits[:max_suggestions]
            
            # Convertir a OutfitSuggestion
            suggestions = []
            for outfit_eval in top_outfits:
                suggestion = OutfitSuggestion(
                    items=outfit_eval["items"],
                    confidence=outfit_eval["confidence"],
                    style_coherence=outfit_eval["style_coherence"],
                    color_harmony=outfit_eval["color_harmony"],
                    appropriateness=outfit_eval["appropriateness"],
                    reasoning=outfit_eval["reasoning"],
                    tips=outfit_eval["tips"]
                )
                suggestions.append(suggestion)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating outfit suggestions: {str(e)}")
            return []

    def _filter_available_items(
        self,
        items: List[WardrobeItemResponse],
        season: Season = None,
        weather: str = None,
        exclude_items: List[str] = None
    ) -> List[WardrobeItemResponse]:
        """Filtrar items disponibles según criterios"""
        
        filtered_items = []
        exclude_set = set(exclude_items or [])
        
        for item in items:
            # Excluir items específicos
            if item.id in exclude_set:
                continue
            
            # Filtrar por temporada
            if season and season not in item.season and Season.ALL_SEASON not in item.season:
                continue
            
            # Filtrar por item activo
            if not item.is_active:
                continue
            
            filtered_items.append(item)
        
        return filtered_items

    def _generate_outfit_combinations(
        self,
        items: List[WardrobeItemResponse],
        must_include: List[str] = None,
        appropriate_styles: List[ClothingStyle] = None,
        max_combinations: int = 10
    ) -> List[List[WardrobeItemResponse]]:
        """Generar combinaciones válidas de outfits"""
        
        # Agrupar items por categoría
        items_by_category = {}
        for item in items:
            category = item.category
            if category not in items_by_category:
                items_by_category[category] = []
            items_by_category[category].append(item)
        
        # Items obligatorios
        must_include_items = []
        if must_include:
            must_include_set = set(must_include)
            must_include_items = [item for item in items if item.id in must_include_set]
        
        combinations = []
        
        # Generar combinaciones básicas (top + bottom)
        tops = items_by_category.get(ClothingCategory.TOPS, [])
        bottoms = items_by_category.get(ClothingCategory.BOTTOMS, [])
        dresses = items_by_category.get(ClothingCategory.DRESSES, [])
        shoes = items_by_category.get(ClothingCategory.SHOES, [])
        outerwear = items_by_category.get(ClothingCategory.OUTERWEAR, [])
        accessories = items_by_category.get(ClothingCategory.ACCESSORIES, [])
        
        # Combinaciones con vestidos
        for dress in dresses[:5]:  # Limitar para performance
            combination = [dress]
            
            # Agregar zapatos si hay
            if shoes:
                combination.append(shoes[0])  # Tomar primer zapato compatible
            
            # Agregar accesorios si hay
            if accessories:
                combination.append(accessories[0])
            
            # Agregar items obligatorios
            for must_item in must_include_items:
                if must_item not in combination:
                    combination.append(must_item)
            
            if self._is_valid_combination(combination):
                combinations.append(combination)
        
        # Combinaciones top + bottom
        for top in tops[:5]:
            for bottom in bottoms[:5]:
                combination = [top, bottom]
                
                # Agregar zapatos compatibles
                compatible_shoes = self._find_compatible_shoes(shoes, top, bottom)
                if compatible_shoes:
                    combination.append(compatible_shoes[0])
                
                # Agregar outerwear si es apropiado
                if outerwear and self._needs_outerwear(top, bottom):
                    compatible_outer = self._find_compatible_outerwear(outerwear, top, bottom)
                    if compatible_outer:
                        combination.append(compatible_outer[0])
                
                # Agregar items obligatorios
                for must_item in must_include_items:
                    if must_item not in combination:
                        combination.append(must_item)
                
                if self._is_valid_combination(combination):
                    combinations.append(combination)
                
                if len(combinations) >= max_combinations:
                    break
            
            if len(combinations) >= max_combinations:
                break
        
        return combinations[:max_combinations]

    def _is_valid_combination(self, items: List[WardrobeItemResponse]) -> bool:
        """Verificar si una combinación de items es válida"""
        
        # Verificar que no haya conflictos de categoría
        categories = [item.category for item in items]
        
        # No puede haber vestido con top o bottom
        if ClothingCategory.DRESSES in categories:
            if ClothingCategory.TOPS in categories or ClothingCategory.BOTTOMS in categories:
                return False
        
        # Debe tener al menos una pieza principal
        main_categories = [ClothingCategory.TOPS, ClothingCategory.BOTTOMS, ClothingCategory.DRESSES]
        if not any(cat in categories for cat in main_categories):
            return False
        
        return True

    def _find_compatible_shoes(
        self,
        shoes: List[WardrobeItemResponse],
        top: WardrobeItemResponse,
        bottom: WardrobeItemResponse
    ) -> List[WardrobeItemResponse]:
        """Encontrar zapatos compatibles con un outfit"""
        
        compatible = []
        outfit_formality = self._calculate_outfit_formality([top, bottom])
        
        for shoe in shoes:
            shoe_formality = self._get_item_formality(shoe)
            
            # Los zapatos deben estar en un rango similar de formalidad
            if abs(outfit_formality - shoe_formality) <= 30:
                compatible.append(shoe)
        
        return sorted(compatible, key=lambda x: self._calculate_style_compatibility([top, bottom], x))

    def _find_compatible_outerwear(
        self,
        outerwear: List[WardrobeItemResponse],
        top: WardrobeItemResponse,
        bottom: WardrobeItemResponse
    ) -> List[WardrobeItemResponse]:
        """Encontrar outerwear compatible"""
        
        compatible = []
        base_styles = set(top.style + bottom.style)
        
        for outer in outerwear:
            outer_styles = set(outer.style)
            
            # Verificar compatibilidad de estilos
            if outer_styles & base_styles or self._are_styles_compatible(base_styles, outer_styles):
                compatible.append(outer)
        
        return compatible

    def _needs_outerwear(self, top: WardrobeItemResponse, bottom: WardrobeItemResponse) -> bool:
        """Determinar si se necesita outerwear basado en el outfit"""
        
        # Lógica simplificada - en un sistema real consideraría el clima
        top_categories = [ClothingSubcategory.T_SHIRT, ClothingSubcategory.TANK_TOP, ClothingSubcategory.BLOUSE]
        
        return any(subcat in [top.subcategory] for subcat in top_categories)

    def _calculate_outfit_formality(self, items: List[WardrobeItemResponse]) -> int:
        """Calcular el nivel de formalidad de un outfit"""
        
        total_formality = 0
        for item in items:
            total_formality += self._get_item_formality(item)
        
        return total_formality // len(items) if items else 50

    def _get_item_formality(self, item: WardrobeItemResponse) -> int:
        """Obtener nivel de formalidad de un item individual"""
        
        formal_styles = [ClothingStyle.FORMAL, ClothingStyle.BUSINESS, ClothingStyle.ELEGANT]
        casual_styles = [ClothingStyle.CASUAL, ClothingStyle.SPORTY]
        
        if any(style in item.style for style in formal_styles):
            return 80
        elif any(style in item.style for style in casual_styles):
            return 30
        else:
            return 50

    def _calculate_style_compatibility(self, base_items: List[WardrobeItemResponse], new_item: WardrobeItemResponse) -> float:
        """Calcular compatibilidad de estilo entre items"""
        
        base_styles = set()
        for item in base_items:
            base_styles.update(item.style)
        
        new_styles = set(new_item.style)
        
        # Verificar intersección directa
        direct_match = len(base_styles & new_styles)
        if direct_match > 0:
            return 100
        
        # Verificar compatibilidad usando reglas
        compatibility_score = 0
        for base_style in base_styles:
            compatible_styles = self.compatible_styles.get(base_style, [])
            if any(style in new_styles for style in compatible_styles):
                compatibility_score += 50
        
        return min(100, compatibility_score)

    def _are_styles_compatible(self, styles1: set, styles2: set) -> bool:
        """Verificar si dos conjuntos de estilos son compatibles"""
        
        # Intersección directa
        if styles1 & styles2:
            return True
        
        # Verificar usando reglas de compatibilidad
        for style1 in styles1:
            compatible = self.compatible_styles.get(style1, [])
            if any(style2 in compatible for style2 in styles2):
                return True
        
        return False

    async def _evaluate_outfit_combination(
        self,
        items: List[WardrobeItemResponse],
        occasion: Occasion,
        season: Season = None,
        weather: str = None,
        temperature: float = None,
        color_preferences: List[str] = None
    ) -> Dict[str, Any]:
        """Evaluar una combinación de outfit y generar puntuación"""
        
        # Calcular métricas de evaluación
        style_coherence = self._calculate_style_coherence(items)
        color_harmony = self._calculate_outfit_color_harmony(items)
        appropriateness = self._calculate_occasion_appropriateness(items, occasion)
        seasonal_appropriateness = self._calculate_seasonal_appropriateness(items, season)
        
        # Puntuación total ponderada
        total_score = (
            style_coherence * 0.3 +
            color_harmony["harmony_score"] * 0.25 +
            appropriateness * 0.25 +
            seasonal_appropriateness * 0.2
        )
        
        # Confianza basada en la puntuación total
        confidence = min(100, total_score + 10)
        
        # Generar reasoning y tips
        reasoning = self._generate_outfit_reasoning(items, occasion, total_score)
        tips = self._generate_styling_tips(items, occasion, color_harmony)
        
        return {
            "items": items,
            "style_coherence": style_coherence,
            "color_harmony": color_harmony,
            "appropriateness": appropriateness,
            "seasonal_appropriateness": seasonal_appropriateness,
            "total_score": total_score,
            "confidence": confidence,
            "reasoning": reasoning,
            "tips": tips
        }

    def _calculate_style_coherence(self, items: List[WardrobeItemResponse]) -> float:
        """Calcular coherencia de estilo en un outfit"""
        
        if not items:
            return 0
        
        all_styles = []
        for item in items:
            all_styles.extend(item.style)
        
        if not all_styles:
            return 50  # Score neutral si no hay estilos definidos
        
        # Contar frecuencia de estilos
        style_counts = {}
        for style in all_styles:
            style_counts[style] = style_counts.get(style, 0) + 1
        
        # Calcular coherencia basada en estilos dominantes
        total_style_instances = len(all_styles)
        dominant_style_count = max(style_counts.values())
        
        coherence = (dominant_style_count / total_style_instances) * 100
        
        # Bonus por compatibilidad de estilos
        compatibility_bonus = 0
        unique_styles = set(all_styles)
        for style in unique_styles:
            compatible_styles = self.compatible_styles.get(style, [])
            compatible_in_outfit = len(unique_styles & set(compatible_styles))
            compatibility_bonus += compatible_in_outfit * 10
        
        return min(100, coherence + compatibility_bonus)

    def _calculate_outfit_color_harmony(self, items: List[WardrobeItemResponse]) -> Dict[str, Any]:
        """Calcular armonía de colores del outfit completo"""
        
        all_colors = []
        for item in items:
            all_colors.append(item.color)
            all_colors.extend(item.secondary_colors)
        
        # Remover duplicados manteniendo orden
        unique_colors = list(dict.fromkeys(all_colors))
        
        return self._calculate_color_harmony(unique_colors)

    def _calculate_occasion_appropriateness(self, items: List[WardrobeItemResponse], occasion: Occasion) -> float:
        """Calcular qué tan apropiado es el outfit para la ocasión"""
        
        appropriate_styles = self.occasion_style_mapping.get(occasion, [])
        
        total_appropriateness = 0
        total_items = len(items)
        
        for item in items:
            item_appropriateness = 0
            
            # Verificar si el item tiene estilos apropiados
            for style in item.style:
                if style in appropriate_styles:
                    item_appropriateness += 30
            
            # Verificar si la ocasión está en las ocasiones del item
            if occasion in item.occasions:
                item_appropriateness += 40
            
            # Bonus por versatilidad
            if len(item.occasions) > 3:
                item_appropriateness += 10
            
            total_appropriateness += min(100, item_appropriateness)
        
        return total_appropriateness / total_items if total_items > 0 else 0

    def _calculate_seasonal_appropriateness(self, items: List[WardrobeItemResponse], season: Season) -> float:
        """Calcular apropiedad estacional del outfit"""
        
        if not season:
            return 100  # Si no se especifica temporada, siempre es apropiado
        
        total_appropriateness = 0
        total_items = len(items)
        
        for item in items:
            if season in item.season or Season.ALL_SEASON in item.season:
                total_appropriateness += 100
            else:
                # Penalty por temporada inapropiada
                total_appropriateness += 20
        
        return total_appropriateness / total_items if total_items > 0 else 0

    def _generate_outfit_reasoning(self, items: List[WardrobeItemResponse], occasion: Occasion, score: float) -> str:
        """Generar explicación del outfit"""
        
        item_names = [item.name for item in items]
        outfit_description = ", ".join(item_names)
        
        if score >= 80:
            quality = "excelente"
        elif score >= 60:
            quality = "buena"
        else:
            quality = "aceptable"
        
        reasoning = f"Esta combinación de {outfit_description} es una {quality} opción para {occasion.value.lower()}. "
        
        # Agregar detalles específicos
        colors = [item.color for item in items]
        if len(set(colors)) <= 2:
            reasoning += "Los colores armonizan bien juntos. "
        
        styles = []
        for item in items:
            styles.extend(item.style)
        
        if styles:
            dominant_style = max(set(styles), key=styles.count)
            reasoning += f"El estilo {dominant_style.value.lower()} predomina en el outfit."
        
        return reasoning

    def _generate_styling_tips(
        self,
        items: List[WardrobeItemResponse],
        occasion: Occasion,
        color_harmony: Dict[str, Any]
    ) -> List[str]:
        """Generar tips de styling para el outfit"""
        
        tips = []
        
        # Tips de color
        if color_harmony["harmony_score"] < 70:
            tips.append("Considera agregar un accesorio que unifique los colores del outfit")
        
        # Tips por ocasión
        if occasion == Occasion.WORK:
            tips.append("Mantén los accesorios simples y profesionales")
        elif occasion == Occasion.DATE:
            tips.append("Un toque de color o accesorio especial puede elevar el look")
        elif occasion == Occasion.CASUAL:
            tips.append("Juega con texturas y capas para añadir interés visual")
        
        # Tips generales
        has_statement_piece = any(item.is_favorite for item in items)
        if not has_statement_piece:
            tips.append("Considera añadir una pieza statement para destacar")
        
        # Tips de versatilidad
        if len(items) == 2:  # Outfit básico
            tips.append("Puedes añadir una chaqueta o accesorio para más versatilidad")
        
        return tips[:3]  # Limitar a 3 tips principales

    async def analyze_wardrobe_gaps(
        self,
        wardrobe_items: List[WardrobeItemResponse],
        user_occasions: List[Occasion] = None,
        user_styles: List[ClothingStyle] = None,
        budget_range: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """Analizar gaps en el armario y generar recomendaciones"""
        
        # Analizar distribución actual
        category_distribution = self._analyze_category_distribution(wardrobe_items)
        color_distribution = self._analyze_color_distribution(wardrobe_items)
        occasion_coverage = self._analyze_occasion_coverage(wardrobe_items, user_occasions)
        style_coverage = self._analyze_style_coverage(wardrobe_items, user_styles)
        
        # Identificar gaps
        missing_basics = self._identify_missing_basics(category_distribution)
        color_gaps = self._identify_color_gaps(color_distribution)
        occasion_gaps = self._identify_occasion_gaps(occasion_coverage, user_occasions)
        style_gaps = self._identify_style_gaps(style_coverage, user_styles)
        
        # Calcular puntuaciones
        versatility_scores = [item.versatility_score or 50 for item in wardrobe_items]
        avg_versatility = sum(versatility_scores) / len(versatility_scores) if versatility_scores else 50
        
        # Generar insights
        insights = self._generate_wardrobe_insights(
            category_distribution, color_distribution, avg_versatility, len(wardrobe_items)
        )
        
        # Priorizar recomendaciones
        recommendations = self._prioritize_recommendations(
            missing_basics, color_gaps, occasion_gaps, style_gaps, budget_range
        )
        
        return {
            "total_items": len(wardrobe_items),
            "category_distribution": category_distribution,
            "color_distribution": color_distribution,
            "occasion_coverage": occasion_coverage,
            "style_coverage": style_coverage,
            "missing_basics": missing_basics,
            "color_gaps": color_gaps,
            "occasion_gaps": occasion_gaps,
            "style_gaps": style_gaps,
            "average_versatility": avg_versatility,
            "wardrobe_score": self._calculate_wardrobe_score(
                len(wardrobe_items), len(missing_basics), avg_versatility
            ),
            "insights": insights,
            "recommendations": recommendations,
            "analysis_date": datetime.now().isoformat()
        }

    def _analyze_category_distribution(self, items: List[WardrobeItemResponse]) -> Dict[str, int]:
        """Analizar distribución por categorías"""
        distribution = {}
        for item in items:
            category = item.category.value
            distribution[category] = distribution.get(category, 0) + 1
        return distribution

    def _analyze_color_distribution(self, items: List[WardrobeItemResponse]) -> Dict[str, int]:
        """Analizar distribución de colores"""
        distribution = {}
        for item in items:
            color = item.color.lower()
            distribution[color] = distribution.get(color, 0) + 1
            
            # Agregar colores secundarios
            for secondary_color in item.secondary_colors:
                color = secondary_color.lower()
                distribution[color] = distribution.get(color, 0) + 0.5
        
        # Convertir a enteros
        return {k: int(v) for k, v in distribution.items()}

    def _analyze_occasion_coverage(self, items: List[WardrobeItemResponse], user_occasions: List[Occasion] = None) -> Dict[str, int]:
        """Analizar cobertura de ocasiones"""
        coverage = {}
        
        target_occasions = user_occasions or list(Occasion)
        
        for occasion in target_occasions:
            count = sum(1 for item in items if occasion in item.occasions)
            coverage[occasion.value] = count
        
        return coverage

    def _analyze_style_coverage(self, items: List[WardrobeItemResponse], user_styles: List[ClothingStyle] = None) -> Dict[str, int]:
        """Analizar cobertura de estilos"""
        coverage = {}
        
        target_styles = user_styles or list(ClothingStyle)
        
        for style in target_styles:
            count = sum(1 for item in items if style in item.style)
            coverage[style.value] = count
        
        return coverage

    def _identify_missing_basics(self, category_distribution: Dict[str, int]) -> List[str]:
        """Identificar básicos faltantes"""
        
        essential_basics = {
            "TOPS": 5,      # Al menos 5 tops
            "BOTTOMS": 3,   # Al menos 3 bottoms
            "SHOES": 3,     # Al menos 3 pares de zapatos
            "OUTERWEAR": 2  # Al menos 2 piezas de outerwear
        }
        
        missing = []
        for category, min_count in essential_basics.items():
            current_count = category_distribution.get(category, 0)
            if current_count < min_count:
                needed = min_count - current_count
                missing.append(f"{needed} más {category.lower()}")
        
        return missing

    def _identify_color_gaps(self, color_distribution: Dict[str, int]) -> List[str]:
        """Identificar gaps de colores"""
        
        essential_colors = ["black", "white", "navy", "gray", "beige"]
        missing_colors = []
        
        for color in essential_colors:
            if color not in color_distribution or color_distribution[color] == 0:
                missing_colors.append(color)
        
        return missing_colors

    def _identify_occasion_gaps(self, occasion_coverage: Dict[str, int], user_occasions: List[Occasion] = None) -> List[str]:
        """Identificar gaps de ocasiones"""
        
        important_occasions = [Occasion.WORK, Occasion.CASUAL, Occasion.FORMAL]
        if user_occasions:
            important_occasions.extend(user_occasions)
        
        gaps = []
        for occasion in important_occasions:
            if occasion_coverage.get(occasion.value, 0) < 2:  # Al menos 2 opciones por ocasión
                gaps.append(occasion.value)
        
        return list(set(gaps))

    def _identify_style_gaps(self, style_coverage: Dict[str, int], user_styles: List[ClothingStyle] = None) -> List[str]:
        """Identificar gaps de estilos"""
        
        if not user_styles:
            return []
        
        gaps = []
        for style in user_styles:
            if style_coverage.get(style.value, 0) < 2:  # Al menos 2 piezas por estilo preferido
                gaps.append(style.value)
        
        return gaps

    def _generate_wardrobe_insights(
        self,
        category_dist: Dict[str, int],
        color_dist: Dict[str, int],
        avg_versatility: float,
        total_items: int
    ) -> List[str]:
        """Generar insights del armario"""
        
        insights = []
        
        # Insight sobre tamaño del armario
        if total_items < 20:
            insights.append("Tu armario es compacto. Considera invertir en piezas versátiles de calidad.")
        elif total_items > 100:
            insights.append("Tienes un armario extenso. Podrías beneficiarte de una curación para mantener solo lo que realmente usas.")
        
        # Insight sobre versatilidad
        if avg_versatility > 70:
            insights.append("Tu armario tiene piezas muy versátiles que funcionan para múltiples ocasiones.")
        elif avg_versatility < 50:
            insights.append("Considera agregar piezas más versátiles que puedas usar en diferentes contextos.")
        
        # Insight sobre colores
        neutral_colors = ["black", "white", "gray", "navy", "beige"]
        neutral_count = sum(color_dist.get(color, 0) for color in neutral_colors)
        total_color_instances = sum(color_dist.values())
        
        if total_color_instances > 0:
            neutral_ratio = neutral_count / total_color_instances
            if neutral_ratio > 0.7:
                insights.append("Tu armario es muy neutro. Un toque de color podría añadir personalidad.")
            elif neutral_ratio < 0.3:
                insights.append("Tienes muchos colores. Más neutros podrían mejorar la versatilidad.")
        
        # Insight sobre distribución de categorías
        if category_dist.get("TOPS", 0) > category_dist.get("BOTTOMS", 0) * 2:
            insights.append("Tienes muchos tops en relación a bottoms. Balancear podría crear más outfits.")
        
        return insights

    def _prioritize_recommendations(
        self,
        missing_basics: List[str],
        color_gaps: List[str],
        occasion_gaps: List[str],
        style_gaps: List[str],
        budget_range: Dict[str, float] = None
    ) -> List[Dict[str, Any]]:
        """Priorizar recomendaciones de compras"""
        
        recommendations = []
        
        # Prioridad alta: básicos faltantes
        for basic in missing_basics:
            recommendations.append({
                "type": "missing_basic",
                "description": f"Agregar {basic}",
                "priority": 9,
                "estimated_cost": budget_range.get("basic", 50) if budget_range else 50,
                "reasoning": "Pieza básica esencial para un armario funcional"
            })
        
        # Prioridad media: colores faltantes
        for color in color_gaps:
            recommendations.append({
                "type": "color_gap",
                "description": f"Agregar pieza en {color}",
                "priority": 7,
                "estimated_cost": budget_range.get("basic", 40) if budget_range else 40,
                "reasoning": f"El {color} es un color versátil que combina con muchas piezas"
            })
        
        # Prioridad media: ocasiones faltantes
        for occasion in occasion_gaps:
            recommendations.append({
                "type": "occasion_gap",
                "description": f"Agregar opciones para {occasion}",
                "priority": 6,
                "estimated_cost": budget_range.get("occasion", 60) if budget_range else 60,
                "reasoning": f"Necesitas más opciones para ocasiones {occasion}"
            })
        
        # Ordenar por prioridad
        recommendations.sort(key=lambda x: x["priority"], reverse=True)
        
        return recommendations[:10]  # Top 10 recomendaciones

    def _calculate_wardrobe_score(self, total_items: int, missing_basics_count: int, avg_versatility: float) -> float:
        """Calcular puntuación general del armario"""
        
        # Score base por cantidad de items
        if total_items >= 30:
            quantity_score = 100
        elif total_items >= 20:
            quantity_score = 80
        elif total_items >= 10:
            quantity_score = 60
        else:
            quantity_score = 40
        
        # Penalty por básicos faltantes
        basics_penalty = missing_basics_count * 10
        
        # Score de versatilidad
        versatility_score = avg_versatility
        
        # Score final ponderado
        final_score = (
            quantity_score * 0.3 +
            max(0, 100 - basics_penalty) * 0.4 +
            versatility_score * 0.3
        )
        
        return min(100, max(0, final_score))
