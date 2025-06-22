"""
Middleware de cache para FastAPI
Manejo automático de cache para endpoints y métricas de performance
"""

import time
from typing import Dict, Any, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.logging import DatabaseLogger
from app.services.cache_service import cache_service


class CacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware para manejo automático de cache en endpoints específicos
    """
    
    def __init__(self, app, cache_endpoints: Optional[Dict[str, Dict]] = None):
        super().__init__(app)
        self.cache_endpoints = cache_endpoints or {}
        self.metrics = {
            "requests_total": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "response_time_saved_ms": 0.0
        }
    
    async def dispatch(self, request: Request, call_next):
        """Procesar request con lógica de cache"""
        start_time = time.perf_counter()
        
        # Verificar si el endpoint debe usar cache
        cache_config = self._should_cache_endpoint(request)
        
        if cache_config and request.method == "GET":
            # Intentar obtener respuesta del cache
            cached_response = await self._get_cached_response(request, cache_config)
            if cached_response:
                self.metrics["cache_hits"] += 1
                elapsed_time = (time.perf_counter() - start_time) * 1000
                self.metrics["response_time_saved_ms"] += elapsed_time
                return cached_response
        
        # Procesar request normalmente
        response = await call_next(request)
        
        # Cachear respuesta si es exitosa y está configurado
        if (cache_config and 
            request.method == "GET" and 
            response.status_code == 200):
            await self._cache_response(request, response, cache_config)
            if cache_config:
                self.metrics["cache_misses"] += 1
        
        self.metrics["requests_total"] += 1
        
        # Agregar headers de cache info
        if cache_config:
            response.headers["X-Cache-Status"] = "MISS" if not cached_response else "HIT"
            response.headers["X-Cache-TTL"] = str(cache_config.get("ttl", 0))
        
        return response
    
    def _should_cache_endpoint(self, request: Request) -> Optional[Dict]:
        """Verificar si el endpoint debe usar cache"""
        path = request.url.path
        
        # Verificar configuración específica de endpoints
        for pattern, config in self.cache_endpoints.items():
            if pattern in path:
                return config
        
        # Reglas automáticas para endpoints comunes
        auto_cache_rules = {
            "/api/v1/users/analytics": {"ttl": settings.CACHE_ANALYTICS_TTL_SECONDS},
            "/api/v1/users/subscription/features": {"ttl": settings.CACHE_SUBSCRIPTION_TTL_SECONDS},
            "/api/v1/facial/history": {"ttl": settings.CACHE_TTL_SECONDS},
            "/api/v1/chromatic/history": {"ttl": settings.CACHE_TTL_SECONDS},
        }
        
        for pattern, config in auto_cache_rules.items():
            if pattern in path:
                return config
        
        return None
    
    async def _get_cached_response(self, request: Request, cache_config: Dict) -> Optional[Response]:
        """Obtener respuesta cacheada"""
        try:
            cache_key = self._generate_cache_key(request)
            cached_data = await cache_service.get(cache_key)
            
            if cached_data:
                # Recrear respuesta desde cache
                response_data = cached_data.get("response_data")
                headers = cached_data.get("headers", {})
                status_code = cached_data.get("status_code", 200)
                
                response = JSONResponse(
                    content=response_data,
                    status_code=status_code,
                    headers=headers
                )
                
                # Agregar headers de cache
                response.headers["X-Cache-Status"] = "HIT"
                response.headers["X-Cache-Age"] = str(cached_data.get("age", 0))
                
                return response
                
        except Exception as e:
            DatabaseLogger.log_error("cache_middleware_get", "cache", e)
        
        return None
    
    async def _cache_response(self, request: Request, response: Response, cache_config: Dict):
        """Cachear respuesta"""
        try:
            cache_key = self._generate_cache_key(request)
            ttl = cache_config.get("ttl", settings.CACHE_TTL_SECONDS)
            
            # Solo cachear respuestas JSON
            content_type = response.headers.get("content-type", "")
            if "application/json" not in content_type:
                return
            
            # Leer contenido de la respuesta
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            # Recrear respuesta con el contenido leído
            import json
            response_data = json.loads(response_body.decode())
            
            # Preparar datos para cache
            cache_data = {
                "response_data": response_data,
                "headers": dict(response.headers),
                "status_code": response.status_code,
                "cached_at": time.time(),
                "age": 0
            }
            
            # Guardar en cache
            await cache_service.set(cache_key, cache_data, ttl)
            
            # Recrear respuesta
            response = JSONResponse(
                content=response_data,
                status_code=response.status_code,
                headers=response.headers
            )
            
        except Exception as e:
            DatabaseLogger.log_error("cache_middleware_set", "cache", e)
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generar clave de cache para el request"""
        path = request.url.path
        query_params = str(request.query_params)
        user_id = getattr(request.state, "user_id", "anonymous")
        
        cache_key = f"endpoint:{user_id}:{path}:{cache_service.key_generator.create_hash(query_params)}"
        return cache_key
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtener métricas del middleware"""
        hit_rate = 0.0
        if self.metrics["requests_total"] > 0:
            hit_rate = (self.metrics["cache_hits"] / self.metrics["requests_total"]) * 100
        
        return {
            **self.metrics,
            "cache_hit_rate": round(hit_rate, 2),
            "avg_time_saved_ms": (
                self.metrics["response_time_saved_ms"] / max(self.metrics["cache_hits"], 1)
            )
        }


class CacheMetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware ligero para recopilar métricas de cache
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.start_time = time.time()
    
    async def dispatch(self, request: Request, call_next):
        """Agregar métricas de cache a responses"""
        start_time = time.perf_counter()
        
        response = await call_next(request)
        
        # Agregar headers informativos
        if settings.CACHE_METRICS_ENABLED:
            processing_time = (time.perf_counter() - start_time) * 1000
            response.headers["X-Processing-Time"] = f"{processing_time:.2f}ms"
            
            # Agregar información de cache si está disponible
            if hasattr(cache_service, "metrics"):
                cache_metrics = await cache_service.get_metrics()
                response.headers["X-Cache-Hit-Rate"] = f"{cache_metrics.get('hit_rate', 0):.1f}%"
        
        return response


# Configuración de endpoints específicos para cache automático
CACHE_ENDPOINT_CONFIG = {
    # Analytics y métricas (30 minutos)
    "/api/v1/users/analytics": {
        "ttl": settings.CACHE_ANALYTICS_TTL_SECONDS,
        "vary_by_user": True
    },
    
    # Features de suscripción (30 minutos)
    "/api/v1/users/subscription/features": {
        "ttl": settings.CACHE_SUBSCRIPTION_TTL_SECONDS,
        "vary_by_user": True
    },
    
    # Historial de análisis (1 hora)
    "/api/v1/facial/history": {
        "ttl": settings.CACHE_TTL_SECONDS,
        "vary_by_user": True
    },
    "/api/v1/chromatic/history": {
        "ttl": settings.CACHE_TTL_SECONDS,
        "vary_by_user": True
    },
    
    # Dashboard de usuario (15 minutos)
    "/api/v1/users/dashboard": {
        "ttl": 900,  # 15 minutos
        "vary_by_user": True
    },
    
    # Estadísticas administrativas (1 hora)
    "/api/v1/users/statistics": {
        "ttl": settings.CACHE_TTL_SECONDS,
        "admin_only": True
    }
}


def create_cache_middleware():
    """Factory para crear middleware de cache"""
    return CacheMiddleware(None, CACHE_ENDPOINT_CONFIG)


def create_cache_metrics_middleware():
    """Factory para crear middleware de métricas"""
    return CacheMetricsMiddleware(None)
