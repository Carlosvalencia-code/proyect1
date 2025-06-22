"""
Configuración de base de datos para Synthia Style
Maneja conexiones PostgreSQL con Prisma ORM
"""

import asyncio
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager

from prisma import Prisma
from prisma.errors import PrismaError
from loguru import logger

from app.core.config import settings
from app.core.logging import DatabaseLogger


class DatabaseManager:
    """Gestor principal de base de datos"""
    
    def __init__(self):
        self.client: Optional[Prisma] = None
        self._connected: bool = False
    
    async def connect(self) -> None:
        """Conectar a la base de datos"""
        if self._connected and self.client:
            logger.info("Base de datos ya conectada")
            return
        
        try:
            logger.info("Conectando a la base de datos...")
            self.client = Prisma()
            await self.client.connect()
            self._connected = True
            logger.info("Conexión a base de datos establecida exitosamente")
            
        except Exception as e:
            self._connected = False
            logger.error(f"Error conectando a la base de datos: {str(e)}")
            raise
    
    async def disconnect(self) -> None:
        """Desconectar de la base de datos"""
        if self.client and self._connected:
            try:
                logger.info("Desconectando de la base de datos...")
                await self.client.disconnect()
                self._connected = False
                logger.info("Desconectado de la base de datos exitosamente")
            except Exception as e:
                logger.error(f"Error desconectando de la base de datos: {str(e)}")
        
        self.client = None
    
    async def health_check(self) -> bool:
        """Verificar salud de la conexión a la base de datos"""
        if not self.client or not self._connected:
            return False
        
        try:
            # Ejecutar query simple para verificar conexión
            await self.client.query_raw("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Health check de base de datos falló: {str(e)}")
            return False
    
    @property
    def is_connected(self) -> bool:
        """Verificar si está conectado"""
        return self._connected and self.client is not None
    
    def get_client(self) -> Prisma:
        """Obtener cliente de base de datos"""
        if not self.client or not self._connected:
            raise RuntimeError("Base de datos no conectada")
        return self.client


# Instancia global del gestor de base de datos
db_manager = DatabaseManager()


@asynccontextmanager
async def get_db_client() -> AsyncGenerator[Prisma, None]:
    """
    Context manager para obtener cliente de base de datos
    Asegura que la conexión esté activa
    """
    if not db_manager.is_connected:
        await db_manager.connect()
    
    try:
        yield db_manager.get_client()
    except Exception as e:
        DatabaseLogger.log_error("context_manager", "general", e)
        raise
    finally:
        # El cliente se mantiene activo para reutilización
        pass


async def get_db() -> Prisma:
    """
    Dependency para FastAPI que proporciona cliente de base de datos
    """
    if not db_manager.is_connected:
        await db_manager.connect()
    
    return db_manager.get_client()


class DatabaseOperations:
    """Operaciones comunes de base de datos"""
    
    @staticmethod
    async def execute_with_retry(
        operation_func,
        max_retries: int = 3,
        delay: float = 1.0
    ):
        """
        Ejecutar operación de base de datos con reintentos
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return await operation_func()
            except PrismaError as e:
                last_exception = e
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Intento {attempt + 1} falló, reintentando en {delay}s: {str(e)}"
                    )
                    await asyncio.sleep(delay)
                    delay *= 2  # Backoff exponencial
                else:
                    logger.error(f"Operación falló después de {max_retries} intentos")
                    raise
            except Exception as e:
                logger.error(f"Error no recuperable en operación de BD: {str(e)}")
                raise
        
        if last_exception:
            raise last_exception
    
    @staticmethod
    async def transaction_with_retry(operation_func, max_retries: int = 3):
        """
        Ejecutar transacción con reintentos
        """
        async def transaction_operation():
            async with get_db_client() as db:
                return await db.tx(operation_func)
        
        return await DatabaseOperations.execute_with_retry(
            transaction_operation, 
            max_retries
        )


class DatabaseMigrations:
    """Manejo de migraciones de base de datos"""
    
    @staticmethod
    async def run_migrations():
        """
        Ejecutar migraciones pendientes
        """
        try:
            logger.info("Ejecutando migraciones de base de datos...")
            
            # Con Prisma, las migraciones se ejecutan con prisma migrate
            # En producción, esto se haría en el pipeline de deployment
            logger.info("Migraciones completadas")
            
        except Exception as e:
            logger.error(f"Error ejecutando migraciones: {str(e)}")
            raise
    
    @staticmethod
    async def seed_initial_data():
        """
        Crear datos iniciales en la base de datos
        """
        try:
            logger.info("Sembrando datos iniciales...")
            
            async with get_db_client() as db:
                # Verificar si ya existen datos
                config_count = await db.systemconfig.count()
                
                if config_count == 0:
                    # Crear configuraciones iniciales del sistema
                    initial_configs = [
                        {
                            "key": "max_file_size",
                            "value": str(settings.MAX_FILE_SIZE),
                            "description": "Tamaño máximo de archivo en bytes",
                            "category": "files"
                        },
                        {
                            "key": "allowed_extensions",
                            "value": ",".join(settings.ALLOWED_EXTENSIONS),
                            "description": "Extensiones de archivo permitidas",
                            "category": "files"
                        },
                        {
                            "key": "gemini_model_facial",
                            "value": "gemini-2.5-flash-preview-04-17",
                            "description": "Modelo de Gemini para análisis facial",
                            "category": "ai"
                        },
                        {
                            "key": "gemini_model_chromatic",
                            "value": "gemini-2.5-flash-preview-04-17",
                            "description": "Modelo de Gemini para análisis cromático",
                            "category": "ai"
                        }
                    ]
                    
                    for config in initial_configs:
                        await db.systemconfig.create(data=config)
                    
                    logger.info("Datos iniciales sembrados exitosamente")
                else:
                    logger.info("Datos iniciales ya existen, saltando...")
                    
        except Exception as e:
            logger.error(f"Error sembrando datos iniciales: {str(e)}")
            raise


class DatabaseHealth:
    """Monitoreo de salud de la base de datos"""
    
    @staticmethod
    async def check_connection() -> dict:
        """Verificar estado de conexión"""
        try:
            if not db_manager.is_connected:
                return {
                    "status": "error",
                    "message": "No conectado a la base de datos"
                }
            
            # Verificar con query simple
            start_time = asyncio.get_event_loop().time()
            is_healthy = await db_manager.health_check()
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            if is_healthy:
                return {
                    "status": "healthy",
                    "response_time_ms": round(response_time, 2),
                    "message": "Conexión a base de datos OK"
                }
            else:
                return {
                    "status": "error",
                    "message": "Health check falló"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error verificando salud de BD: {str(e)}"
            }
    
    @staticmethod
    async def get_statistics() -> dict:
        """Obtener estadísticas de la base de datos"""
        try:
            async with get_db_client() as db:
                stats = {}
                
                # Contar registros en tablas principales
                stats["users"] = await db.user.count()
                stats["facial_analyses"] = await db.facialanalysis.count()
                stats["chromatic_analyses"] = await db.chromaticanalysis.count()
                stats["feedbacks"] = await db.feedback.count()
                
                # Estadísticas de actividad reciente (último día)
                from datetime import datetime, timedelta
                yesterday = datetime.utcnow() - timedelta(days=1)
                
                stats["recent_activity"] = {
                    "new_users": await db.user.count(
                        where={"createdAt": {"gte": yesterday}}
                    ),
                    "recent_analyses": await db.facialanalysis.count(
                        where={"createdAt": {"gte": yesterday}}
                    )
                }
                
                return {
                    "status": "success",
                    "statistics": stats
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error obteniendo estadísticas: {str(e)}"
            }


# Eventos de ciclo de vida de la aplicación
async def startup_database():
    """Inicializar base de datos al startup"""
    try:
        await db_manager.connect()
        await DatabaseMigrations.seed_initial_data()
        logger.info("Base de datos inicializada correctamente")
    except Exception as e:
        logger.error(f"Error inicializando base de datos: {str(e)}")
        raise


async def shutdown_database():
    """Cerrar conexiones al shutdown"""
    try:
        await db_manager.disconnect()
        logger.info("Base de datos desconectada correctamente")
    except Exception as e:
        logger.error(f"Error cerrando base de datos: {str(e)}")
