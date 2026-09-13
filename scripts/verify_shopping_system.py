#!/usr/bin/env python3
# =============================================================================
# SYNTHIA STYLE - VERIFICACIÓN DEL SISTEMA DE SHOPPING
# =============================================================================
# Script para verificar que todas las funcionalidades de shopping están funcionando

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import get_settings
from app.services.shopping_recommendation_service import ShoppingRecommendationService
from app.services.merchant_integration_service import MerchantIntegrationService
from app.services.cache_service import CacheService
from app.services.gemini_service import GeminiService
from app.services.wardrobe_ai_service import WardrobeAIService
from app.schemas.shopping import (
    ProductSearchFilters, 
    RecommendationRequest,
    RecommendationType,
    Merchant
)

settings = get_settings()

class ShoppingSystemVerifier:
    """
    Verificador completo del sistema de shopping
    """
    
    def __init__(self):
        self.cache_service = CacheService()
        self.gemini_service = GeminiService()
        self.wardrobe_ai_service = WardrobeAIService(
            gemini_service=self.gemini_service,
            cache_service=self.cache_service
        )
        self.merchant_service = MerchantIntegrationService(self.cache_service)
        self.recommendation_service = ShoppingRecommendationService(
            gemini_service=self.gemini_service,
            cache_service=self.cache_service,
            wardrobe_ai_service=self.wardrobe_ai_service
        )
        
        self.results = []
    
    def log_result(self, test_name: str, success: bool, message: str, details: dict = None):
        """
        Registra el resultado de un test
        """
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
        
        if details and not success:
            print(f"   Detalles: {json.dumps(details, indent=2)}")
    
    async def test_configuration(self):
        """
        Verifica la configuración del sistema
        """
        try:
            # Verificar configuraciones obligatorias
            required_configs = [
                ("GEMINI_API_KEY", settings.GEMINI_API_KEY),
                ("DATABASE_URL", settings.DATABASE_URL),
                ("SECRET_KEY", settings.SECRET_KEY),
            ]
            
            missing_configs = []
            for config_name, config_value in required_configs:
                if not config_value:
                    missing_configs.append(config_name)
            
            if missing_configs:
                self.log_result(
                    "Configuración Obligatoria",
                    False,
                    f"Configuraciones faltantes: {', '.join(missing_configs)}",
                    {"missing": missing_configs}
                )
                return False
            
            # Verificar configuraciones de shopping
            shopping_configs = {
                "SHOPPING_ENABLED": settings.SHOPPING_ENABLED,
                "SHOPPING_CACHE_TTL": settings.SHOPPING_CACHE_TTL,
                "SHOPPING_MAX_RESULTS_PER_MERCHANT": settings.SHOPPING_MAX_RESULTS_PER_MERCHANT,
            }
            
            self.log_result(
                "Configuración de Shopping",
                True,
                "Configuraciones de shopping válidas",
                shopping_configs
            )
            
            # Verificar configuraciones de merchants
            merchant_configs = {}
            for merchant in Merchant:
                config_name = f"{merchant.value.upper()}_AFFILIATE_TAG"
                config_value = getattr(settings, config_name, None)
                merchant_configs[merchant.value] = bool(config_value)
            
            active_merchants = sum(merchant_configs.values())
            self.log_result(
                "Configuración de Merchants",
                active_merchants > 0,
                f"{active_merchants} merchants configurados",
                merchant_configs
            )
            
            return True
            
        except Exception as e:
            self.log_result(
                "Configuración",
                False,
                f"Error verificando configuración: {e}",
                {"error": str(e)}
            )
            return False
    
    async def test_cache_service(self):
        """
        Verifica el servicio de cache
        """
        try:
            test_key = "test_shopping_verification"
            test_value = {"timestamp": datetime.now().isoformat(), "test": True}
            
            # Test set
            await self.cache_service.set(test_key, test_value, ttl=60)
            
            # Test get
            cached_value = await self.cache_service.get(test_key)
            
            if cached_value and cached_value.get("test") == True:
                self.log_result(
                    "Servicio de Cache",
                    True,
                    "Cache funcionando correctamente"
                )
                
                # Cleanup
                await self.cache_service.delete(test_key)
                return True
            else:
                self.log_result(
                    "Servicio de Cache",
                    False,
                    "Cache no retorna valores correctos",
                    {"expected": test_value, "actual": cached_value}
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Servicio de Cache",
                False,
                f"Error en servicio de cache: {e}",
                {"error": str(e)}
            )
            return False
    
    async def test_merchant_integration(self):
        """
        Verifica la integración con merchants
        """
        try:
            # Test básico de búsqueda
            filters = ProductSearchFilters(
                query="test product",
                limit=5
            )
            
            search_result = await self.merchant_service.search_products(filters)
            
            if search_result and hasattr(search_result, 'products'):
                self.log_result(
                    "Integración con Merchants",
                    True,
                    f"Búsqueda exitosa, {search_result.total_count} productos encontrados",
                    {
                        "total_count": search_result.total_count,
                        "search_time": search_result.search_time,
                        "products_count": len(search_result.products)
                    }
                )
                return True
            else:
                self.log_result(
                    "Integración con Merchants",
                    False,
                    "Búsqueda no retornó resultados válidos",
                    {"result": str(search_result)}
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Integración con Merchants",
                False,
                f"Error en integración con merchants: {e}",
                {"error": str(e)}
            )
            return False
    
    async def test_commission_rates(self):
        """
        Verifica las tasas de comisión
        """
        try:
            commission_data = {}
            
            for merchant in Merchant:
                rate = await self.merchant_service.get_commission_rate(merchant)
                commission_data[merchant.value] = rate
                
                if not isinstance(rate, (int, float)) or rate < 0 or rate > 1:
                    self.log_result(
                        "Tasas de Comisión",
                        False,
                        f"Tasa inválida para {merchant.value}: {rate}",
                        {"merchant": merchant.value, "rate": rate}
                    )
                    return False
            
            self.log_result(
                "Tasas de Comisión",
                True,
                "Todas las tasas de comisión son válidas",
                commission_data
            )
            return True
            
        except Exception as e:
            self.log_result(
                "Tasas de Comisión",
                False,
                f"Error verificando tasas de comisión: {e}",
                {"error": str(e)}
            )
            return False
    
    async def test_affiliate_link_generation(self):
        """
        Verifica la generación de links de afiliado
        """
        try:
            from app.schemas.shopping import ProductResponse
            
            # Mock product para test
            mock_product = ProductResponse(
                id="test_product_verification",
                merchant="amazon",
                external_id="B00TEST123",
                merchant_url="https://amazon.com/dp/B00TEST123",
                name="Test Product",
                price=Decimal("29.99"),
                currency="USD",
                category="TOPS",
                colors=["black"],
                sizes=["M"],
                images=["test.jpg"],
                in_stock=True,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                last_checked=datetime.now()
            )
            
            affiliate_link = await self.merchant_service.generate_affiliate_link(
                product=mock_product,
                user_id="test_user_verification",
                tracking_params={"source": "verification"}
            )
            
            if affiliate_link and isinstance(affiliate_link, str) and "amazon.com" in affiliate_link:
                self.log_result(
                    "Generación de Links de Afiliado",
                    True,
                    "Links de afiliado generados correctamente",
                    {"link": affiliate_link[:100] + "..." if len(affiliate_link) > 100 else affiliate_link}
                )
                return True
            else:
                self.log_result(
                    "Generación de Links de Afiliado",
                    False,
                    "Link de afiliado inválido",
                    {"link": affiliate_link}
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Generación de Links de Afiliado",
                False,
                f"Error generando links de afiliado: {e}",
                {"error": str(e)}
            )
            return False
    
    async def test_recommendation_engine(self):
        """
        Verifica el motor de recomendaciones
        """
        try:
            # Mock datos del usuario
            mock_wardrobe = [
                {
                    "id": "item_1",
                    "category": "TOPS",
                    "color": "negro",
                    "style": ["CASUAL"],
                    "times_worn": 10,
                    "purchase_price": 25.0
                },
                {
                    "id": "item_2", 
                    "category": "BOTTOMS",
                    "color": "azul",
                    "style": ["CASUAL"],
                    "times_worn": 5,
                    "purchase_price": 45.0
                }
            ]
            
            mock_preferences = {
                "preferred_merchants": ["amazon"],
                "monthly_budget": 200.0,
                "enable_recommendations": True
            }
            
            recommendations = await self.recommendation_service.generate_personalized_recommendations(
                user_id="test_user_verification",
                user_wardrobe=mock_wardrobe,
                user_preferences=mock_preferences,
                request_params=RecommendationRequest(
                    recommendation_types=[RecommendationType.BASIC_ITEM],
                    max_recommendations=3
                )
            )
            
            if recommendations and len(recommendations) > 0:
                self.log_result(
                    "Motor de Recomendaciones",
                    True,
                    f"Motor generó {len(recommendations)} recomendaciones",
                    {
                        "recommendations_count": len(recommendations),
                        "types": [rec.recommendation_type.value for rec in recommendations]
                    }
                )
                return True
            else:
                self.log_result(
                    "Motor de Recomendaciones",
                    False,
                    "Motor no generó recomendaciones",
                    {"recommendations": recommendations}
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Motor de Recomendaciones",
                False,
                f"Error en motor de recomendaciones: {e}",
                {"error": str(e)}
            )
            return False
    
    async def test_data_schemas(self):
        """
        Verifica los schemas de datos
        """
        try:
            # Test ProductSearchFilters
            filters = ProductSearchFilters(
                query="test",
                min_price=Decimal("10.00"),
                max_price=Decimal("50.00"),
                limit=20
            )
            
            # Test RecommendationRequest
            rec_request = RecommendationRequest(
                recommendation_types=[RecommendationType.BASIC_ITEM],
                max_recommendations=5
            )
            
            self.log_result(
                "Schemas de Datos",
                True,
                "Todos los schemas validan correctamente",
                {
                    "filters_valid": bool(filters.query),
                    "request_valid": bool(rec_request.max_recommendations)
                }
            )
            return True
            
        except Exception as e:
            self.log_result(
                "Schemas de Datos",
                False,
                f"Error en validación de schemas: {e}",
                {"error": str(e)}
            )
            return False
    
    async def run_all_tests(self):
        """
        Ejecuta todos los tests de verificación
        """
        print("🔍 Iniciando verificación completa del sistema de shopping...")
        print("=" * 70)
        
        tests = [
            ("Configuración", self.test_configuration),
            ("Cache", self.test_cache_service),
            ("Merchant Integration", self.test_merchant_integration),
            ("Tasas de Comisión", self.test_commission_rates),
            ("Links de Afiliado", self.test_affiliate_link_generation),
            ("Motor de Recomendaciones", self.test_recommendation_engine),
            ("Schemas", self.test_data_schemas),
        ]
        
        total_tests = len(tests)
        passed_tests = 0
        
        for test_name, test_func in tests:
            try:
                success = await test_func()
                if success:
                    passed_tests += 1
            except Exception as e:
                self.log_result(
                    test_name,
                    False,
                    f"Test falló con excepción: {e}",
                    {"error": str(e)}
                )
        
        print("\n" + "=" * 70)
        print(f"📊 Resumen de Verificación:")
        print(f"   Tests ejecutados: {total_tests}")
        print(f"   Tests exitosos: {passed_tests}")
        print(f"   Tests fallidos: {total_tests - passed_tests}")
        print(f"   Porcentaje de éxito: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("🎉 ¡Todos los tests pasaron! El sistema de shopping está funcionando correctamente.")
            return True
        else:
            print("⚠️  Algunos tests fallaron. Revisar los detalles arriba.")
            return False
    
    def generate_report(self):
        """
        Genera un reporte detallado de la verificación
        """
        report = {
            "verification_timestamp": datetime.now().isoformat(),
            "system": "Synthia Style Shopping System",
            "version": "1.0.0",
            "total_tests": len(self.results),
            "passed_tests": sum(1 for r in self.results if r["success"]),
            "failed_tests": sum(1 for r in self.results if not r["success"]),
            "success_rate": (sum(1 for r in self.results if r["success"]) / len(self.results)) * 100 if self.results else 0,
            "test_results": self.results
        }
        
        # Guardar reporte
        report_path = Path(__file__).parent.parent / "verification_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Reporte detallado guardado en: {report_path}")
        return report

async def main():
    """
    Función principal de verificación
    """
    verifier = ShoppingSystemVerifier()
    
    try:
        success = await verifier.run_all_tests()
        report = verifier.generate_report()
        
        if success:
            print("\n✅ Sistema de shopping completamente funcional")
            return True
        else:
            print("\n❌ Sistema tiene problemas que requieren atención")
            return False
            
    except Exception as e:
        print(f"\n💥 Error crítico durante la verificación: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
