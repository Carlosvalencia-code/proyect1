#!/usr/bin/env python3
# =============================================================================
# SYNTHIA STYLE - MIGRACIÓN DE FUNCIONALIDADES DE SHOPPING
# =============================================================================
# Script para aplicar migraciones y configurar datos iniciales para shopping

import asyncio
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from prisma import Prisma
from app.core.config import get_settings

settings = get_settings()

async def run_migrations():
    """
    Ejecuta las migraciones de Prisma para aplicar cambios de schema
    """
    print("🔄 Ejecutando migraciones de Prisma...")
    
    # Ejecutar prisma migrate deploy
    exit_code = os.system("cd /workspace/synthia-style-complete/backend && npx prisma migrate deploy")
    
    if exit_code == 0:
        print("✅ Migraciones ejecutadas exitosamente")
    else:
        print("❌ Error ejecutando migraciones")
        return False
    
    return True

async def generate_prisma_client():
    """
    Genera el cliente de Prisma actualizado
    """
    print("🔄 Generando cliente de Prisma...")
    
    # Ejecutar prisma generate
    exit_code = os.system("cd /workspace/synthia-style-complete/backend && npx prisma generate")
    
    if exit_code == 0:
        print("✅ Cliente de Prisma generado exitosamente")
    else:
        print("❌ Error generando cliente de Prisma")
        return False
    
    return True

async def seed_initial_data():
    """
    Inserta datos iniciales para funcionalidades de shopping
    """
    print("🔄 Insertando datos iniciales de shopping...")
    
    try:
        db = Prisma()
        await db.connect()
        
        # Verificar conexión
        result = await db.query_raw("SELECT 1 as test")
        print(f"✅ Conexión a base de datos verificada: {result}")
        
        # Crear datos de ejemplo si no existen
        
        # 1. Crear productos de ejemplo
        sample_products = [
            {
                "merchant": "amazon",
                "external_id": "B0SAMPLE001",
                "merchant_url": "https://amazon.com/dp/B0SAMPLE001",
                "name": "Camiseta Básica Premium",
                "description": "Camiseta de algodón 100% premium, perfecta para uso diario",
                "brand": "Example Brand",
                "price": 29.99,
                "currency": "USD",
                "category": "TOPS",
                "colors": ["negro", "blanco", "azul"],
                "sizes": ["S", "M", "L", "XL"],
                "images": ["https://via.placeholder.com/400x400?text=Camiseta+Premium"],
                "rating": 4.5,
                "review_count": 127,
                "tags": ["básico", "algodón", "premium"],
                "in_stock": True,
                "is_active": True
            },
            {
                "merchant": "asos",
                "external_id": "ASOS001",
                "merchant_url": "https://asos.com/product/ASOS001",
                "name": "Jeans Skinny Azul",
                "description": "Jeans skinny de mezclilla premium con corte moderno",
                "brand": "ASOS",
                "price": 65.00,
                "sale_price": 45.50,
                "currency": "USD",
                "category": "BOTTOMS",
                "colors": ["azul", "negro"],
                "sizes": ["26", "28", "30", "32", "34"],
                "images": ["https://via.placeholder.com/400x400?text=Jeans+ASOS"],
                "rating": 4.2,
                "review_count": 89,
                "tags": ["jeans", "skinny", "mezclilla"],
                "in_stock": True,
                "is_active": True
            }
        ]
        
        for product_data in sample_products:
            # Verificar si el producto ya existe
            existing = await db.product.find_first(
                where={
                    "merchant": product_data["merchant"],
                    "external_id": product_data["external_id"]
                }
            )
            
            if not existing:
                await db.product.create(data=product_data)
                print(f"✅ Producto creado: {product_data['name']}")
            else:
                print(f"ℹ️  Producto ya existe: {product_data['name']}")
        
        # 2. Crear preferencias de shopping por defecto
        default_shopping_preferences = {
            "preferred_merchants": ["amazon", "asos"],
            "blocked_merchants": [],
            "monthly_budget": 200.00,
            "max_item_price": 100.00,
            "budget_alerts": True,
            "enable_recommendations": True,
            "enable_price_alerts": True,
            "enable_trend_alerts": False,
            "enable_sale_alerts": True,
            "notification_frequency": "weekly",
            "max_recommendations_per_day": 5,
            "allow_affiliate_links": True,
            "share_earnings": False,
            "prefer_sustainable_brands": False,
            "prefer_local_brands": False,
            "avoid_fast_fashion": False,
            "share_shopping_data": False,
            "allow_personalization": True
        }
        
        print("✅ Datos iniciales de shopping configurados")
        
        await db.disconnect()
        
    except Exception as e:
        print(f"❌ Error insertando datos iniciales: {e}")
        return False
    
    return True

async def verify_installation():
    """
    Verifica que la instalación sea correcta
    """
    print("🔄 Verificando instalación de funcionalidades de shopping...")
    
    try:
        db = Prisma()
        await db.connect()
        
        # Verificar que las nuevas tablas existen
        tables_to_check = [
            "Product",
            "ShoppingRecommendation", 
            "WishlistItem",
            "AffiliateEarning",
            "PurchaseTracking",
            "PriceAlert",
            "MarketTrend",
            "ShoppingPreference"
        ]
        
        for table in tables_to_check:
            try:
                # Intentar consultar cada tabla
                result = await db.query_raw(f"SELECT COUNT(*) FROM \"{table}\"")
                print(f"✅ Tabla {table}: {result[0]['count']} registros")
            except Exception as e:
                print(f"❌ Error con tabla {table}: {e}")
                return False
        
        await db.disconnect()
        
    except Exception as e:
        print(f"❌ Error verificando instalación: {e}")
        return False
    
    return True

async def main():
    """
    Función principal de migración
    """
    print("🚀 Iniciando migración de funcionalidades de shopping para Synthia Style...")
    print("=" * 70)
    
    try:
        # Paso 1: Ejecutar migraciones
        if not await run_migrations():
            print("❌ Falló la ejecución de migraciones")
            return False
        
        # Paso 2: Generar cliente de Prisma
        if not await generate_prisma_client():
            print("❌ Falló la generación del cliente de Prisma")
            return False
        
        # Paso 3: Insertar datos iniciales
        if not await seed_initial_data():
            print("❌ Falló la inserción de datos iniciales")
            return False
        
        # Paso 4: Verificar instalación
        if not await verify_installation():
            print("❌ Falló la verificación de instalación")
            return False
        
        print("\n" + "=" * 70)
        print("🎉 Migración completada exitosamente!")
        print("\n📋 Funcionalidades agregadas:")
        print("   • Sistema de búsqueda de productos en múltiples merchants")
        print("   • Motor de recomendaciones inteligentes de shopping")
        print("   • Integración con APIs de afiliados")
        print("   • Sistema de wishlist con alertas de precio")
        print("   • Tracking de comisiones y earnings")
        print("   • Analytics de performance de afiliados")
        print("\n🔗 Endpoints disponibles:")
        print("   • POST /api/v1/shopping/search - Búsqueda de productos")
        print("   • POST /api/v1/shopping/recommendations - Generar recomendaciones")
        print("   • GET/POST /api/v1/shopping/wishlist - Gestionar wishlist")
        print("   • GET /api/v1/affiliates/earnings - Ver ganancias")
        print("   • POST /api/v1/affiliates/track/click - Track clicks")
        print("\n✨ La migración está completa y lista para usar!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
