#!/usr/bin/env python3
"""
Script de prueba de integración para Synthia Style Backend
Verifica que todos los componentes principales funcionen correctamente
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Agregar directorio de la aplicación al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.core.config import settings
from app.services.cache_service import cache_service
from app.services.gemini_service import gemini_service
from app.core.logging import configure_logging
from app.db.database import startup_database, shutdown_database


class SynthiaTestSuite:
    """Suite de pruebas de integración para Synthia Style"""
    
    def __init__(self):
        self.test_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "tests": {},
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0
            }
        }
    
    def log_test_result(self, test_name: str, success: bool, message: str = "", error: str = ""):
        """Registrar resultado de prueba"""
        self.test_results["tests"][test_name] = {
            "success": success,
            "message": message,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.test_results["summary"]["total"] += 1
        if success:
            self.test_results["summary"]["passed"] += 1
            print(f"✅ {test_name}: {message}")
        else:
            self.test_results["summary"]["failed"] += 1
            print(f"❌ {test_name}: {error}")
    
    async def test_configuration(self):
        """Probar configuración básica"""
        try:
            # Verificar configuraciones esenciales
            assert settings.APP_NAME, "APP_NAME no configurado"
            assert settings.DATABASE_URL, "DATABASE_URL no configurado"
            assert settings.JWT_SECRET_KEY, "JWT_SECRET_KEY no configurado"
            
            self.log_test_result(
                "configuracion_basica",
                True,
                f"Configuración cargada correctamente - Entorno: {settings.ENVIRONMENT}"
            )
            
        except Exception as e:
            self.log_test_result(
                "configuracion_basica",
                False,
                error=str(e)
            )
    
    async def test_database_connection(self):
        """Probar conexión a la base de datos"""
        try:
            await startup_database()
            
            # Importar después de la inicialización
            from app.db.database import get_db_sync
            
            # Verificar conexión
            db = get_db_sync()
            if db:
                self.log_test_result(
                    "conexion_database",
                    True,
                    "Conexión a PostgreSQL establecida correctamente"
                )
            else:
                self.log_test_result(
                    "conexion_database",
                    False,
                    error="No se pudo obtener conexión a la base de datos"
                )
            
        except Exception as e:
            self.log_test_result(
                "conexion_database",
                False,
                error=f"Error conectando a PostgreSQL: {str(e)}"
            )
    
    async def test_redis_cache(self):
        """Probar conexión y funcionalidad de Redis cache"""
        try:
            # Inicializar cache service
            cache_initialized = await cache_service.initialize()
            
            if not cache_initialized:
                self.log_test_result(
                    "redis_cache",
                    False,
                    error="No se pudo inicializar Redis cache"
                )
                return
            
            # Probar operaciones básicas
            test_key = "test:integration"
            test_value = {"message": "test", "timestamp": datetime.utcnow().isoformat()}
            
            # Set
            await cache_service.set(test_key, test_value, ttl=60)
            
            # Get
            retrieved_value = await cache_service.get(test_key)
            
            if retrieved_value and retrieved_value.get("message") == "test":
                # Delete
                await cache_service.delete(test_key)
                
                self.log_test_result(
                    "redis_cache",
                    True,
                    "Redis cache funcionando correctamente (set/get/delete)"
                )
            else:
                self.log_test_result(
                    "redis_cache",
                    False,
                    error="Error en operaciones básicas de cache"
                )
                
        except Exception as e:
            self.log_test_result(
                "redis_cache",
                False,
                error=f"Error con Redis: {str(e)}"
            )
    
    async def test_gemini_service(self):
        """Probar inicialización del servicio Gemini"""
        try:
            # Verificar configuración de Gemini
            if not settings.GEMINI_API_KEY:
                self.log_test_result(
                    "gemini_service",
                    False,
                    error="GEMINI_API_KEY no configurado"
                )
                return
            
            # Probar health check
            health_status = await gemini_service.health_check()
            
            if health_status.get("status") == "healthy":
                self.log_test_result(
                    "gemini_service",
                    True,
                    f"Servicio Gemini funcionando - Respuesta: {health_status.get('response_time', 'N/A')}s"
                )
            else:
                self.log_test_result(
                    "gemini_service",
                    False,
                    error=f"Gemini health check falló: {health_status.get('message', 'Error desconocido')}"
                )
                
        except Exception as e:
            self.log_test_result(
                "gemini_service",
                False,
                error=f"Error inicializando Gemini: {str(e)}"
            )
    
    async def test_cache_integration(self):
        """Probar integración del cache con servicios"""
        try:
            if not cache_service.redis:
                self.log_test_result(
                    "cache_integration",
                    False,
                    error="Redis no disponible para prueba de integración"
                )
                return
            
            # Probar hash de imagen
            test_image_data = "dGVzdCBpbWFnZSBkYXRh"  # "test image data" en base64
            image_hash = await cache_service.create_image_hash(test_image_data)
            
            if image_hash and len(image_hash) > 0:
                # Probar cache de análisis
                test_analysis = {
                    "forma_rostro": "ovalado",
                    "confianza_analisis": 85,
                    "caracteristicas_destacadas": ["ojos expresivos", "pómulos definidos"]
                }
                
                # Guardar en cache
                await cache_service.set_analysis_cache(image_hash, "facial", test_analysis)
                
                # Recuperar del cache
                cached_analysis = await cache_service.get_analysis_cache(image_hash, "facial")
                
                if cached_analysis:
                    self.log_test_result(
                        "cache_integration",
                        True,
                        "Integración de cache con análisis funcionando correctamente"
                    )
                else:
                    self.log_test_result(
                        "cache_integration",
                        False,
                        error="No se pudo recuperar análisis del cache"
                    )
            else:
                self.log_test_result(
                    "cache_integration",
                    False,
                    error="No se pudo generar hash de imagen"
                )
                
        except Exception as e:
            self.log_test_result(
                "cache_integration",
                False,
                error=f"Error en integración de cache: {str(e)}"
            )
    
    async def test_logging_system(self):
        """Probar sistema de logging"""
        try:
            # Configurar logging
            configure_logging()
            
            # Probar logging básico
            from app.core.logging import AILogger, RequestLogger
            
            # Test AI Logger
            AILogger.log_analysis_request(
                user_id="test_user",
                analysis_type="test",
                metadata={"test": True}
            )
            
            self.log_test_result(
                "logging_system",
                True,
                "Sistema de logging funcionando correctamente"
            )
            
        except Exception as e:
            self.log_test_result(
                "logging_system",
                False,
                error=f"Error en sistema de logging: {str(e)}"
            )
    
    async def run_all_tests(self):
        """Ejecutar todas las pruebas"""
        print("🚀 Iniciando suite de pruebas de integración para Synthia Style\n")
        
        tests = [
            self.test_configuration,
            self.test_database_connection,
            self.test_redis_cache,
            self.test_gemini_service,
            self.test_cache_integration,
            self.test_logging_system
        ]
        
        for test in tests:
            try:
                await test()
            except Exception as e:
                test_name = test.__name__.replace('test_', '')
                self.log_test_result(
                    test_name,
                    False,
                    error=f"Excepción no manejada: {str(e)}"
                )
        
        # Cleanup
        try:
            await cache_service.close()
            await shutdown_database()
        except Exception as e:
            print(f"⚠️  Error durante cleanup: {str(e)}")
        
        # Mostrar resumen
        summary = self.test_results["summary"]
        print(f"\n📊 Resumen de Pruebas:")
        print(f"   Total: {summary['total']}")
        print(f"   Exitosas: {summary['passed']} ✅")
        print(f"   Fallidas: {summary['failed']} ❌")
        
        success_rate = (summary['passed'] / summary['total']) * 100 if summary['total'] > 0 else 0
        print(f"   Tasa de éxito: {success_rate:.1f}%")
        
        # Guardar resultados
        with open("test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n📄 Resultados detallados guardados en: test_results.json")
        
        return summary['failed'] == 0


async def main():
    """Función principal"""
    test_suite = SynthiaTestSuite()
    success = await test_suite.run_all_tests()
    
    if success:
        print("\n🎉 ¡Todas las pruebas pasaron exitosamente!")
        sys.exit(0)
    else:
        print("\n💥 Algunas pruebas fallaron. Revisa los detalles arriba.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
