"""
Sistema completo de caching con Redis para Synthia Style
Optimización de performance para análisis IA, sesiones y consultas
"""

import asyncio
import hashlib
import json
import time
import lz4.frame
import zstandard as zstd
from typing import Optional, Dict, Any, List, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

import aioredis
from aioredis import Redis
from fastapi import HTTPException

from app.core.config import settings
from app.core.logging import DatabaseLogger


@dataclass
class CacheMetrics:
    """Métricas de performance del cache"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    errors: int = 0
    total_time_saved_ms: float = 0.0
    last_reset: datetime = None
    
    @property
    def hit_rate(self) -> float:
        """Calcular hit rate"""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0
    
    @property
    def miss_rate(self) -> float:
        """Calcular miss rate"""
        return 100.0 - self.hit_rate


class CacheCompression:
    """Manejo de compresión para el cache"""
    
    @staticmethod
    def compress(data: bytes, algorithm: str = "lz4", level: int = 1) -> bytes:
        """Comprimir datos"""
        try:
            if algorithm == "lz4":
                return lz4.frame.compress(data, compression_level=level)
            elif algorithm == "zstd":
                cctx = zstd.ZstdCompressor(level=level)
                return cctx.compress(data)
            elif algorithm == "gzip":
                import gzip
                return gzip.compress(data, compresslevel=level)
            else:
                return data
        except Exception:
            return data
    
    @staticmethod
    def decompress(data: bytes, algorithm: str = "lz4") -> bytes:
        """Descomprimir datos"""
        try:
            if algorithm == "lz4":
                return lz4.frame.decompress(data)
            elif algorithm == "zstd":
                dctx = zstd.ZstdDecompressor()
                return dctx.decompress(data)
            elif algorithm == "gzip":
                import gzip
                return gzip.decompress(data)
            else:
                return data
        except Exception:
            return data


class CacheKeyGenerator:
    """Generador de claves de cache con namespaces"""
    
    @staticmethod
    def _sanitize_key(key: str) -> str:
        """Sanitizar clave para Redis"""
        return key.replace(" ", "_").replace(":", "_").replace("/", "_")
    
    @classmethod
    def user_key(cls, user_id: str, suffix: str = "") -> str:
        """Generar clave para datos de usuario"""
        key = f"{settings.CACHE_USER_NAMESPACE}:{user_id}"
        if suffix:
            key += f":{cls._sanitize_key(suffix)}"
        return key
    
    @classmethod
    def analysis_key(cls, analysis_type: str, image_hash: str) -> str:
        """Generar clave para análisis IA"""
        return f"{settings.CACHE_ANALYSIS_NAMESPACE}:{analysis_type}:{image_hash}"
    
    @classmethod
    def recommendations_key(cls, category: str, filters_hash: str) -> str:
        """Generar clave para recomendaciones"""
        return f"{settings.CACHE_RECOMMENDATIONS_NAMESPACE}:{category}:{filters_hash}"
    
    @classmethod
    def config_key(cls, config_type: str, identifier: str = "") -> str:
        """Generar clave para configuraciones"""
        key = f"{settings.CACHE_CONFIG_NAMESPACE}:{config_type}"
        if identifier:
            key += f":{cls._sanitize_key(identifier)}"
        return key
    
    @classmethod
    def session_key(cls, user_id: str, session_type: str = "main") -> str:
        """Generar clave para sesiones"""
        return f"{settings.CACHE_SESSION_NAMESPACE}:{user_id}:{session_type}"
    
    @classmethod
    def create_hash(cls, data: Any) -> str:
        """Crear hash único para datos complejos"""
        if isinstance(data, dict):
            # Ordenar keys para hash consistente
            sorted_data = json.dumps(data, sort_keys=True, default=str)
        else:
            sorted_data = str(data)
        
        return hashlib.sha256(sorted_data.encode()).hexdigest()[:16]


class CacheService:
    """Servicio principal de cache con Redis"""
    
    def __init__(self):
        self.redis: Optional[Redis] = None
        self.metrics = CacheMetrics(last_reset=datetime.utcnow())
        self.compression = CacheCompression()
        self.key_generator = CacheKeyGenerator()
        self._connection_pool = None
        
    async def initialize(self) -> bool:
        """Inicializar conexión Redis"""
        if not settings.REDIS_ENABLED:
            DatabaseLogger.log_info("cache_init", "cache", "Redis cache disabled")
            return False
            
        try:
            # Crear pool de conexiones
            self._connection_pool = aioredis.ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT,
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                decode_responses=False,  # Manejar bytes para compresión
                retry_on_timeout=True
            )
            
            self.redis = Redis(connection_pool=self._connection_pool)
            
            # Test de conectividad
            await self.redis.ping()
            
            DatabaseLogger.log_info("cache_init", "cache", "Redis cache initialized successfully")
            
            # Warmup del cache si está habilitado
            if settings.CACHE_WARMUP_ENABLED:
                asyncio.create_task(self._warmup_cache())
            
            return True
            
        except Exception as e:
            DatabaseLogger.log_error("cache_init", "cache", e)
            self.redis = None
            return False
    
    async def close(self):
        """Cerrar conexiones Redis"""
        if self.redis:
            await self.redis.close()
        if self._connection_pool:
            await self._connection_pool.disconnect()
    
    @asynccontextmanager
    async def _redis_operation(self):
        """Context manager para operaciones Redis con manejo de errores"""
        if not self.redis:
            raise HTTPException(status_code=503, detail="Cache service not available")
        
        try:
            yield self.redis
        except Exception as e:
            self.metrics.errors += 1
            DatabaseLogger.log_error("redis_operation", "cache", e)
            raise
    
    def _serialize_data(self, data: Any) -> bytes:
        """Serializar datos para almacenamiento"""
        try:
            if settings.CACHE_SERIALIZATION_FORMAT == "json":
                serialized = json.dumps(data, default=str).encode('utf-8')
            else:
                # Fallback a JSON
                serialized = json.dumps(data, default=str).encode('utf-8')
            
            # Comprimir si está habilitado
            if settings.CACHE_COMPRESSION_ENABLED:
                serialized = self.compression.compress(
                    serialized, 
                    settings.CACHE_COMPRESSION_ALGORITHM,
                    settings.CACHE_COMPRESSION_LEVEL
                )
            
            return serialized
            
        except Exception as e:
            DatabaseLogger.log_error("serialize_data", "cache", e)
            raise
    
    def _deserialize_data(self, data: bytes) -> Any:
        """Deserializar datos del cache"""
        try:
            # Descomprimir si está habilitado
            if settings.CACHE_COMPRESSION_ENABLED:
                data = self.compression.decompress(
                    data, 
                    settings.CACHE_COMPRESSION_ALGORITHM
                )
            
            # Deserializar
            if settings.CACHE_SERIALIZATION_FORMAT == "json":
                return json.loads(data.decode('utf-8'))
            else:
                # Fallback a JSON
                return json.loads(data.decode('utf-8'))
                
        except Exception as e:
            DatabaseLogger.log_error("deserialize_data", "cache", e)
            raise
    
    # =================== MÉTODOS PRINCIPALES DE CACHE ===================
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Obtener valor del cache"""
        if not self.redis:
            return default
            
        start_time = time.perf_counter()
        
        try:
            async with self._redis_operation() as redis:
                data = await redis.get(key)
                
                if data is None:
                    self.metrics.misses += 1
                    return default
                
                self.metrics.hits += 1
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                self.metrics.total_time_saved_ms += elapsed_ms
                
                return self._deserialize_data(data)
                
        except Exception as e:
            DatabaseLogger.log_error("cache_get", "cache", e, {"key": key})
            return default
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Establecer valor en cache"""
        if not self.redis:
            return False
            
        try:
            async with self._redis_operation() as redis:
                serialized_data = self._serialize_data(value)
                
                if ttl:
                    await redis.setex(key, ttl, serialized_data)
                else:
                    await redis.set(key, serialized_data)
                
                self.metrics.sets += 1
                return True
                
        except Exception as e:
            DatabaseLogger.log_error("cache_set", "cache", e, {"key": key})
            return False
    
    async def delete(self, key: str) -> bool:
        """Eliminar clave del cache"""
        if not self.redis:
            return False
            
        try:
            async with self._redis_operation() as redis:
                result = await redis.delete(key)
                
                if result > 0:
                    self.metrics.deletes += 1
                    return True
                return False
                
        except Exception as e:
            DatabaseLogger.log_error("cache_delete", "cache", e, {"key": key})
            return False
    
    async def exists(self, key: str) -> bool:
        """Verificar si existe una clave"""
        if not self.redis:
            return False
            
        try:
            async with self._redis_operation() as redis:
                return await redis.exists(key) > 0
        except Exception:
            return False
    
    async def ttl(self, key: str) -> int:
        """Obtener TTL de una clave"""
        if not self.redis:
            return -1
            
        try:
            async with self._redis_operation() as redis:
                return await redis.ttl(key)
        except Exception:
            return -1
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidar claves que coincidan con un patrón"""
        if not self.redis:
            return 0
            
        try:
            async with self._redis_operation() as redis:
                keys = await redis.keys(pattern)
                if keys:
                    deleted = await redis.delete(*keys)
                    self.metrics.deletes += deleted
                    return deleted
                return 0
                
        except Exception as e:
            DatabaseLogger.log_error("cache_invalidate_pattern", "cache", e, {"pattern": pattern})
            return 0
    
    # =================== MÉTODOS ESPECÍFICOS PARA ANÁLISIS IA ===================
    
    async def get_analysis_cache(self, image_hash: str, analysis_type: str) -> Optional[Dict]:
        """Obtener resultado de análisis IA del cache"""
        key = self.key_generator.analysis_key(analysis_type, image_hash)
        return await self.get(key)
    
    async def set_analysis_cache(self, image_hash: str, analysis_type: str, result: Dict, 
                               ttl: Optional[int] = None) -> bool:
        """Guardar resultado de análisis IA en cache"""
        key = self.key_generator.analysis_key(analysis_type, image_hash)
        
        # TTL específico por tipo de análisis
        if ttl is None:
            if analysis_type == "facial":
                ttl = settings.CACHE_AI_ANALYSIS_TTL_SECONDS
            elif analysis_type == "chromatic":
                ttl = settings.CACHE_CHROMATIC_ANALYSIS_TTL_SECONDS
            else:
                ttl = settings.CACHE_TTL_SECONDS
        
        # Agregar metadata del cache
        cache_data = {
            "result": result,
            "analysis_type": analysis_type,
            "image_hash": image_hash,
            "cached_at": datetime.utcnow().isoformat(),
            "cache_version": "1.0"
        }
        
        return await self.set(key, cache_data, ttl)
    
    async def create_image_hash(self, image_data: Union[str, bytes]) -> str:
        """Crear hash único para imagen"""
        if isinstance(image_data, str):
            # Si es base64, decodificar primero
            try:
                import base64
                if image_data.startswith('data:image'):
                    # Remover header de data URL
                    image_data = image_data.split(',')[1]
                image_bytes = base64.b64decode(image_data)
            except Exception:
                image_bytes = image_data.encode()
        else:
            image_bytes = image_data
        
        return hashlib.sha256(image_bytes).hexdigest()
    
    # =================== MÉTODOS PARA SESIONES DE USUARIO ===================
    
    async def get_user_session(self, user_id: str, session_type: str = "main") -> Optional[Dict]:
        """Obtener sesión de usuario del cache"""
        key = self.key_generator.session_key(user_id, session_type)
        return await self.get(key)
    
    async def set_user_session(self, user_id: str, session_data: Dict, 
                             session_type: str = "main", ttl: Optional[int] = None) -> bool:
        """Guardar sesión de usuario en cache"""
        key = self.key_generator.session_key(user_id, session_type)
        
        if ttl is None:
            ttl = settings.CACHE_USER_SESSION_TTL_SECONDS
        
        # Agregar metadata de sesión
        cache_data = {
            "session_data": session_data,
            "user_id": user_id,
            "session_type": session_type,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(seconds=ttl)).isoformat()
        }
        
        return await self.set(key, cache_data, ttl)
    
    async def invalidate_user_cache(self, user_id: str) -> int:
        """Invalidar todo el cache de un usuario"""
        pattern = f"{settings.CACHE_USER_NAMESPACE}:{user_id}:*"
        return await self.invalidate_pattern(pattern)
    
    async def invalidate_user_sessions(self, user_id: str) -> int:
        """Invalidar todas las sesiones de un usuario"""
        pattern = f"{settings.CACHE_SESSION_NAMESPACE}:{user_id}:*"
        return await self.invalidate_pattern(pattern)
    
    # =================== MÉTODOS PARA RECOMENDACIONES ===================
    
    async def get_recommendations_cache(self, category: str, filters: Dict) -> Optional[List]:
        """Obtener recomendaciones del cache"""
        filters_hash = self.key_generator.create_hash(filters)
        key = self.key_generator.recommendations_key(category, filters_hash)
        
        cached_data = await self.get(key)
        if cached_data and isinstance(cached_data, dict):
            return cached_data.get("recommendations")
        return cached_data
    
    async def set_recommendations_cache(self, category: str, filters: Dict, 
                                      recommendations: List, ttl: Optional[int] = None) -> bool:
        """Guardar recomendaciones en cache"""
        filters_hash = self.key_generator.create_hash(filters)
        key = self.key_generator.recommendations_key(category, filters_hash)
        
        if ttl is None:
            ttl = settings.CACHE_RECOMMENDATIONS_TTL_SECONDS
        
        cache_data = {
            "recommendations": recommendations,
            "category": category,
            "filters": filters,
            "filters_hash": filters_hash,
            "cached_at": datetime.utcnow().isoformat(),
            "count": len(recommendations)
        }
        
        return await self.set(key, cache_data, ttl)
    
    # =================== MÉTODOS PARA CONFIGURACIONES ===================
    
    async def get_config_cache(self, config_type: str, identifier: str = "") -> Optional[Any]:
        """Obtener configuración del cache"""
        key = self.key_generator.config_key(config_type, identifier)
        return await self.get(key)
    
    async def set_config_cache(self, config_type: str, config_data: Any, 
                             identifier: str = "", ttl: Optional[int] = None) -> bool:
        """Guardar configuración en cache"""
        key = self.key_generator.config_key(config_type, identifier)
        
        if ttl is None:
            ttl = settings.CACHE_CONFIG_TTL_SECONDS
        
        return await self.set(key, config_data, ttl)
    
    # =================== MÉTODOS DE WARMUP Y PRELOADING ===================
    
    async def _warmup_cache(self):
        """Warmup del cache con datos críticos"""
        try:
            DatabaseLogger.log_info("cache_warmup", "cache", "Starting cache warmup")
            
            # Precargar configuraciones críticas
            await self._warmup_subscription_features()
            await self._warmup_system_config()
            
            DatabaseLogger.log_info("cache_warmup", "cache", "Cache warmup completed")
            
        except Exception as e:
            DatabaseLogger.log_error("cache_warmup", "cache", e)
    
    async def _warmup_subscription_features(self):
        """Precargar features de suscripción"""
        # Este método se implementará cuando se integre con la base de datos
        pass
    
    async def _warmup_system_config(self):
        """Precargar configuraciones del sistema"""
        # Este método se implementará cuando se integre con la base de datos
        pass
    
    # =================== MÉTODOS DE MÉTRICAS Y MONITORING ===================
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Obtener métricas del cache"""
        metrics_data = asdict(self.metrics)
        
        # Agregar información adicional de Redis
        if self.redis:
            try:
                async with self._redis_operation() as redis:
                    info = await redis.info()
                    metrics_data.update({
                        "redis_connected_clients": info.get("connected_clients", 0),
                        "redis_used_memory": info.get("used_memory", 0),
                        "redis_used_memory_human": info.get("used_memory_human", "0B"),
                        "redis_keyspace_hits": info.get("keyspace_hits", 0),
                        "redis_keyspace_misses": info.get("keyspace_misses", 0),
                        "redis_total_commands_processed": info.get("total_commands_processed", 0)
                    })
            except Exception:
                pass
        
        return metrics_data
    
    async def reset_metrics(self):
        """Resetear métricas del cache"""
        self.metrics = CacheMetrics(last_reset=datetime.utcnow())
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check del servicio de cache"""
        if not self.redis:
            return {
                "status": "disabled",
                "message": "Redis cache is disabled",
                "healthy": False
            }
        
        try:
            async with self._redis_operation() as redis:
                start_time = time.perf_counter()
                await redis.ping()
                response_time = (time.perf_counter() - start_time) * 1000
                
                return {
                    "status": "healthy",
                    "response_time_ms": round(response_time, 2),
                    "healthy": True,
                    "metrics": await self.get_metrics()
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "healthy": False
            }


# Instancia global del servicio de cache
cache_service = CacheService()


# =================== DECORADORES PARA CACHE AUTOMÁTICO ===================

def cached(ttl: int = None, namespace: str = "default", key_prefix: str = ""):
    """Decorador para cache automático de funciones"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            if not cache_service.redis:
                return await func(*args, **kwargs)
            
            # Generar clave de cache
            cache_key = f"{namespace}:{key_prefix}:{cache_service.key_generator.create_hash((args, kwargs))}"
            
            # Intentar obtener del cache
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Ejecutar función y guardar resultado
            result = await func(*args, **kwargs)
            await cache_service.set(cache_key, result, ttl or settings.CACHE_TTL_SECONDS)
            
            return result
        return wrapper
    return decorator


def cache_invalidate_on_update(pattern: str):
    """Decorador para invalidar cache automáticamente"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            if cache_service.redis:
                await cache_service.invalidate_pattern(pattern)
            
            return result
        return wrapper
    return decorator
