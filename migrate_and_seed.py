"""
Script para migración y seeding de datos en Synthia Style
Configura las tablas iniciales y datos de prueba
"""

import asyncio
import os
import sys
import json
from datetime import datetime, timedelta

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.config import settings
from app.db.database import get_db_client
from app.core.security import get_password_hash
from app.schemas.user import SubscriptionTier, UserRole, SkinTone, HairColor, EyeColor

async def migrate_database():
    """Ejecutar migraciones de Prisma"""
    print("🔄 Ejecutando migraciones de base de datos...")
    
    # Ejecutar comando de migración
    migration_cmd = "npx prisma migrate dev --name init"
    exit_code = os.system(migration_cmd)
    
    if exit_code == 0:
        print("✅ Migraciones ejecutadas exitosamente")
    else:
        print("❌ Error ejecutando migraciones")
        return False
    
    # Generar cliente Prisma
    generate_cmd = "npx prisma generate"
    exit_code = os.system(generate_cmd)
    
    if exit_code == 0:
        print("✅ Cliente Prisma generado exitosamente")
        return True
    else:
        print("❌ Error generando cliente Prisma")
        return False


async def seed_subscription_features():
    """Crear features por tier de suscripción"""
    print("📊 Configurando features de suscripción...")
    
    try:
        async with get_db_client() as db:
            # Verificar si ya existen features
            existing = await db.subscriptionfeatures.find_first()
            if existing:
                print("⚠️  Features de suscripción ya existen, omitiendo...")
                return True
            
            # Crear features para cada tier
            features_data = [
                {
                    "tier": SubscriptionTier.FREE,
                    "monthlyAnalysisLimit": 5,
                    "dailyAnalysisLimit": 2,
                    "advancedRecommendations": False,
                    "personalizedTips": False,
                    "exportResults": False,
                    "prioritySupport": False,
                    "customReports": False,
                    "detailedAiAnalysis": False,
                    "multiplePhotoAnalysis": False,
                    "videoAnalysis": False,
                    "realTimeConsultation": False,
                    "publicProfile": False,
                    "shareResults": False,
                    "followUsers": False,
                    "historyRetentionDays": 30,
                    "maxStoredAnalyses": 5,
                    "liveChatSupport": False,
                    "phoneSupport": False,
                    "personalStylistAccess": False,
                    "monthlyPrice": 0.0,
                    "yearlyPrice": 0.0,
                    "currency": "USD",
                    "isActive": True
                },
                {
                    "tier": SubscriptionTier.PREMIUM,
                    "monthlyAnalysisLimit": 25,
                    "dailyAnalysisLimit": 5,
                    "advancedRecommendations": True,
                    "personalizedTips": True,
                    "exportResults": True,
                    "prioritySupport": True,
                    "customReports": False,
                    "detailedAiAnalysis": True,
                    "multiplePhotoAnalysis": False,
                    "videoAnalysis": False,
                    "realTimeConsultation": False,
                    "publicProfile": True,
                    "shareResults": True,
                    "followUsers": True,
                    "historyRetentionDays": 180,
                    "maxStoredAnalyses": 50,
                    "liveChatSupport": True,
                    "phoneSupport": False,
                    "personalStylistAccess": False,
                    "monthlyPrice": 9.99,
                    "yearlyPrice": 99.99,
                    "currency": "USD",
                    "isActive": True
                },
                {
                    "tier": SubscriptionTier.PRO,
                    "monthlyAnalysisLimit": 100,
                    "dailyAnalysisLimit": 10,
                    "advancedRecommendations": True,
                    "personalizedTips": True,
                    "exportResults": True,
                    "prioritySupport": True,
                    "customReports": True,
                    "detailedAiAnalysis": True,
                    "multiplePhotoAnalysis": True,
                    "videoAnalysis": False,
                    "realTimeConsultation": True,
                    "publicProfile": True,
                    "shareResults": True,
                    "followUsers": True,
                    "historyRetentionDays": 365,
                    "maxStoredAnalyses": 200,
                    "liveChatSupport": True,
                    "phoneSupport": True,
                    "personalStylistAccess": False,
                    "monthlyPrice": 29.99,
                    "yearlyPrice": 299.99,
                    "currency": "USD",
                    "isActive": True
                },
                {
                    "tier": SubscriptionTier.ENTERPRISE,
                    "monthlyAnalysisLimit": -1,  # Ilimitado
                    "dailyAnalysisLimit": -1,
                    "advancedRecommendations": True,
                    "personalizedTips": True,
                    "exportResults": True,
                    "prioritySupport": True,
                    "customReports": True,
                    "detailedAiAnalysis": True,
                    "multiplePhotoAnalysis": True,
                    "videoAnalysis": True,
                    "realTimeConsultation": True,
                    "publicProfile": True,
                    "shareResults": True,
                    "followUsers": True,
                    "historyRetentionDays": -1,  # Ilimitado
                    "maxStoredAnalyses": -1,
                    "liveChatSupport": True,
                    "phoneSupport": True,
                    "personalStylistAccess": True,
                    "monthlyPrice": 99.99,
                    "yearlyPrice": 999.99,
                    "currency": "USD",
                    "isActive": True
                }
            ]
            
            # Crear features en lote
            await db.subscriptionfeatures.create_many(data=features_data)
            
            print("✅ Features de suscripción creadas exitosamente")
            return True
            
    except Exception as e:
        print(f"❌ Error creando features de suscripción: {e}")
        return False


async def seed_admin_user():
    """Crear usuario administrador inicial"""
    print("👤 Creando usuario administrador...")
    
    try:
        async with get_db_client() as db:
            # Verificar si ya existe un admin
            existing_admin = await db.user.find_first(
                where={"role": UserRole.SUPER_ADMIN}
            )
            
            if existing_admin:
                print("⚠️  Usuario administrador ya existe, omitiendo...")
                return True
            
            # Crear usuario admin
            admin_data = {
                "email": "admin@synthiastyle.com",
                "password": get_password_hash("admin123456"),  # Cambiar en producción
                "firstName": "Super",
                "lastName": "Admin",
                "role": UserRole.SUPER_ADMIN,
                "subscriptionTier": SubscriptionTier.ENTERPRISE,
                "onboardingCompleted": True,
                "isVerified": True,
                "isActive": True
            }
            
            admin_user = await db.user.create(data=admin_data)
            
            # Crear preferencias por defecto
            await db.userpreferences.create(
                data={"userId": admin_user.id}
            )
            
            # Crear perfil extendido
            await db.userprofile.create(
                data={
                    "userId": admin_user.id,
                    "bio": "Cuenta de administrador del sistema Synthia Style",
                    "profession": "Administrador de Sistema"
                }
            )
            
            # Crear onboarding completado
            await db.useronboarding.create(
                data={
                    "userId": admin_user.id,
                    "welcomeCompleted": True,
                    "profileSetupCompleted": True,
                    "preferencesSetCompleted": True,
                    "firstAnalysisCompleted": True,
                    "tutorialCompleted": True,
                    "currentStep": 5,
                    "totalSteps": 5,
                    "completionPercentage": 100.0,
                    "completedAt": datetime.utcnow()
                }
            )
            
            print(f"✅ Usuario administrador creado: {admin_data['email']}")
            return True
            
    except Exception as e:
        print(f"❌ Error creando usuario administrador: {e}")
        return False


async def seed_demo_users():
    """Crear usuarios de demostración"""
    print("👥 Creando usuarios de demostración...")
    
    try:
        async with get_db_client() as db:
            # Verificar si ya existen usuarios demo
            existing_demo = await db.user.find_first(
                where={"email": "demo@synthiastyle.com"}
            )
            
            if existing_demo:
                print("⚠️  Usuarios demo ya existen, omitiendo...")
                return True
            
            # Crear usuarios demo
            demo_users = [
                {
                    "email": "demo@synthiastyle.com",
                    "password": get_password_hash("demo123"),
                    "firstName": "María",
                    "lastName": "González",
                    "role": UserRole.USER,
                    "subscriptionTier": SubscriptionTier.PREMIUM,
                    "skinTone": SkinTone.MEDIUM,
                    "hairColor": HairColor.BROWN,
                    "eyeColor": EyeColor.BROWN,
                    "onboardingCompleted": True,
                    "isVerified": True,
                    "isActive": True
                },
                {
                    "email": "test@synthiastyle.com",
                    "password": get_password_hash("test123"),
                    "firstName": "Ana",
                    "lastName": "Martínez",
                    "role": UserRole.USER,
                    "subscriptionTier": SubscriptionTier.FREE,
                    "skinTone": SkinTone.LIGHT,
                    "hairColor": HairColor.BLONDE,
                    "eyeColor": EyeColor.BLUE,
                    "onboardingCompleted": False,
                    "isVerified": False,
                    "isActive": True
                }
            ]
            
            for user_data in demo_users:
                user = await db.user.create(data=user_data)
                
                # Crear preferencias
                await db.userpreferences.create(
                    data={"userId": user.id}
                )
                
                # Crear perfil extendido
                await db.userprofile.create(
                    data={
                        "userId": user.id,
                        "bio": f"Usuario demo de Synthia Style - {user_data['firstName']}",
                        "favoriteColors": ["azul", "rosa", "verde"]
                    }
                )
            
            print("✅ Usuarios demo creados exitosamente")
            return True
            
    except Exception as e:
        print(f"❌ Error creando usuarios demo: {e}")
        return False


async def seed_system_config():
    """Crear configuraciones del sistema"""
    print("⚙️  Configurando parámetros del sistema...")
    
    try:
        async with get_db_client() as db:
            # Verificar si ya existe configuración
            existing = await db.systemconfig.find_first()
            if existing:
                print("⚠️  Configuración del sistema ya existe, omitiendo...")
                return True
            
            # Configuraciones del sistema
            configs = [
                {
                    "key": "app_version",
                    "value": "1.0.0",
                    "description": "Versión actual de la aplicación",
                    "category": "app",
                    "dataType": "string",
                    "isPublic": True
                },
                {
                    "key": "maintenance_mode",
                    "value": "false",
                    "description": "Modo de mantenimiento activado",
                    "category": "app",
                    "dataType": "boolean",
                    "isPublic": True
                },
                {
                    "key": "max_file_size_mb",
                    "value": "10",
                    "description": "Tamaño máximo de archivo en MB",
                    "category": "uploads",
                    "dataType": "number",
                    "isPublic": False
                },
                {
                    "key": "supported_image_formats",
                    "value": json.dumps(["jpg", "jpeg", "png", "webp"]),
                    "description": "Formatos de imagen soportados",
                    "category": "uploads",
                    "dataType": "json",
                    "isPublic": True
                },
                {
                    "key": "facial_analysis_confidence_threshold",
                    "value": "0.7",
                    "description": "Umbral de confianza para análisis facial",
                    "category": "ai",
                    "dataType": "number",
                    "isPublic": False
                },
                {
                    "key": "chromatic_analysis_confidence_threshold",
                    "value": "0.75",
                    "description": "Umbral de confianza para análisis cromático",
                    "category": "ai",
                    "dataType": "number",
                    "isPublic": False
                },
                {
                    "key": "welcome_email_enabled",
                    "value": "true",
                    "description": "Enviar email de bienvenida",
                    "category": "notifications",
                    "dataType": "boolean",
                    "isPublic": False
                },
                {
                    "key": "analytics_tracking_enabled",
                    "value": "true",
                    "description": "Tracking de analytics habilitado",
                    "category": "analytics",
                    "dataType": "boolean",
                    "isPublic": False
                }
            ]
            
            await db.systemconfig.create_many(data=configs)
            
            print("✅ Configuración del sistema creada exitosamente")
            return True
            
    except Exception as e:
        print(f"❌ Error creando configuración del sistema: {e}")
        return False


async def main():
    """Función principal del script"""
    print("🚀 Iniciando migración y seeding de Synthia Style...")
    print("=" * 60)
    
    # Ejecutar migraciones
    if not await migrate_database():
        print("❌ Falló la migración, abortando...")
        return
    
    print()
    
    # Ejecutar seeding
    success_count = 0
    total_tasks = 4
    
    tasks = [
        ("Features de suscripción", seed_subscription_features),
        ("Usuario administrador", seed_admin_user),
        ("Usuarios demo", seed_demo_users),
        ("Configuración del sistema", seed_system_config)
    ]
    
    for task_name, task_func in tasks:
        try:
            if await task_func():
                success_count += 1
        except Exception as e:
            print(f"❌ Error en {task_name}: {e}")
    
    print()
    print("=" * 60)
    print(f"📊 Resumen: {success_count}/{total_tasks} tareas completadas exitosamente")
    
    if success_count == total_tasks:
        print("🎉 ¡Migración y seeding completados exitosamente!")
        print()
        print("📋 Credenciales de acceso:")
        print("   👤 Admin: admin@synthiastyle.com / admin123456")
        print("   🎭 Demo: demo@synthiastyle.com / demo123")
        print("   🧪 Test: test@synthiastyle.com / test123")
        print()
        print("⚠️  IMPORTANTE: Cambia las contraseñas por defecto en producción")
    else:
        print("⚠️  Algunas tareas fallaron. Revisa los errores anteriores.")


if __name__ == "__main__":
    asyncio.run(main())
