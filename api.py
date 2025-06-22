"""
Router principal de la API v1
Incluye todos los endpoints de la aplicación
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    facial_analysis,
    chromatic_analysis,
    feedback,
    files,
    cache
)


# Router principal de la API v1
api_router = APIRouter()

# Incluir routers de endpoints
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Autenticación"]
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Usuarios"]
)

api_router.include_router(
    facial_analysis.router,
    prefix="/facial-analysis",
    tags=["Análisis Facial"]
)

api_router.include_router(
    chromatic_analysis.router,
    prefix="/chromatic-analysis", 
    tags=["Análisis Cromático"]
)

api_router.include_router(
    feedback.router,
    prefix="/feedback",
    tags=["Feedback"]
)

api_router.include_router(
    files.router,
    prefix="/files",
    tags=["Archivos"]
)

api_router.include_router(
    cache.router,
    prefix="/cache",
    tags=["Cache & Monitoreo"]
)
