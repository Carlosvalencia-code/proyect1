#!/usr/bin/env python3
"""
Script de lanzamiento para Synthia Style FastAPI
"""
import os
import sys
from pathlib import Path

# Agregar directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

if __name__ == "__main__":
    import uvicorn
    from app.core.config import get_settings
    
    settings = get_settings()
    
    print("🚀 Iniciando Synthia Style FastAPI Server...")
    print(f"   Host: {settings.HOST}")
    print(f"   Port: {settings.PORT}")
    print(f"   Environment: {settings.ENVIRONMENT}")
    print(f"   Debug: {settings.DEBUG}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )
