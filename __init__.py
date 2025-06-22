# =============================================================================
# SYNTHIA STYLE - ENDPOINTS INITIALIZATION  
# =============================================================================
# Inicialización de todos los endpoints del API v1

# Exportar todos los routers para facilitar importación
from . import (
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

__all__ = [
    "auth",
    "users",
    "facial_analysis", 
    "chromatic_analysis",
    "feedback",
    "files",
    "cache",
    "wardrobe",
    "outfits",
    "wardrobe_analysis",
    "shopping",
    "affiliates",
    "flask_migration"
]
