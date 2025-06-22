"""
Configuración de logging estructurado para Synthia Style
Utiliza loguru y structlog para logging avanzado
"""

import os
import sys
import json
from typing import Any, Dict
from datetime import datetime

import structlog
from loguru import logger
from fastapi import Request

from app.core.config import settings


def configure_logging():
    """
    Configurar el sistema de logging de la aplicación
    """
    # Configurar loguru
    logger.remove()  # Remover handler por defecto
    
    # Crear directorio de logs si no existe
    log_dir = os.path.dirname(settings.log_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Formato para desarrollo
    if settings.is_development:
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                   "<level>{message}</level>",
            level=settings.LOG_LEVEL,
            colorize=True
        )
    
    # Handler para archivo (siempre activo)
    logger.add(
        settings.log_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level=settings.LOG_LEVEL,
        rotation="10 MB",
        retention="7 days",
        compression="gz",
        serialize=settings.LOG_FORMAT == "json"
    )
    
    # Configurar structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.LOG_FORMAT == "json" 
            else structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )


class RequestLogger:
    """Logger especializado para requests HTTP"""
    
    @staticmethod
    def log_request(request: Request, response_time: float = None, status_code: int = None):
        """Log de request HTTP"""
        log_data = {
            "event": "http_request",
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if response_time is not None:
            log_data["response_time_ms"] = round(response_time * 1000, 2)
        
        if status_code is not None:
            log_data["status_code"] = status_code
        
        # Determinar nivel de log basado en status code
        if status_code:
            if status_code >= 500:
                logger.error("HTTP Request", **log_data)
            elif status_code >= 400:
                logger.warning("HTTP Request", **log_data)
            else:
                logger.info("HTTP Request", **log_data)
        else:
            logger.info("HTTP Request", **log_data)
    
    @staticmethod
    def log_error(request: Request, error: Exception, status_code: int = 500):
        """Log de error en request"""
        log_data = {
            "event": "http_error",
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else None,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "status_code": status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.error("HTTP Error", **log_data)


class AILogger:
    """Logger especializado para operaciones de IA"""
    
    @staticmethod
    def log_analysis_request(user_id: str, analysis_type: str, metadata: Dict[str, Any] = None):
        """Log de solicitud de análisis de IA"""
        log_data = {
            "event": "ai_analysis_request",
            "user_id": user_id,
            "analysis_type": analysis_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if metadata:
            log_data["metadata"] = metadata
        
        logger.info("AI Analysis Request", **log_data)
    
    @staticmethod
    def log_analysis_response(
        user_id: str, 
        analysis_type: str, 
        success: bool, 
        response_time: float,
        confidence: int = None,
        error: str = None
    ):
        """Log de respuesta de análisis de IA"""
        log_data = {
            "event": "ai_analysis_response",
            "user_id": user_id,
            "analysis_type": analysis_type,
            "success": success,
            "response_time_ms": round(response_time * 1000, 2),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if confidence is not None:
            log_data["confidence"] = confidence
        
        if error:
            log_data["error"] = error
        
        if success:
            logger.info("AI Analysis Success", **log_data)
        else:
            logger.error("AI Analysis Failed", **log_data)


class DatabaseLogger:
    """Logger especializado para operaciones de base de datos"""
    
    @staticmethod
    def log_query(operation: str, table: str, duration: float = None, affected_rows: int = None):
        """Log de operación de base de datos"""
        log_data = {
            "event": "database_operation",
            "operation": operation,
            "table": table,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if duration is not None:
            log_data["duration_ms"] = round(duration * 1000, 2)
        
        if affected_rows is not None:
            log_data["affected_rows"] = affected_rows
        
        logger.debug("Database Operation", **log_data)
    
    @staticmethod
    def log_error(operation: str, table: str, error: Exception):
        """Log de error de base de datos"""
        log_data = {
            "event": "database_error",
            "operation": operation,
            "table": table,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.error("Database Error", **log_data)


class SecurityLogger:
    """Logger especializado para eventos de seguridad"""
    
    @staticmethod
    def log_authentication(user_id: str, success: bool, ip_address: str = None, user_agent: str = None):
        """Log de intento de autenticación"""
        log_data = {
            "event": "authentication_attempt",
            "user_id": user_id,
            "success": success,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if success:
            logger.info("Authentication Success", **log_data)
        else:
            logger.warning("Authentication Failed", **log_data)
    
    @staticmethod
    def log_authorization(user_id: str, resource: str, action: str, success: bool):
        """Log de intento de autorización"""
        log_data = {
            "event": "authorization_attempt",
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if success:
            logger.debug("Authorization Success", **log_data)
        else:
            logger.warning("Authorization Failed", **log_data)


# Funciones de utilidad para logging
def get_logger(name: str):
    """Obtener logger con contexto"""
    return structlog.get_logger(name)


def log_startup_info():
    """Log información de inicio de la aplicación"""
    logger.info(
        "Application Starting",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        debug=settings.DEBUG,
        host=settings.HOST,
        port=settings.PORT
    )


def log_shutdown_info():
    """Log información de cierre de la aplicación"""
    logger.info(
        "Application Shutting Down",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow().isoformat()
    )


# Inicializar logging al importar el módulo
configure_logging()
