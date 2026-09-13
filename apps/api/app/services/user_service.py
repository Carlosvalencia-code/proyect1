"""
Servicio avanzado de gestión de usuarios para Synthia Style
Maneja perfiles extendidos, analytics, onboarding y suscripciones
"""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
from collections import defaultdict

from app.core.config import settings
from app.core.logging import DatabaseLogger
from app.db.database import get_db_client
from app.schemas.user import (
    SubscriptionTier, UserRole, SubscriptionFeaturesData,
    UserAnalyticsData, UserOnboardingData, OnboardingFlowResponse,
    OnboardingStepResponse, UsageLimitsResponse, DailyUsageData,
    ChurnRisk
)


class UserAnalyticsService:
    """Servicio para manejo de analytics de usuario"""
    
    @staticmethod
    async def calculate_user_analytics(user_id: str) -> UserAnalyticsData:
        """Calcular analytics completos del usuario"""
        try:
            async with get_db_client() as db:
                # Obtener datos básicos del usuario
                user = await db.user.find_unique(
                    where={"id": user_id},
                    include={
                        "facialAnalyses": True,
                        "chromaticAnalyses": True,
                        "feedbacks": True,
                        "dailyUsage": True
                    }
                )
                
                if not user:
                    raise ValueError("Usuario no encontrado")
                
                # Calcular estadísticas de análisis
                total_facial = len(user.facialAnalyses or [])
                total_chromatic = len(user.chromaticAnalyses or [])
                
                # Análisis por día de la semana
                analysis_by_day = defaultdict(int)
                analysis_by_hour = defaultdict(int)
                
                for analysis in (user.facialAnalyses or []) + (user.chromaticAnalyses or []):
                    day_name = analysis.createdAt.strftime("%A").lower()
                    hour = analysis.createdAt.hour
                    analysis_by_day[day_name] += 1
                    analysis_by_hour[hour] += 1
                
                most_frequent_day = max(analysis_by_day, key=analysis_by_day.get) if analysis_by_day else None
                most_active_hour = max(analysis_by_hour, key=analysis_by_hour.get) if analysis_by_hour else None
                
                # Calcular engagement
                feedback_count = len(user.feedbacks or [])
                
                # Calcular confianza promedio de análisis faciales
                facial_confidences = [a.confidenceLevel for a in user.facialAnalyses or [] if a.confidenceLevel]
                avg_confidence = sum(facial_confidences) / len(facial_confidences) if facial_confidences else 0
                
                # Calcular datos de los últimos 30 días
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                recent_facial = [a for a in user.facialAnalyses or [] if a.createdAt >= thirty_days_ago]
                recent_chromatic = [a for a in user.chromaticAnalyses or [] if a.createdAt >= thirty_days_ago]
                
                # Calcular tiempo total y sesiones desde uso diario
                total_time = sum(usage.timeSpentMinutes for usage in user.dailyUsage or [])
                total_sessions = sum(usage.sessionsCount for usage in user.dailyUsage or [])
                avg_session_time = total_time / total_sessions if total_sessions > 0 else 0
                
                # Calcular score de retención basado en actividad reciente
                retention_score = min(100, (len(recent_facial) + len(recent_chromatic)) * 10)
                
                # Determinar riesgo de abandono
                churn_risk = ChurnRisk.LOW
                if retention_score < 20:
                    churn_risk = ChurnRisk.HIGH
                elif retention_score < 50:
                    churn_risk = ChurnRisk.MEDIUM
                
                # Crear objeto de analytics
                analytics = UserAnalyticsData(
                    id=f"analytics_{user_id}",
                    user_id=user_id,
                    total_sessions=total_sessions,
                    total_time_spent=total_time,
                    average_session_time=avg_session_time,
                    total_facial_analyses=total_facial,
                    total_chromatic_analyses=total_chromatic,
                    most_frequent_analysis_day=most_frequent_day,
                    most_active_hour=most_active_hour,
                    feedback_given=feedback_count,
                    recommendations_shared=0,  # TODO: Implementar tracking
                    profile_views=0,  # TODO: Implementar tracking
                    preferred_analysis_type="facial" if total_facial > total_chromatic else "chromatic",
                    average_confidence_score=avg_confidence,
                    improvement_trend=0.0,  # TODO: Calcular tendencia
                    onboarding_completion=100.0 if user.onboardingCompleted else 0.0,
                    retention_score=retention_score,
                    churn_risk=churn_risk,
                    recent_analyses=len(recent_facial) + len(recent_chromatic),
                    recent_sessions=len([u for u in user.dailyUsage or [] if u.date >= thirty_days_ago.date()]),
                    recent_engagement=min(100, feedback_count * 20),
                    last_calculated=datetime.utcnow(),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                return analytics
                
        except Exception as e:
            DatabaseLogger.log_error("calculate_analytics", "user_analytics", e)
            raise
    
    @staticmethod
    async def update_user_analytics(user_id: str) -> None:
        """Actualizar analytics del usuario en la base de datos"""
        try:
            analytics = await UserAnalyticsService.calculate_user_analytics(user_id)
            
            async with get_db_client() as db:
                # Verificar si ya existe registro de analytics
                existing = await db.useranalytics.find_unique(
                    where={"userId": user_id}
                )
                
                analytics_data = analytics.dict(exclude={"id", "created_at"})
                analytics_data["userId"] = user_id
                
                if existing:
                    await db.useranalytics.update(
                        where={"userId": user_id},
                        data=analytics_data
                    )
                else:
                    await db.useranalytics.create(data=analytics_data)
                    
        except Exception as e:
            DatabaseLogger.log_error("update_analytics", "user_analytics", e)
            raise


class UserOnboardingService:
    """Servicio para manejo del onboarding de usuarios"""
    
    ONBOARDING_STEPS = [
        {
            "step": 1,
            "title": "Bienvenida",
            "description": "Conoce Synthia Style y sus funcionalidades",
            "fields_required": []
        },
        {
            "step": 2,
            "title": "Configuración del Perfil",
            "description": "Completa tu información personal",
            "fields_required": ["first_name", "skin_tone", "hair_color"]
        },
        {
            "step": 3,
            "title": "Preferencias de Estilo",
            "description": "Cuéntanos sobre tus gustos y preferencias",
            "fields_required": ["style_preferences", "favorite_colors"]
        },
        {
            "step": 4,
            "title": "Primer Análisis",
            "description": "Realiza tu primer análisis facial o cromático",
            "fields_required": []
        },
        {
            "step": 5,
            "title": "Tutorial Completado",
            "description": "¡Listo para usar Synthia Style!",
            "fields_required": []
        }
    ]
    
    @staticmethod
    async def get_onboarding_flow(user_id: str) -> OnboardingFlowResponse:
        """Obtener flujo de onboarding personalizado"""
        try:
            async with get_db_client() as db:
                # Obtener datos de onboarding
                onboarding = await db.useronboarding.find_unique(
                    where={"userId": user_id}
                )
                
                user = await db.user.find_unique(
                    where={"id": user_id},
                    include={"profile": True, "facialAnalyses": True, "chromaticAnalyses": True}
                )
                
                if not onboarding:
                    # Crear registro de onboarding si no existe
                    onboarding = await db.useronboarding.create(
                        data={
                            "userId": user_id,
                            "currentStep": 0,
                            "totalSteps": len(UserOnboardingService.ONBOARDING_STEPS),
                            "completionPercentage": 0.0
                        }
                    )
                
                # Determinar estado de cada paso
                steps = []
                for step_info in UserOnboardingService.ONBOARDING_STEPS:
                    is_completed = False
                    
                    # Lógica para determinar si el paso está completado
                    if step_info["step"] == 1:
                        is_completed = onboarding.welcomeCompleted
                    elif step_info["step"] == 2:
                        is_completed = onboarding.profileSetupCompleted or (
                            user and user.firstName and user.skinTone
                        )
                    elif step_info["step"] == 3:
                        is_completed = onboarding.preferencesSetCompleted or (
                            user and user.profile and user.profile.favoriteColors
                        )
                    elif step_info["step"] == 4:
                        is_completed = onboarding.firstAnalysisCompleted or (
                            len(user.facialAnalyses or []) > 0 or len(user.chromaticAnalyses or []) > 0
                        )
                    elif step_info["step"] == 5:
                        is_completed = onboarding.tutorialCompleted
                    
                    steps.append(OnboardingStepResponse(
                        step=step_info["step"],
                        title=step_info["title"],
                        description=step_info["description"],
                        is_completed=is_completed,
                        fields_required=step_info["fields_required"]
                    ))
                
                # Calcular porcentaje de completitud
                completed_steps = sum(1 for step in steps if step.is_completed)
                completion_percentage = (completed_steps / len(steps)) * 100
                
                # Determinar paso actual
                current_step = completed_steps + 1 if completed_steps < len(steps) else len(steps)
                
                # Determinar ruta recomendada basada en el perfil
                recommended_path = "standard"
                if user and user.subscriptionTier in [SubscriptionTier.PREMIUM, SubscriptionTier.PRO]:
                    recommended_path = "detailed"
                
                return OnboardingFlowResponse(
                    current_step=current_step,
                    total_steps=len(steps),
                    completion_percentage=completion_percentage,
                    steps=steps,
                    recommended_path=recommended_path
                )
                
        except Exception as e:
            DatabaseLogger.log_error("get_onboarding_flow", "user_onboarding", e)
            raise
    
    @staticmethod
    async def complete_onboarding_step(user_id: str, step: int) -> bool:
        """Marcar paso de onboarding como completado"""
        try:
            async with get_db_client() as db:
                onboarding = await db.useronboarding.find_unique(
                    where={"userId": user_id}
                )
                
                if not onboarding:
                    return False
                
                update_data = {"lastStepCompletedAt": datetime.utcnow()}
                
                # Marcar paso específico como completado
                if step == 1:
                    update_data["welcomeCompleted"] = True
                elif step == 2:
                    update_data["profileSetupCompleted"] = True
                elif step == 3:
                    update_data["preferencesSetCompleted"] = True
                elif step == 4:
                    update_data["firstAnalysisCompleted"] = True
                elif step == 5:
                    update_data["tutorialCompleted"] = True
                    update_data["completedAt"] = datetime.utcnow()
                    # Marcar onboarding como completado en el usuario
                    await db.user.update(
                        where={"id": user_id},
                        data={"onboardingCompleted": True}
                    )
                
                # Actualizar paso actual si es mayor
                if step > onboarding.currentStep:
                    update_data["currentStep"] = step
                
                # Recalcular porcentaje
                flow = await UserOnboardingService.get_onboarding_flow(user_id)
                update_data["completionPercentage"] = flow.completion_percentage
                
                await db.useronboarding.update(
                    where={"userId": user_id},
                    data=update_data
                )
                
                return True
                
        except Exception as e:
            DatabaseLogger.log_error("complete_onboarding_step", "user_onboarding", e)
            return False


class SubscriptionService:
    """Servicio para manejo de suscripciones y límites"""
    
    # Definir features por tier
    TIER_FEATURES = {
        SubscriptionTier.FREE: {
            "monthly_analysis_limit": 5,
            "daily_analysis_limit": 2,
            "advanced_recommendations": False,
            "export_results": False,
            "priority_support": False,
            "history_retention_days": 30,
            "max_stored_analyses": 5
        },
        SubscriptionTier.PREMIUM: {
            "monthly_analysis_limit": 25,
            "daily_analysis_limit": 5,
            "advanced_recommendations": True,
            "export_results": True,
            "priority_support": True,
            "history_retention_days": 180,
            "max_stored_analyses": 50
        },
        SubscriptionTier.PRO: {
            "monthly_analysis_limit": 100,
            "daily_analysis_limit": 10,
            "advanced_recommendations": True,
            "export_results": True,
            "priority_support": True,
            "detailed_ai_analysis": True,
            "multiple_photo_analysis": True,
            "history_retention_days": 365,
            "max_stored_analyses": 200
        },
        SubscriptionTier.ENTERPRISE: {
            "monthly_analysis_limit": -1,  # Ilimitado
            "daily_analysis_limit": -1,
            "advanced_recommendations": True,
            "export_results": True,
            "priority_support": True,
            "detailed_ai_analysis": True,
            "multiple_photo_analysis": True,
            "video_analysis": True,
            "realtime_consultation": True,
            "personal_stylist_access": True,
            "history_retention_days": -1,  # Ilimitado
            "max_stored_analyses": -1
        }
    }
    
    @staticmethod
    async def get_subscription_features(tier: SubscriptionTier) -> SubscriptionFeaturesData:
        """Obtener features disponibles para un tier"""
        features = SubscriptionService.TIER_FEATURES.get(tier, SubscriptionService.TIER_FEATURES[SubscriptionTier.FREE])
        
        return SubscriptionFeaturesData(
            tier=tier,
            **features,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @staticmethod
    async def check_usage_limits(user_id: str) -> UsageLimitsResponse:
        """Verificar límites de uso del usuario"""
        try:
            async with get_db_client() as db:
                user = await db.user.find_unique(
                    where={"id": user_id}
                )
                
                if not user:
                    raise ValueError("Usuario no encontrado")
                
                # Obtener uso diario actual
                today = date.today()
                daily_usage = await db.dailyusage.find_unique(
                    where={
                        "userId_date": {
                            "userId": user_id,
                            "date": today
                        }
                    }
                )
                
                daily_analyses_used = daily_usage.totalAnalysesCount if daily_usage else 0
                
                # Obtener features del tier actual
                features = await SubscriptionService.get_subscription_features(user.subscriptionTier)
                
                # Verificar si puede hacer más análisis
                can_analyze = True
                if features.daily_analysis_limit > 0 and daily_analyses_used >= features.daily_analysis_limit:
                    can_analyze = False
                if features.monthly_analysis_limit > 0 and user.monthlyAnalysisCount >= features.monthly_analysis_limit:
                    can_analyze = False
                
                # Calcular tiempo hasta reset diario (medianoche)
                now = datetime.now()
                tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                time_until_reset = int((tomorrow - now).total_seconds() / 60)
                
                return UsageLimitsResponse(
                    current_tier=user.subscriptionTier,
                    monthly_analyses_used=user.monthlyAnalysisCount,
                    monthly_analyses_limit=features.monthly_analysis_limit,
                    daily_analyses_used=daily_analyses_used,
                    daily_analyses_limit=features.daily_analysis_limit,
                    can_analyze=can_analyze,
                    time_until_reset=time_until_reset if not can_analyze else None
                )
                
        except Exception as e:
            DatabaseLogger.log_error("check_usage_limits", "subscription", e)
            raise
    
    @staticmethod
    async def increment_usage(user_id: str, analysis_type: str) -> bool:
        """Incrementar contador de uso del usuario"""
        try:
            async with get_db_client() as db:
                today = date.today()
                
                # Actualizar uso diario
                daily_usage = await db.dailyusage.upsert(
                    where={
                        "userId_date": {
                            "userId": user_id,
                            "date": today
                        }
                    },
                    data={
                        "create": {
                            "userId": user_id,
                            "date": today,
                            "facialAnalysesCount": 1 if analysis_type == "facial" else 0,
                            "chromaticAnalysesCount": 1 if analysis_type == "chromatic" else 0,
                            "totalAnalysesCount": 1,
                            "sessionsCount": 1
                        },
                        "update": {
                            "facialAnalysesCount": {"increment": 1} if analysis_type == "facial" else {},
                            "chromaticAnalysesCount": {"increment": 1} if analysis_type == "chromatic" else {},
                            "totalAnalysesCount": {"increment": 1}
                        }
                    }
                )
                
                # Actualizar contador mensual del usuario
                await db.user.update(
                    where={"id": user_id},
                    data={"monthlyAnalysisCount": {"increment": 1}}
                )
                
                return True
                
        except Exception as e:
            DatabaseLogger.log_error("increment_usage", "subscription", e)
            return False
    
    @staticmethod
    async def reset_monthly_usage():
        """Reset mensual de contadores (ejecutar via cron)"""
        try:
            async with get_db_client() as db:
                await db.user.update_many(
                    data={
                        "monthlyAnalysisCount": 0,
                        "lastAnalysisReset": datetime.utcnow()
                    }
                )
                
                DatabaseLogger.log_query("reset_monthly_usage", "users", affected_rows=None)
                
        except Exception as e:
            DatabaseLogger.log_error("reset_monthly_usage", "subscription", e)


class UserService:
    """Servicio principal para gestión avanzada de usuarios"""
    
    @staticmethod
    async def get_user_dashboard(user_id: str) -> Dict[str, Any]:
        """Obtener dashboard completo del usuario"""
        try:
            async with get_db_client() as db:
                # Obtener datos del usuario con todas las relaciones
                user = await db.user.find_unique(
                    where={"id": user_id},
                    include={
                        "preferences": True,
                        "profile": True,
                        "analytics": True,
                        "onboarding": True,
                        "facialAnalyses": {"take": 5, "orderBy": {"createdAt": "desc"}},
                        "chromaticAnalyses": {"take": 5, "orderBy": {"createdAt": "desc"}},
                        "feedbacks": {"take": 5, "orderBy": {"createdAt": "desc"}}
                    }
                )
                
                if not user:
                    raise ValueError("Usuario no encontrado")
                
                # Obtener features de suscripción
                subscription_features = await SubscriptionService.get_subscription_features(user.subscriptionTier)
                
                # Obtener límites de uso
                usage_limits = await SubscriptionService.check_usage_limits(user_id)
                
                # Obtener flujo de onboarding si no está completado
                onboarding_flow = None
                if not user.onboardingCompleted:
                    onboarding_flow = await UserOnboardingService.get_onboarding_flow(user_id)
                
                # Calcular analytics si no existen o están desactualizados
                if not user.analytics or (datetime.utcnow() - user.analytics.lastCalculated).days > 1:
                    await UserAnalyticsService.update_user_analytics(user_id)
                    # Recargar analytics actualizados
                    user = await db.user.find_unique(
                        where={"id": user_id},
                        include={"analytics": True}
                    )
                
                dashboard = {
                    "user": user,
                    "subscription_features": subscription_features,
                    "usage_limits": usage_limits,
                    "onboarding_flow": onboarding_flow,
                    "recent_analyses": {
                        "facial": user.facialAnalyses or [],
                        "chromatic": user.chromaticAnalyses or []
                    },
                    "recent_feedback": user.feedbacks or []
                }
                
                return dashboard
                
        except Exception as e:
            DatabaseLogger.log_error("get_user_dashboard", "users", e)
            raise
    
    @staticmethod
    async def update_user_activity(user_id: str, activity_data: Dict[str, Any]):
        """Actualizar actividad del usuario"""
        try:
            async with get_db_client() as db:
                today = date.today()
                
                # Actualizar última actividad del usuario
                await db.user.update(
                    where={"id": user_id},
                    data={"lastActive": datetime.utcnow()}
                )
                
                # Actualizar o crear registro de uso diario
                session_time = activity_data.get("session_time_minutes", 0)
                features_used = activity_data.get("features_used", [])
                
                await db.dailyusage.upsert(
                    where={
                        "userId_date": {
                            "userId": user_id,
                            "date": today
                        }
                    },
                    data={
                        "create": {
                            "userId": user_id,
                            "date": today,
                            "sessionsCount": 1,
                            "timeSpentMinutes": session_time,
                            "featuresUsed": features_used
                        },
                        "update": {
                            "sessionsCount": {"increment": 1},
                            "timeSpentMinutes": {"increment": session_time},
                            "featuresUsed": features_used  # Sobrescribir con las más recientes
                        }
                    }
                )
                
        except Exception as e:
            DatabaseLogger.log_error("update_user_activity", "users", e)


# Instancias de servicios
user_analytics_service = UserAnalyticsService()
user_onboarding_service = UserOnboardingService()
subscription_service = SubscriptionService()
user_service = UserService()
