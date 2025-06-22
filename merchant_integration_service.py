# =============================================================================
# SYNTHIA STYLE - MERCHANT INTEGRATION SERVICE
# =============================================================================
# Servicio para integración con merchants y gestión de afiliados

import asyncio
import aiohttp
import json
import hashlib
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Any, Tuple
from urllib.parse import urlencode, urlparse, parse_qs
import logging
import re

from app.core.config import get_settings
from app.services.cache_service import CacheService
from app.schemas.shopping import (
    ProductCreate, 
    ProductUpdate, 
    ProductResponse,
    ProductSearchFilters,
    ProductSearchResponse,
    Merchant,
    AffiliateEarningCreate
)

logger = logging.getLogger(__name__)
settings = get_settings()

class MerchantIntegrationService:
    """
    Servicio para integración con merchants y manejo de productos externos
    """
    
    def __init__(self, cache_service: CacheService):
        self.cache_service = cache_service
        
        # Configuración de merchants
        self.merchant_configs = {
            Merchant.AMAZON: {
                "base_url": "https://paapi-v5.amazon.com",
                "search_endpoint": "/paapi5/searchitems",
                "affiliate_tag": settings.AMAZON_AFFILIATE_TAG,
                "access_key": settings.AMAZON_ACCESS_KEY,
                "secret_key": settings.AMAZON_SECRET_KEY,
                "commission_rate": 0.04,  # 4%
                "currency": "USD",
                "enabled": bool(settings.AMAZON_AFFILIATE_TAG)
            },
            Merchant.ASOS: {
                "base_url": "https://api.asos.com",
                "search_endpoint": "/v4/search/products",
                "affiliate_tag": settings.ASOS_AFFILIATE_TAG,
                "api_key": settings.ASOS_API_KEY,
                "commission_rate": 0.06,  # 6%
                "currency": "USD",
                "enabled": bool(settings.ASOS_API_KEY)
            },
            Merchant.ZARA: {
                "base_url": "https://www.zara.com",
                "search_endpoint": "/api/catalog/search",
                "affiliate_tag": settings.ZARA_AFFILIATE_TAG,
                "commission_rate": 0.03,  # 3%
                "currency": "USD",
                "enabled": False,  # Requiere web scraping
                "scraping_enabled": True
            },
            Merchant.HM: {
                "base_url": "https://www2.hm.com",
                "search_endpoint": "/en_us/api/search",
                "affiliate_tag": settings.HM_AFFILIATE_TAG,
                "commission_rate": 0.05,  # 5%
                "currency": "USD",
                "enabled": False,  # Requiere web scraping
                "scraping_enabled": True
            }
        }
        
        # Cache TTL
        self.search_cache_ttl = 3600  # 1 hora
        self.product_cache_ttl = 7200  # 2 horas
        
        # Rate limiting
        self.rate_limits = {
            Merchant.AMAZON: {"requests_per_minute": 10, "requests_per_day": 8640},
            Merchant.ASOS: {"requests_per_minute": 30, "requests_per_day": 5000},
            Merchant.ZARA: {"requests_per_minute": 5, "requests_per_day": 1000},
            Merchant.HM: {"requests_per_minute": 5, "requests_per_day": 1000}
        }
    
    async def search_products(
        self,
        filters: ProductSearchFilters,
        preferred_merchants: Optional[List[str]] = None
    ) -> ProductSearchResponse:
        """
        Busca productos en múltiples merchants de forma concurrente
        """
        try:
            logger.info(f"Searching products with query: {filters.query}")
            
            # Cache key para la búsqueda
            cache_key = f"product_search:{hashlib.md5(str(filters.dict()).encode()).hexdigest()}"
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                logger.info("Returning cached search results")
                return ProductSearchResponse(**cached_result)
            
            # Determinar merchants a usar
            merchants_to_search = self._get_active_merchants(preferred_merchants)
            
            # Buscar en paralelo
            search_tasks = []
            for merchant in merchants_to_search:
                if await self._check_rate_limit(merchant):
                    task = self._search_in_merchant(merchant, filters)
                    search_tasks.append(task)
            
            if not search_tasks:
                logger.warning("No merchants available for search")
                return ProductSearchResponse(
                    products=[],
                    total_count=0,
                    filters_applied=filters,
                    search_time=0.0
                )
            
            # Ejecutar búsquedas concurrentes
            start_time = asyncio.get_event_loop().time()
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            search_time = asyncio.get_event_loop().time() - start_time
            
            # Procesar resultados
            all_products = []
            for result in search_results:
                if isinstance(result, list):
                    all_products.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"Search error: {result}")
            
            # Filtrar y rankear productos
            filtered_products = self._filter_and_rank_products(all_products, filters)
            
            # Aplicar límites de paginación
            start_idx = filters.offset
            end_idx = start_idx + filters.limit
            paginated_products = filtered_products[start_idx:end_idx]
            
            # Generar sugerencias de búsqueda si hay pocos resultados
            suggestions = []
            if len(filtered_products) < 5 and filters.query:
                suggestions = await self._generate_search_suggestions(filters.query)
            
            result = ProductSearchResponse(
                products=paginated_products,
                total_count=len(filtered_products),
                filters_applied=filters,
                suggestions=suggestions,
                search_time=search_time,
                result_quality_score=self._calculate_quality_score(filtered_products, filters)
            )
            
            # Cache del resultado
            await self.cache_service.set(
                cache_key, 
                result.dict(), 
                ttl=self.search_cache_ttl
            )
            
            logger.info(f"Found {len(paginated_products)} products in {search_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return ProductSearchResponse(
                products=[],
                total_count=0,
                filters_applied=filters,
                search_time=0.0
            )
    
    async def _search_in_merchant(
        self,
        merchant: Merchant,
        filters: ProductSearchFilters
    ) -> List[ProductResponse]:
        """
        Busca productos en un merchant específico
        """
        try:
            config = self.merchant_configs[merchant]
            
            if config.get("enabled", False):
                # API oficial habilitada
                return await self._api_search(merchant, filters)
            elif config.get("scraping_enabled", False):
                # Web scraping como fallback
                return await self._scraping_search(merchant, filters)
            else:
                # Merchant no disponible, devolver productos mock para demo
                return await self._mock_search(merchant, filters)
                
        except Exception as e:
            logger.error(f"Error searching in {merchant}: {e}")
            return []
    
    async def _api_search(
        self,
        merchant: Merchant,
        filters: ProductSearchFilters
    ) -> List[ProductResponse]:
        """
        Búsqueda usando API oficial del merchant
        """
        config = self.merchant_configs[merchant]
        
        if merchant == Merchant.AMAZON:
            return await self._amazon_api_search(filters, config)
        elif merchant == Merchant.ASOS:
            return await self._asos_api_search(filters, config)
        else:
            return []
    
    async def _amazon_api_search(
        self,
        filters: ProductSearchFilters,
        config: Dict[str, Any]
    ) -> List[ProductResponse]:
        """
        Búsqueda en Amazon usando Product Advertising API
        """
        try:
            # Simular respuesta de Amazon API (requiere implementación completa de PA-API)
            # En producción, aquí iría la integración real con Amazon PA-API
            
            mock_products = [
                {
                    "id": f"amazon_product_{i}",
                    "merchant": "amazon",
                    "external_id": f"B0{i:08d}",
                    "merchant_url": f"https://amazon.com/dp/B0{i:08d}",
                    "name": f"{filters.query or 'Fashion'} Item {i}",
                    "description": f"High quality {filters.query or 'fashion'} item from Amazon",
                    "brand": f"Brand{i}",
                    "price": Decimal(f"{20 + i * 5}.99"),
                    "currency": "USD",
                    "category": filters.category or "TOPS",
                    "colors": ["black", "white", "blue"],
                    "sizes": ["S", "M", "L", "XL"],
                    "images": [f"https://via.placeholder.com/300x300?text=Amazon+Product+{i}"],
                    "rating": 4.0 + (i % 5) / 10,
                    "review_count": 100 + i * 50,
                    "tags": ["amazon", "fashion", "quality"],
                    "in_stock": True,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "last_checked": datetime.now()
                }
                for i in range(1, 6)
            ]
            
            return [ProductResponse(**product) for product in mock_products]
            
        except Exception as e:
            logger.error(f"Amazon API search error: {e}")
            return []
    
    async def _asos_api_search(
        self,
        filters: ProductSearchFilters,
        config: Dict[str, Any]
    ) -> List[ProductResponse]:
        """
        Búsqueda en ASOS usando su API
        """
        try:
            # Simular respuesta de ASOS API
            mock_products = [
                {
                    "id": f"asos_product_{i}",
                    "merchant": "asos",
                    "external_id": f"ASOS{i:06d}",
                    "merchant_url": f"https://asos.com/product/ASOS{i:06d}",
                    "name": f"ASOS {filters.query or 'Style'} {i}",
                    "description": f"Trendy {filters.query or 'fashion'} piece from ASOS",
                    "brand": "ASOS",
                    "price": Decimal(f"{15 + i * 3}.00"),
                    "sale_price": Decimal(f"{12 + i * 2}.00") if i % 2 == 0 else None,
                    "currency": "USD",
                    "category": filters.category or "DRESSES",
                    "colors": ["red", "green", "yellow"],
                    "sizes": ["XS", "S", "M", "L"],
                    "images": [f"https://via.placeholder.com/300x300?text=ASOS+Product+{i}"],
                    "rating": 3.8 + (i % 3) / 10,
                    "review_count": 50 + i * 25,
                    "tags": ["asos", "trendy", "affordable"],
                    "in_stock": True,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "last_checked": datetime.now()
                }
                for i in range(1, 4)
            ]
            
            return [ProductResponse(**product) for product in mock_products]
            
        except Exception as e:
            logger.error(f"ASOS API search error: {e}")
            return []
    
    async def _scraping_search(
        self,
        merchant: Merchant,
        filters: ProductSearchFilters
    ) -> List[ProductResponse]:
        """
        Búsqueda usando web scraping ético
        """
        try:
            # Implementación de web scraping con rate limiting y respeto al robots.txt
            # En producción, usar bibliotecas como Scrapy o BeautifulSoup
            
            # Por ahora, devolver productos mock para demo
            return await self._mock_search(merchant, filters)
            
        except Exception as e:
            logger.error(f"Scraping search error for {merchant}: {e}")
            return []
    
    async def _mock_search(
        self,
        merchant: Merchant,
        filters: ProductSearchFilters
    ) -> List[ProductResponse]:
        """
        Genera productos mock para demostración
        """
        try:
            merchant_data = {
                Merchant.ZARA: {
                    "brand": "Zara",
                    "price_range": (25, 80),
                    "style": "trendy"
                },
                Merchant.HM: {
                    "brand": "H&M",
                    "price_range": (10, 50),
                    "style": "affordable"
                },
                Merchant.UNIQLO: {
                    "brand": "Uniqlo",
                    "price_range": (15, 60),
                    "style": "minimalist"
                }
            }
            
            data = merchant_data.get(merchant, {"brand": "Generic", "price_range": (20, 70), "style": "fashion"})
            min_price, max_price = data["price_range"]
            
            mock_products = [
                {
                    "id": f"{merchant.value}_product_{i}",
                    "merchant": merchant.value,
                    "external_id": f"{merchant.value.upper()}{i:06d}",
                    "merchant_url": f"https://{merchant.value}.com/product/{merchant.value.upper()}{i:06d}",
                    "name": f"{data['brand']} {filters.query or 'Fashion'} Item {i}",
                    "description": f"{data['style'].title()} {filters.query or 'fashion'} from {data['brand']}",
                    "brand": data["brand"],
                    "price": Decimal(f"{min_price + i * ((max_price - min_price) // 5)}.00"),
                    "currency": "USD",
                    "category": filters.category or "TOPS",
                    "colors": ["black", "white", "gray"],
                    "sizes": ["S", "M", "L"],
                    "images": [f"https://via.placeholder.com/300x300?text={data['brand']}+{i}"],
                    "rating": 4.0 + (i % 4) / 10,
                    "review_count": 30 + i * 20,
                    "tags": [merchant.value, data["style"], "fashion"],
                    "in_stock": True,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "last_checked": datetime.now()
                }
                for i in range(1, 4)
            ]
            
            return [ProductResponse(**product) for product in mock_products]
            
        except Exception as e:
            logger.error(f"Mock search error for {merchant}: {e}")
            return []
    
    def _get_active_merchants(
        self,
        preferred_merchants: Optional[List[str]] = None
    ) -> List[Merchant]:
        """
        Obtiene lista de merchants activos para búsqueda
        """
        if preferred_merchants:
            # Filtrar merchants preferidos que estén disponibles
            return [
                Merchant(merchant) 
                for merchant in preferred_merchants 
                if merchant in [m.value for m in Merchant] and 
                (self.merchant_configs.get(Merchant(merchant), {}).get("enabled", False) or
                 self.merchant_configs.get(Merchant(merchant), {}).get("scraping_enabled", False))
            ]
        else:
            # Todos los merchants disponibles
            return [
                merchant 
                for merchant in Merchant 
                if (self.merchant_configs.get(merchant, {}).get("enabled", False) or
                    self.merchant_configs.get(merchant, {}).get("scraping_enabled", False))
            ]
    
    async def _check_rate_limit(self, merchant: Merchant) -> bool:
        """
        Verifica si el merchant está dentro de los límites de rate limiting
        """
        try:
            limits = self.rate_limits.get(merchant, {"requests_per_minute": 10})
            cache_key = f"rate_limit:{merchant.value}:minute"
            
            current_count = await self.cache_service.get(cache_key) or 0
            if current_count >= limits["requests_per_minute"]:
                logger.warning(f"Rate limit exceeded for {merchant}")
                return False
            
            # Incrementar contador
            await self.cache_service.set(cache_key, current_count + 1, ttl=60)
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check error for {merchant}: {e}")
            return False
    
    def _filter_and_rank_products(
        self,
        products: List[ProductResponse],
        filters: ProductSearchFilters
    ) -> List[ProductResponse]:
        """
        Filtra y rankea productos por relevancia
        """
        if not products:
            return []
        
        filtered = products
        
        # Aplicar filtros
        if filters.min_price is not None:
            filtered = [p for p in filtered if p.price >= filters.min_price]
        
        if filters.max_price is not None:
            filtered = [p for p in filtered if p.price <= filters.max_price]
        
        if filters.brand:
            filtered = [p for p in filtered if p.brand and p.brand.lower() in [b.lower() for b in filters.brand]]
        
        if filters.colors:
            filtered = [p for p in filtered if any(c in p.colors for c in filters.colors)]
        
        if filters.sizes:
            filtered = [p for p in filtered if any(s in p.sizes for s in filters.sizes)]
        
        if filters.on_sale is not None:
            if filters.on_sale:
                filtered = [p for p in filtered if p.sale_price is not None]
            else:
                filtered = [p for p in filtered if p.sale_price is None]
        
        if filters.in_stock is not None:
            filtered = [p for p in filtered if p.in_stock == filters.in_stock]
        
        if filters.min_rating is not None:
            filtered = [p for p in filtered if p.rating and p.rating >= filters.min_rating]
        
        # Rankear por relevancia
        def calculate_relevance_score(product: ProductResponse) -> float:
            score = 0.0
            
            # Score por rating (30%)
            if product.rating:
                score += (product.rating / 5.0) * 0.3
            
            # Score por número de reviews (20%)
            if product.review_count:
                # Normalizar (1000 reviews = score máximo)
                review_score = min(product.review_count / 1000.0, 1.0)
                score += review_score * 0.2
            
            # Score por coincidencia de query (30%)
            if filters.query:
                query_lower = filters.query.lower()
                name_match = query_lower in product.name.lower()
                desc_match = product.description and query_lower in product.description.lower()
                brand_match = product.brand and query_lower in product.brand.lower()
                
                if name_match:
                    score += 0.2
                if desc_match:
                    score += 0.05
                if brand_match:
                    score += 0.05
            
            # Score por precio competitivo (10%)
            if filters.min_price and filters.max_price:
                price_range = filters.max_price - filters.min_price
                if price_range > 0:
                    # Favorece precios en el rango medio-bajo
                    relative_price = (product.price - filters.min_price) / price_range
                    price_score = 1.0 - relative_price  # Menor precio = mayor score
                    score += price_score * 0.1
            
            # Score por disponibilidad (10%)
            if product.in_stock:
                score += 0.1
            
            return score
        
        # Ordenar por score de relevancia
        if filters.sort_by == "relevance":
            filtered.sort(key=calculate_relevance_score, reverse=True)
        elif filters.sort_by == "price_asc":
            filtered.sort(key=lambda p: p.price)
        elif filters.sort_by == "price_desc":
            filtered.sort(key=lambda p: p.price, reverse=True)
        elif filters.sort_by == "rating":
            filtered.sort(key=lambda p: p.rating or 0, reverse=True)
        elif filters.sort_by == "popularity":
            filtered.sort(key=lambda p: p.review_count, reverse=True)
        
        return filtered
    
    def _calculate_quality_score(
        self,
        products: List[ProductResponse],
        filters: ProductSearchFilters
    ) -> Optional[float]:
        """
        Calcula un score de calidad para los resultados de búsqueda
        """
        if not products:
            return 0.0
        
        # Métricas de calidad
        avg_rating = sum(p.rating or 0 for p in products) / len(products)
        in_stock_ratio = sum(1 for p in products if p.in_stock) / len(products)
        with_images_ratio = sum(1 for p in products if p.images) / len(products)
        price_variety = len(set(float(p.price) for p in products)) / len(products)
        
        # Score combinado
        quality_score = (
            (avg_rating / 5.0) * 0.3 +  # 30% rating
            in_stock_ratio * 0.25 +      # 25% disponibilidad
            with_images_ratio * 0.25 +   # 25% imágenes
            price_variety * 0.2           # 20% variedad de precios
        )
        
        return round(quality_score * 100, 2)
    
    async def _generate_search_suggestions(self, query: str) -> List[str]:
        """
        Genera sugerencias de búsqueda alternativas
        """
        try:
            # Sugerencias básicas basadas en el query
            suggestions = []
            
            # Sinónimos y términos relacionados
            synonyms = {
                "shirt": ["blouse", "top", "tee"],
                "pants": ["trousers", "jeans", "bottoms"],
                "dress": ["gown", "frock", "outfit"],
                "shoes": ["footwear", "sneakers", "boots"],
                "jacket": ["coat", "blazer", "cardigan"]
            }
            
            query_lower = query.lower()
            for term, alternatives in synonyms.items():
                if term in query_lower:
                    for alt in alternatives:
                        suggestion = query_lower.replace(term, alt)
                        suggestions.append(suggestion.title())
            
            # Sugerencias genéricas si no hay sinónimos
            if not suggestions:
                suggestions = [
                    f"{query} for women",
                    f"{query} for men",
                    f"casual {query}",
                    f"formal {query}",
                    f"{query} on sale"
                ]
            
            return suggestions[:3]  # Máximo 3 sugerencias
            
        except Exception as e:
            logger.error(f"Error generating search suggestions: {e}")
            return []
    
    async def generate_affiliate_link(
        self,
        product: ProductResponse,
        user_id: str,
        tracking_params: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Genera link de afiliado para un producto
        """
        try:
            merchant = Merchant(product.merchant)
            config = self.merchant_configs.get(merchant, {})
            affiliate_tag = config.get("affiliate_tag")
            
            if not affiliate_tag:
                logger.warning(f"No affiliate tag configured for {merchant}")
                return product.merchant_url
            
            # Crear tracking code único
            tracking_code = hashlib.md5(f"{user_id}:{product.id}:{datetime.now().isoformat()}".encode()).hexdigest()[:12]
            
            # Parámetros de afiliado por merchant
            if merchant == Merchant.AMAZON:
                affiliate_params = {
                    "tag": affiliate_tag,
                    "linkCode": "as2",
                    "creative": "9325",
                    "creativeASIN": product.external_id,
                    "tracking_id": tracking_code
                }
            elif merchant == Merchant.ASOS:
                affiliate_params = {
                    "affid": affiliate_tag,
                    "tracking": tracking_code
                }
            else:
                # Parámetros genéricos
                affiliate_params = {
                    "ref": affiliate_tag,
                    "tracking": tracking_code
                }
            
            # Agregar parámetros personalizados
            if tracking_params:
                affiliate_params.update(tracking_params)
            
            # Construir URL con parámetros
            base_url = product.merchant_url
            if "?" in base_url:
                affiliate_url = f"{base_url}&{urlencode(affiliate_params)}"
            else:
                affiliate_url = f"{base_url}?{urlencode(affiliate_params)}"
            
            logger.info(f"Generated affiliate link for product {product.id}")
            return affiliate_url
            
        except Exception as e:
            logger.error(f"Error generating affiliate link: {e}")
            return product.merchant_url
    
    async def track_affiliate_click(
        self,
        product_id: str,
        user_id: str,
        affiliate_link: str,
        source: str = "recommendation"
    ) -> str:
        """
        Registra un click en link de afiliado y retorna tracking ID
        """
        try:
            tracking_id = hashlib.md5(f"{user_id}:{product_id}:{datetime.now().isoformat()}".encode()).hexdigest()
            
            # Datos de tracking
            tracking_data = {
                "tracking_id": tracking_id,
                "user_id": user_id,
                "product_id": product_id,
                "affiliate_link": affiliate_link,
                "click_source": source,
                "clicked_at": datetime.now().isoformat(),
                "user_agent": "synthia-app",  # En producción, obtener del request
                "ip_address": "127.0.0.1"     # En producción, obtener del request
            }
            
            # Guardar en cache para tracking temporal
            cache_key = f"affiliate_click:{tracking_id}"
            await self.cache_service.set(cache_key, tracking_data, ttl=86400)  # 24 horas
            
            logger.info(f"Tracked affiliate click: {tracking_id}")
            return tracking_id
            
        except Exception as e:
            logger.error(f"Error tracking affiliate click: {e}")
            return ""
    
    async def get_commission_rate(self, merchant: Merchant) -> float:
        """
        Obtiene la tasa de comisión para un merchant
        """
        config = self.merchant_configs.get(merchant, {})
        return config.get("commission_rate", 0.0)
    
    async def update_product_prices(self, products: List[ProductResponse]) -> List[ProductResponse]:
        """
        Actualiza precios de productos de forma batch
        """
        try:
            # En producción, esto haría requests a las APIs para obtener precios actualizados
            # Por ahora, simular actualización
            
            updated_products = []
            for product in products:
                # Simular cambio de precio ocasional
                if hash(product.id) % 10 == 0:  # 10% de productos cambian precio
                    new_price = product.price * Decimal("0.95")  # 5% descuento
                    product.sale_price = new_price
                
                product.last_checked = datetime.now()
                updated_products.append(product)
            
            logger.info(f"Updated prices for {len(updated_products)} products")
            return updated_products
            
        except Exception as e:
            logger.error(f"Error updating product prices: {e}")
            return products
