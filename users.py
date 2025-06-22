"""
Endpoints avanzados de usuarios para Synthia Style API
Gestión completa de perfiles, analytics, onboarding y suscripciones
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body

from app.schemas.user import (
    UserUpdate, UserResponse, UserPreferencesUpdate, UserProfile,
    UserExtended, UserProfileExtended, UserPreferencesExtended,
    UserAnalyticsData, UserOnboardingData, OnboardingFlowResponse,
    SubscriptionFeaturesData, UsageLimitsResponse, UserDashboard,
    UserProfileUpdate, UserAdvancedUpdate, SubscriptionUpgrade,
    OnboardingStepResponse, SubscriptionTier, UserRole
)
from app.schemas.common import APIResponse, PaginationParams, PaginatedResponse
from app.core.security import get_current_user_id
from app.db.database import get_db
from app.services.user_service import (
    user_service, user_analytics_service, user_onboarding_service,
    subscription_service
)

router = APIRouter()


# ============= ENDPOINTS DE PERFIL BÁSICO =============

@router.get("/profile", response_model=UserProfile)
async def get_user_profile(
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
) -> UserProfile:
    """
    Obtener perfil completo del usuario (endpoint original preservado)
    """
    try:
        user = await db.user.find_unique(
            where={"id": current_user_id},
            include={"preferences": True}
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Obtener estadísticas
        facial_analyses_count = await db.facialanalysis.count(
            where={"userId": current_user_id}
        )
        
        chromatic_analyses_count = await db.chromaticanalysis.count(
            where={"userId": current_user_id}
        )
        
        # Última fecha de análisis
        last_analysis = await db.facialanalysis.find_first(
            where={"userId": current_user_id},
            order={"createdAt": "desc"}
        )
        
        last_analysis_date = last_analysis.createdAt if last_analysis else None
        
        from app.schemas.user import UserStats
        stats = UserStats(
            total_facial_analyses=facial_analyses_count,
            total_chromatic_analyses=chromatic_analyses_count,
            last_analysis_date=last_analysis_date
        )
        
        return UserProfile(
            id=user.id,
            email=user.email,
            first_name=user.firstName,
            last_name=user.lastName,
            is_active=user.isActive,
            created_at=user.createdAt,
            updated_at=user.updatedAt,
            preferences=user.preferences,
            stats=stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo perfil: {str(e)}"
        )


# ============= ENDPOINTS AVANZADOS =============

@router.get("/dashboard", response_model=APIResponse)
async def get_user_dashboard(
    current_user_id: str = Depends(get_current_user_id)
) -> APIResponse:
    """
    Obtener dashboard completo del usuario con analytics y métricas
    """
    try:
        dashboard = await user_service.get_user_dashboard(current_user_id)
        
        return APIResponse(
            message="Dashboard obtenido exitosamente",
            data=dashboard
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo dashboard: {str(e)}"
        )


@router.get("/profile/extended", response_model=UserProfileExtended)
async def get_extended_profile(
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
) -> UserProfileExtended:
    """
    Obtener perfil extendido del usuario
    """
    try:
        profile = await db.userprofile.find_unique(
            where={"userId": current_user_id}
        )
        
        if not profile:
            # Crear perfil extendido vacío si no existe
            profile = await db.userprofile.create(
                data={"userId": current_user_id}
            )
        
        return UserProfileExtended(
            id=profile.id,
            user_id=profile.userId,
            bio=profile.bio,
            website=profile.website,
            profession=profile.profession,
            interests=profile.interests or [],
            style_preferences=profile.stylePreferences,
            favorite_colors=profile.favoriteColors or [],
            fashion_goals=profile.fashionGoals or [],
            budget_range=profile.budgetRange,
            height=profile.height,
            weight=profile.weight,
            body_type=profile.bodyType,
            instagram_handle=profile.instagramHandle,
            tiktok_handle=profile.tiktokHandle,
            linkedin_profile=profile.linkedinProfile,
            allow_public_profile=profile.allowPublicProfile,
            show_stats_publicly=profile.showStatsPublicly,
            show_recommendations_publicly=profile.showRecommendationsPublicly,
            created_at=profile.createdAt,
            updated_at=profile.updatedAt
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo perfil extendido: {str(e)}"
        )


@router.put("/profile/extended", response_model=UserProfileExtended)
async def update_extended_profile(
    profile_update: UserProfileUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
) -> UserProfileExtended:
    """
    Actualizar perfil extendido del usuario
    """
    try:
        # Preparar datos de actualización
        update_data = {}
        for field, value in profile_update.dict(exclude_unset=True).items():
            if value is not None:
                # Convertir nombres de campos de snake_case a camelCase para Prisma
                prisma_field = {
                    "instagram_handle": "instagramHandle",
                    "tiktok_handle": "tiktokHandle", 
                    "linkedin_profile": "linkedinProfile",
                    "favorite_colors": "favoriteColors",
                    "fashion_goals": "fashionGoals",
                    "budget_range": "budgetRange",
                    "body_type": "bodyType",
                    "allow_public_profile": "allowPublicProfile",
                    "show_stats_publicly": "showStatsPublicly",
                    "show_recommendations_publicly": "showRecommendationsPublicly",
                    "style_preferences": "stylePreferences"
                }.get(field, field)
                
                update_data[prisma_field] = value
        
        # Actualizar o crear perfil
        profile = await db.userprofile.upsert(
            where={"userId": current_user_id},
            data={
                "create": {
                    "userId": current_user_id,
                    **update_data
                },
                "update": update_data
            }
        )
        
        return UserProfileExtended(
            id=profile.id,
            user_id=profile.userId,
            bio=profile.bio,
            website=profile.website,
            profession=profile.profession,
            interests=profile.interests or [],
            style_preferences=profile.stylePreferences,
            favorite_colors=profile.favoriteColors or [],
            fashion_goals=profile.fashionGoals or [],
            budget_range=profile.budgetRange,
            height=profile.height,
            weight=profile.weight,
            body_type=profile.bodyType,
            instagram_handle=profile.instagramHandle,
            tiktok_handle=profile.tiktokHandle,
            linkedin_profile=profile.linkedinProfile,
            allow_public_profile=profile.allowPublicProfile,
            show_stats_publicly=profile.showStatsPublicly,
            show_recommendations_publicly=profile.showRecommendationsPublicly,
            created_at=profile.createdAt,
            updated_at=profile.updatedAt
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error actualizando perfil extendido: {str(e)}"
        )


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
) -> UserResponse:
    """
    Actualizar perfil de usuario
    """
    try:
        # Construir datos de actualización
        update_data = {}
        if user_update.first_name is not None:
            update_data["firstName"] = user_update.first_name
        if user_update.last_name is not None:
            update_data["lastName"] = user_update.last_name
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay datos para actualizar"
            )
        
        # Actualizar usuario
        updated_user = await db.user.update(
            where={"id": current_user_id},
            data=update_data,
            include={"preferences": True}
        )
        
        return UserResponse(
            id=updated_user.id,
            email=updated_user.email,
            first_name=updated_user.firstName,
            last_name=updated_user.lastName,
            is_active=updated_user.isActive,
            created_at=updated_user.createdAt,
            updated_at=updated_user.updatedAt,
            preferences=updated_user.preferences
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error actualizando perfil: {str(e)}"
        )


# ============= ENDPOINTS DE ANALYTICS =============

@router.get("/analytics", response_model=UserAnalyticsData)
async def get_user_analytics(
    current_user_id: str = Depends(get_current_user_id),
    force_recalculate: bool = Query(default=False, description="Forzar recálculo de analytics")
) -> UserAnalyticsData:
    """
    Obtener analytics del usuario
    """
    try:
        if force_recalculate:
            await user_analytics_service.update_user_analytics(current_user_id)
        
        analytics = await user_analytics_service.calculate_user_analytics(current_user_id)
        return analytics
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo analytics: {str(e)}"
        )


@router.post("/analytics/refresh", response_model=APIResponse)
async def refresh_user_analytics(
    current_user_id: str = Depends(get_current_user_id)
) -> APIResponse:
    """
    Refrescar analytics del usuario
    """
    try:
        await user_analytics_service.update_user_analytics(current_user_id)
        
        return APIResponse(message="Analytics actualizados exitosamente")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error actualizando analytics: {str(e)}"
        )


# ============= ENDPOINTS DE ONBOARDING =============

@router.get("/onboarding", response_model=OnboardingFlowResponse)
async def get_onboarding_flow(
    current_user_id: str = Depends(get_current_user_id)
) -> OnboardingFlowResponse:
    """
    Obtener flujo de onboarding personalizado
    """
    try:
        flow = await user_onboarding_service.get_onboarding_flow(current_user_id)
        return flow
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo onboarding: {str(e)}"
        )


@router.post("/onboarding/step/{step}", response_model=APIResponse)
async def complete_onboarding_step(
    step: int,
    current_user_id: str = Depends(get_current_user_id)
) -> APIResponse:
    """
    Marcar paso de onboarding como completado
    """
    try:
        if step < 1 or step > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El paso debe estar entre 1 y 5"
            )
        
        success = await user_onboarding_service.complete_onboarding_step(current_user_id, step)
        
        if success:
            return APIResponse(message=f"Paso {step} de onboarding completado")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo completar el paso de onboarding"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error completando onboarding: {str(e)}"
        )


# ============= ENDPOINTS DE SUSCRIPCIONES =============

@router.get("/subscription/features", response_model=SubscriptionFeaturesData)
async def get_subscription_features(
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
) -> SubscriptionFeaturesData:
    """
    Obtener features disponibles para la suscripción actual
    """
    try:
        user = await db.user.find_unique(where={"id": current_user_id})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        features = await subscription_service.get_subscription_features(user.subscriptionTier)
        return features
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo features: {str(e)}"
        )


@router.get("/subscription/usage", response_model=UsageLimitsResponse)
async def get_usage_limits(
    current_user_id: str = Depends(get_current_user_id)
) -> UsageLimitsResponse:
    """
    Obtener límites de uso y consumo actual
    """
    try:
        limits = await subscription_service.check_usage_limits(current_user_id)
        return limits
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo límites: {str(e)}"
        )


@router.post("/subscription/upgrade", response_model=APIResponse)
async def upgrade_subscription(
    upgrade_data: SubscriptionUpgrade,
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
) -> APIResponse:
    """
    Solicitar upgrade de suscripción
    """
    try:
        user = await db.user.find_unique(where={"id": current_user_id})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Verificar que el upgrade sea válido
        tier_hierarchy = {
            SubscriptionTier.FREE: 0,
            SubscriptionTier.PREMIUM: 1,
            SubscriptionTier.PRO: 2,
            SubscriptionTier.ENTERPRISE: 3
        }
        
        current_level = tier_hierarchy.get(user.subscriptionTier, 0)
        target_level = tier_hierarchy.get(upgrade_data.target_tier, 0)
        
        if target_level <= current_level:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El tier objetivo debe ser superior al actual"
            )
        
        # TODO: Integrar con sistema de pagos
        # Por ahora, simular upgrade exitoso
        
        # Actualizar tier del usuario
        expiry_date = datetime.utcnow() + timedelta(days=30 if upgrade_data.billing_cycle == "monthly" else 365)
        
        await db.user.update(
            where={"id": current_user_id},
            data={
                "subscriptionTier": upgrade_data.target_tier,
                "subscriptionExpiry": expiry_date
            }
        )
        
        # Crear registro en historial
        await db.subscriptionhistory.create(
            data={
                "userId": current_user_id,
                "tier": upgrade_data.target_tier,
                "startDate": datetime.utcnow(),
                "endDate": expiry_date,
                "changeReason": "upgrade",
                "previousTier": user.subscriptionTier,
                "paymentMethod": upgrade_data.payment_method
            }
        )
        
        return APIResponse(
            message=f"Suscripción actualizada a {upgrade_data.target_tier.value} exitosamente"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error actualizando suscripción: {str(e)}"
        )


# ============= ENDPOINTS DE PREFERENCIAS EXTENDIDAS =============

@router.get("/preferences/extended", response_model=UserPreferencesExtended)
async def get_extended_preferences(
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
) -> UserPreferencesExtended:
    """
    Obtener preferencias extendidas del usuario
    """
    try:
        preferences = await db.userpreferences.find_unique(
            where={"userId": current_user_id}
        )
        
        if not preferences:
            # Crear preferencias por defecto
            preferences = await db.userpreferences.create(
                data={"userId": current_user_id}
            )
        
        return UserPreferencesExtended(
            id=preferences.id,
            user_id=preferences.userId,
            email_notifications=preferences.emailNotifications,
            push_notifications=preferences.pushNotifications,
            marketing_emails=preferences.marketingEmails,
            analysis_reminders=preferences.analysisReminders,
            weekly_digest=preferences.weeklyDigest,
            share_analytics=preferences.shareAnalytics,
            profile_visibility=preferences.profileVisibility,
            show_analysis_history=preferences.showAnalysisHistory,
            allow_data_export=preferences.allowDataExport,
            data_retention_days=preferences.dataRetentionDays,
            auto_save_results=preferences.autoSaveResults,
            detailed_recommendations=preferences.detailedRecommendations,
            include_confidence_score=preferences.includeConfidenceScore,
            preferred_language=preferences.preferredLanguage,
            theme=preferences.theme,
            currency=preferences.currency,
            timezone=preferences.timezone,
            created_at=preferences.createdAt,
            updated_at=preferences.updatedAt
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo preferencias: {str(e)}"
        )


@router.put("/preferences", response_model=APIResponse)
async def update_user_preferences(
    preferences_update: UserPreferencesUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
) -> APIResponse:
    """
    Actualizar preferencias del usuario (endpoint original mejorado)
    """
    try:
        # Construir datos de actualización
        update_data = {}
        if preferences_update.email_notifications is not None:
            update_data["emailNotifications"] = preferences_update.email_notifications
        if preferences_update.push_notifications is not None:
            update_data["pushNotifications"] = preferences_update.push_notifications
        if preferences_update.share_analytics is not None:
            update_data["shareAnalytics"] = preferences_update.share_analytics
        if preferences_update.profile_visibility is not None:
            update_data["profileVisibility"] = preferences_update.profile_visibility.value
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay preferencias para actualizar"
            )
        
        # Verificar si existen preferencias
        existing_prefs = await db.userpreferences.find_unique(
            where={"userId": current_user_id}
        )
        
        if existing_prefs:
            # Actualizar preferencias existentes
            await db.userpreferences.update(
                where={"userId": current_user_id},
                data=update_data
            )
        else:
            # Crear nuevas preferencias
            await db.userpreferences.create(
                data={
                    "userId": current_user_id,
                    **update_data
                }
            )
        
        return APIResponse(message="Preferencias actualizadas exitosamente")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error actualizando preferencias: {str(e)}"
        )


# ============= ENDPOINTS DE ACTUALIZACIÓN AVANZADA =============

@router.put("/profile/advanced", response_model=APIResponse) 
async def update_advanced_profile(
    profile_update: UserAdvancedUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
) -> APIResponse:
    """
    Actualización avanzada del perfil de usuario
    """
    try:
        update_data = {}
        for field, value in profile_update.dict(exclude_unset=True).items():
            if value is not None:
                # Convertir nombres de campos para Prisma
                prisma_field = {
                    "first_name": "firstName",
                    "last_name": "lastName", 
                    "date_of_birth": "dateOfBirth",
                    "skin_tone": "skinTone",
                    "hair_color": "hairColor",
                    "eye_color": "eyeColor"
                }.get(field, field)
                
                update_data[prisma_field] = value
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay datos para actualizar"
            )
        
        await db.user.update(
            where={"id": current_user_id},
            data=update_data
        )
        
        return APIResponse(message="Perfil actualizado exitosamente")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error actualizando perfil: {str(e)}"
        )


@router.post("/activity", response_model=APIResponse)
async def track_user_activity(
    activity_data: Dict[str, Any] = Body(..., description="Datos de actividad del usuario"),
    current_user_id: str = Depends(get_current_user_id)
) -> APIResponse:
    """
    Registrar actividad del usuario para analytics
    """
    try:
        await user_service.update_user_activity(current_user_id, activity_data)
        
        return APIResponse(message="Actividad registrada exitosamente")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registrando actividad: {str(e)}"
        )


# ============= ENDPOINTS ADMINISTRATIVOS =============

@router.get("/all", response_model=PaginatedResponse)
async def get_all_users(
    pagination: PaginationParams = Depends(),
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
) -> PaginatedResponse:
    """
    Obtener lista de usuarios (solo para administradores)
    """
    try:
        # Verificar permisos de administrador
        current_user = await db.user.find_unique(where={"id": current_user_id})
        if not current_user or current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para acceder a esta información"
            )
        
        # Calcular offset
        offset = (pagination.page - 1) * pagination.limit
        
        # Obtener usuarios con paginación
        users = await db.user.find_many(
            skip=offset,
            take=pagination.limit,
            order={"createdAt": "desc"},
            include={"analytics": True}
        )
        
        # Contar total de usuarios
        total = await db.user.count()
        
        return PaginatedResponse(
            items=users,
            total=total,
            page=pagination.page,
            limit=pagination.limit,
            pages=(total + pagination.limit - 1) // pagination.limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo usuarios: {str(e)}"
        )


@router.get("/statistics", response_model=APIResponse)
async def get_platform_statistics(
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
) -> APIResponse:
    """
    Obtener estadísticas generales de la plataforma (solo para administradores)
    """
    try:
        # Verificar permisos de administrador
        current_user = await db.user.find_unique(where={"id": current_user_id})
        if not current_user or current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para acceder a esta información"
            )
        
        # Obtener estadísticas
        total_users = await db.user.count()
        active_users = await db.user.count(where={"isActive": True})
        verified_users = await db.user.count(where={"isVerified": True})
        onboarded_users = await db.user.count(where={"onboardingCompleted": True})
        
        # Estadísticas por tier
        tier_stats = {}
        for tier in SubscriptionTier:
            count = await db.user.count(where={"subscriptionTier": tier})
            tier_stats[tier.value] = count
        
        # Estadísticas de análisis
        total_facial_analyses = await db.facialanalysis.count()
        total_chromatic_analyses = await db.chromaticanalysis.count()
        
        # Estadísticas de los últimos 30 días
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        new_users_30d = await db.user.count(
            where={"createdAt": {"gte": thirty_days_ago}}
        )
        analyses_30d = await db.facialanalysis.count(
            where={"createdAt": {"gte": thirty_days_ago}}
        ) + await db.chromaticanalysis.count(
            where={"createdAt": {"gte": thirty_days_ago}}
        )
        
        statistics = {
            "users": {
                "total": total_users,
                "active": active_users,
                "verified": verified_users,
                "onboarded": onboarded_users,
                "new_last_30_days": new_users_30d
            },
            "subscriptions": tier_stats,
            "analyses": {
                "total_facial": total_facial_analyses,
                "total_chromatic": total_chromatic_analyses,
                "total": total_facial_analyses + total_chromatic_analyses,
                "last_30_days": analyses_30d
            },
            "engagement": {
                "onboarding_completion_rate": (onboarded_users / total_users * 100) if total_users > 0 else 0,
                "verification_rate": (verified_users / total_users * 100) if total_users > 0 else 0
            }
        }
        
        return APIResponse(
            message="Estadísticas obtenidas exitosamente",
            data=statistics
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )


@router.delete("/profile", response_model=APIResponse)
async def delete_user_profile(
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
) -> APIResponse:
    """
    Eliminar perfil de usuario (soft delete)
    """
    try:
        # Verificar que el usuario existe
        user = await db.user.find_unique(where={"id": current_user_id})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Realizar soft delete
        await db.user.update(
            where={"id": current_user_id},
            data={"isActive": False}
        )
        
        return APIResponse(message="Perfil eliminado exitosamente")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error eliminando perfil: {str(e)}"
        )


@router.delete("/account", response_model=APIResponse)
async def delete_user_account(
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
) -> APIResponse:
    """
    Eliminar cuenta de usuario (soft delete)
    """
    try:
        # Desactivar usuario en lugar de eliminar completamente
        await db.user.update(
            where={"id": current_user_id},
            data={"isActive": False}
        )
        
        # Invalidar todas las sesiones
        await db.usersession.update_many(
            where={"userId": current_user_id},
            data={"isActive": False}
        )
        
        return APIResponse(message="Cuenta desactivada exitosamente")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error eliminando cuenta: {str(e)}"
        )
