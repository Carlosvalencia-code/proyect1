"""
Aplicación principal FastAPI para Synthia Style
Configuración de la aplicación, middleware y rutas
"""

import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.logging import (
    configure_logging, 
    log_startup_info, 
    log_shutdown_info,
    RequestLogger
)
from app.core.security import CORS_CONFIG
from app.db.database import startup_database, shutdown_database
from app.api.v1.api import api_router
from app.services.cache_service import cache_service
from app.core.cache_middleware import create_cache_middleware, create_cache_metrics_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestión del ciclo de vida de la aplicación
    """
    # Startup
    try:
        log_startup_info()
        
        # Inicializar base de datos
        await startup_database()
        
        # Inicializar cache Redis
        cache_initialized = await cache_service.initialize()
        if cache_initialized:
            print("✅ Redis cache initialized successfully")
        else:
            print("⚠️  Redis cache initialization failed or disabled")
        
        yield
        
    finally:
        # Shutdown
        log_shutdown_info()
        
        # Cerrar conexiones
        await shutdown_database()
        await cache_service.close()


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API moderna para análisis de estilo personal con IA",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)


# Configurar logging
configure_logging()


# Middleware para CORS
app.add_middleware(
    CORSMiddleware,
    **CORS_CONFIG
)

# Middleware para compresión
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Middleware para cache (solo si está habilitado)
if settings.REDIS_ENABLED:
    cache_middleware = create_cache_middleware()
    metrics_middleware = create_cache_metrics_middleware()
    app.add_middleware(cache_middleware.__class__)
    app.add_middleware(metrics_middleware.__class__)


# Middleware para logging de requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para logging de requests HTTP"""
    start_time = time.time()
    
    # Procesar request
    response = await call_next(request)
    
    # Calcular tiempo de respuesta
    process_time = time.time() - start_time
    
    # Log del request
    RequestLogger.log_request(
        request=request,
        response_time=process_time,
        status_code=response.status_code
    )
    
    # Agregar header de tiempo de respuesta
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# Middleware para manejo de errores globales
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Manejador global de excepciones HTTP"""
    
    # Log del error
    RequestLogger.log_error(
        request=request,
        error=exc,
        status_code=exc.status_code
    )
    
    # Respuesta de error estandarizada
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "error_code": f"HTTP_{exc.status_code}",
            "timestamp": time.time()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Manejador de excepciones generales"""
    
    # Log del error
    RequestLogger.log_error(
        request=request,
        error=exc,
        status_code=500
    )
    
    # En producción, no mostrar detalles del error
    if settings.is_production:
        detail = "Error interno del servidor"
    else:
        detail = str(exc)
    
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": detail,
            "error_code": "INTERNAL_SERVER_ERROR",
            "timestamp": time.time()
        }
    )


# Montar archivos estáticos
if settings.upload_path:
    app.mount(
        "/uploads", 
        StaticFiles(directory=settings.upload_path), 
        name="uploads"
    )


# Incluir rutas de la API
app.include_router(api_router, prefix="/api/v1")


# Endpoints de salud y información
@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """
    Endpoint de health check
    """
    from app.db.database import DatabaseHealth
    from app.services.gemini_service import gemini_service
    
    # Verificar base de datos
    db_health = await DatabaseHealth.check_connection()
    
    # Verificar servicio Gemini
    gemini_health = await gemini_service.health_check()
    
    # Estado general
    overall_status = "healthy"
    if db_health["status"] != "healthy" or gemini_health["status"] != "healthy":
        overall_status = "degraded"
    
    return {
        "status": overall_status,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time(),
        "services": {
            "database": db_health,
            "gemini_ai": gemini_health
        }
    }


@app.get("/info", tags=["Info"])
async def app_info() -> Dict[str, Any]:
    """
    Información de la aplicación
    """
    from app.services.gemini_service import gemini_service
    from app.services.file_service import file_service
    
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "features": {
            "facial_analysis": True,
            "chromatic_analysis": True,
            "file_upload": True,
            "user_management": True,
            "feedback_system": True
        },
        "services": {
            "gemini": gemini_service.get_service_info(),
            "file_storage": {
                "upload_dir": str(settings.upload_path),
                "max_file_size": settings.MAX_FILE_SIZE,
                "allowed_extensions": settings.ALLOWED_EXTENSIONS
            }
        },
        "api_docs": "/docs" if settings.DEBUG else None
    }


@app.get("/metrics", tags=["Metrics"])
async def metrics() -> Dict[str, Any]:
    """
    Métricas básicas de la aplicación
    """
    from app.db.database import DatabaseHealth
    from app.services.file_service import file_service
    
    # Estadísticas de base de datos
    db_stats = await DatabaseHealth.get_statistics()
    
    # Estadísticas de archivos
    storage_stats = file_service.get_storage_stats()
    
    return {
        "timestamp": time.time(),
        "database": db_stats.get("statistics", {}),
        "storage": storage_stats,
        "application": {
            "uptime_seconds": time.time() - app.state.start_time if hasattr(app.state, 'start_time') else 0,
            "environment": settings.ENVIRONMENT,
            "version": settings.APP_VERSION
        }
    }


@app.get("/", tags=["Root"])
async def root() -> Dict[str, Any]:
    """
    Endpoint raíz de la API
    """
    return {
        "message": f"Bienvenido a {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else None,
        "health": "/health",
        "api": "/api/v1"
    }


# Configurar estado inicial de la aplicación
@app.on_event("startup")
async def set_start_time():
    """Establecer tiempo de inicio de la aplicación"""
    app.state.start_time = time.time()


# Configuración adicional para desarrollo
if settings.is_development:
    @app.get("/debug/config", tags=["Debug"])
    async def debug_config():
        """Mostrar configuración (solo en desarrollo)"""
        return {
            "app_name": settings.APP_NAME,
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "database_configured": bool(settings.DATABASE_URL),
            "gemini_configured": bool(settings.GEMINI_API_KEY),
            "upload_dir": str(settings.upload_path),
            "cors_origins": settings.CORS_ORIGINS,
            "log_level": settings.LOG_LEVEL
        }
    
    @app.get("/debug/routes", tags=["Debug"])
    async def debug_routes():
        """Mostrar todas las rutas disponibles (solo en desarrollo)"""
        routes = []
        for route in app.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                routes.append({
                    "path": route.path,
                    "methods": list(route.methods),
                    "name": route.name
                })
        return {"routes": routes}
