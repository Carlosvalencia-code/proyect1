"""
Endpoints para gestión y monitoreo del sistema de cache Redis
Métricas, health checks y administración de cache
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path

from app.schemas.common import APIResponse
from app.core.security import get_current_user_id
from app.db.database import get_db
from app.services.cache_service import cache_service
from app.schemas.user import UserRole

router = APIRouter()


@router.get("/health", response_model=Dict[str, Any])
async def cache_health_check():
    """
    Health check del servicio de cache Redis
    """
    try:
        health_status = await cache_service.health_check()
        return health_status
        
    except Exception as e:
        return {
            "status": "error",
            "healthy": False,
            "error": str(e)
        }


@router.get("/metrics", response_model=Dict[str, Any])
async def get_cache_metrics(
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Obtener métricas detalladas del cache (solo para administradores)
    """
    try:
        # Verificar permisos de administrador
        current_user = await db.user.find_unique(where={"id": current_user_id})
        if not current_user or current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para acceder a esta información"
            )
        
        metrics = await cache_service.get_metrics()
        
        return {
            "cache_metrics": metrics,
            "timestamp": "now",
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo métricas: {str(e)}"
        )


@router.post("/metrics/reset", response_model=APIResponse)
async def reset_cache_metrics(
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Resetear métricas del cache (solo para administradores)
    """
    try:
        # Verificar permisos de administrador
        current_user = await db.user.find_unique(where={"id": current_user_id})
        if not current_user or current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para realizar esta acción"
            )
        
        await cache_service.reset_metrics()
        
        return APIResponse(message="Métricas del cache reseteadas exitosamente")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reseteando métricas: {str(e)}"
        )


@router.get("/keys", response_model=Dict[str, Any])
async def get_cache_keys(
    pattern: Optional[str] = Query(default="*", description="Patrón de búsqueda"),
    limit: int = Query(default=100, ge=1, le=1000, description="Límite de resultados"),
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Obtener lista de claves en el cache (solo para administradores)
    """
    try:
        # Verificar permisos de administrador
        current_user = await db.user.find_unique(where={"id": current_user_id})
        if not current_user or current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para acceder a esta información"
            )
        
        if not cache_service.redis:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Servicio de cache no disponible"
            )
        
        # Obtener claves que coincidan con el patrón
        async with cache_service._redis_operation() as redis:
            keys = await redis.keys(pattern)
            
            # Limitar resultados
            keys = keys[:limit]
            
            # Obtener información adicional para cada clave
            key_info = []
            for key in keys:
                try:
                    key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                    ttl = await redis.ttl(key)
                    key_info.append({
                        "key": key_str,
                        "ttl": ttl,
                        "expires": ttl > 0
                    })
                except Exception:
                    continue
        
        return {
            "keys": key_info,
            "total_found": len(key_info),
            "pattern": pattern,
            "limit": limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo claves: {str(e)}"
        )


@router.delete("/keys/{key_pattern}", response_model=APIResponse)
async def delete_cache_keys(
    key_pattern: str = Path(..., description="Patrón de claves a eliminar"),
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Eliminar claves del cache por patrón (solo para administradores)
    """
    try:
        # Verificar permisos de administrador
        current_user = await db.user.find_unique(where={"id": current_user_id})
        if not current_user or current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para realizar esta acción"
            )
        
        # Prevenir eliminación masiva accidental
        if key_pattern in ["*", "**", ""]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Patrón muy amplio. Especifica un patrón más específico"
            )
        
        deleted_count = await cache_service.invalidate_pattern(key_pattern)
        
        return APIResponse(
            message=f"Se eliminaron {deleted_count} claves que coinciden con el patrón '{key_pattern}'"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error eliminando claves: {str(e)}"
        )


@router.get("/analysis/{analysis_type}/stats", response_model=Dict[str, Any])
async def get_analysis_cache_stats(
    analysis_type: str = Path(..., description="Tipo de análisis (facial, chromatic)"),
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Obtener estadísticas de cache para un tipo de análisis específico
    """
    try:
        # Verificar permisos de administrador
        current_user = await db.user.find_unique(where={"id": current_user_id})
        if not current_user or current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para acceder a esta información"
            )
        
        if analysis_type not in ["facial", "chromatic"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de análisis debe ser 'facial' o 'chromatic'"
            )
        
        if not cache_service.redis:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Servicio de cache no disponible"
            )
        
        # Buscar claves de análisis
        pattern = f"analysis:{analysis_type}:*"
        
        async with cache_service._redis_operation() as redis:
            keys = await redis.keys(pattern)
            
            total_entries = len(keys)
            
            # Analizar TTL de las entradas
            ttl_stats = {
                "expired": 0,
                "expiring_soon": 0,  # < 1 hora
                "healthy": 0
            }
            
            total_size = 0
            
            for key in keys[:100]:  # Limitar análisis a 100 claves
                try:
                    ttl = await redis.ttl(key)
                    
                    if ttl == -1:  # No expira
                        ttl_stats["healthy"] += 1
                    elif ttl <= 0:  # Expirado
                        ttl_stats["expired"] += 1
                    elif ttl < 3600:  # Expira en menos de 1 hora
                        ttl_stats["expiring_soon"] += 1
                    else:
                        ttl_stats["healthy"] += 1
                    
                    # Estimar tamaño
                    memory_usage = await redis.memory_usage(key)
                    if memory_usage:
                        total_size += memory_usage
                        
                except Exception:
                    continue
        
        return {
            "analysis_type": analysis_type,
            "total_entries": total_entries,
            "ttl_stats": ttl_stats,
            "estimated_size_bytes": total_size,
            "estimated_size_mb": round(total_size / (1024 * 1024), 2),
            "pattern": pattern
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )


@router.post("/invalidate/user/{user_id}", response_model=APIResponse)
async def invalidate_user_cache(
    user_id: str = Path(..., description="ID del usuario"),
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Invalidar todo el cache de un usuario específico
    """
    try:
        # Verificar permisos: admin o el propio usuario
        current_user = await db.user.find_unique(where={"id": current_user_id})
        
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario actual no encontrado"
            )
        
        # Solo el propio usuario o un admin pueden invalidar el cache
        if (current_user_id != user_id and 
            current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para invalidar el cache de este usuario"
            )
        
        # Verificar que el usuario objetivo existe
        target_user = await db.user.find_unique(where={"id": user_id})
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario objetivo no encontrado"
            )
        
        # Invalidar cache del usuario
        deleted_count = await cache_service.invalidate_user_cache(user_id)
        
        return APIResponse(
            message=f"Se invalidaron {deleted_count} entradas de cache para el usuario {user_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error invalidando cache de usuario: {str(e)}"
        )


@router.post("/warmup", response_model=APIResponse)
async def warmup_cache(
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Ejecutar warmup manual del cache (solo para administradores)
    """
    try:
        # Verificar permisos de administrador
        current_user = await db.user.find_unique(where={"id": current_user_id})
        if not current_user or current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para realizar esta acción"
            )
        
        # Ejecutar warmup
        await cache_service._warmup_cache()
        
        return APIResponse(message="Warmup del cache ejecutado exitosamente")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error ejecutando warmup: {str(e)}"
        )


@router.get("/info", response_model=Dict[str, Any])
async def get_cache_info():
    """
    Obtener información general del sistema de cache
    """
    try:
        info = {
            "redis_enabled": cache_service.redis is not None,
            "compression_enabled": settings.CACHE_COMPRESSION_ENABLED,
            "compression_algorithm": settings.CACHE_COMPRESSION_ALGORITHM,
            "metrics_enabled": settings.CACHE_METRICS_ENABLED,
            "warmup_enabled": settings.CACHE_WARMUP_ENABLED,
            "ttl_config": {
                "default": settings.CACHE_TTL_SECONDS,
                "analytics": settings.CACHE_ANALYTICS_TTL_SECONDS,
                "user_session": settings.CACHE_USER_SESSION_TTL_SECONDS,
                "ai_analysis": settings.CACHE_AI_ANALYSIS_TTL_SECONDS,
                "chromatic_analysis": settings.CACHE_CHROMATIC_ANALYSIS_TTL_SECONDS,
                "recommendations": settings.CACHE_RECOMMENDATIONS_TTL_SECONDS,
                "config": settings.CACHE_CONFIG_TTL_SECONDS
            },
            "namespaces": {
                "user": settings.CACHE_USER_NAMESPACE,
                "analysis": settings.CACHE_ANALYSIS_NAMESPACE,
                "recommendations": settings.CACHE_RECOMMENDATIONS_NAMESPACE,
                "config": settings.CACHE_CONFIG_NAMESPACE,
                "session": settings.CACHE_SESSION_NAMESPACE
            }
        }
        
        if cache_service.redis:
            health = await cache_service.health_check()
            info["health"] = health
        
        return info
        
    except Exception as e:
        return {
            "error": str(e),
            "redis_enabled": False
        }
