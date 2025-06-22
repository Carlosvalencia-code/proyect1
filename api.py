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
    cache,
    wardrobe,
    outfits,
    wardrobe_analysis,
    shopping,
    affiliates,
    flask_migration
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

# Nuevos routers del armario virtual
api_router.include_router(
    wardrobe.router,
    tags=["Armario Virtual"]
)

api_router.include_router(
    outfits.router,
    tags=["Outfits"]
)

api_router.include_router(
    wardrobe_analysis.router,
    tags=["Análisis de Armario"]
)

# Nuevos routers de shopping y afiliados
api_router.include_router(
    shopping.router,
    prefix="/shopping",
    tags=["Shopping & Recomendaciones"]
)

api_router.include_router(
    affiliates.router,
    prefix="/affiliates",
    tags=["Afiliados & Comisiones"]
)

# Router de migración de Flask (compatibilidad)
api_router.include_router(
    flask_migration.router,
    prefix="/flask",
    tags=["Migración Flask (Compatibilidad)"]
)
