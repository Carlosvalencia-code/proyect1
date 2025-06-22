"""
Endpoints de análisis facial para Synthia Style API
Maneja análisis de rostro y recomendaciones de estilo con sistema de suscripciones
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse

from app.schemas.facial_analysis import (
    FacialAnalysisRequest, FacialAnalysisResponse, FacialAnalysisResult,
    FacialAnalysisHistory, FacialAnalysisFilter, FaceShapeEnum
)
from app.schemas.common import APIResponse, PaginationParams, PaginatedResponse
from app.core.security import get_current_user_id
from app.db.database import get_db
from app.services.gemini_service import gemini_service
from app.services.file_service import file_service
from app.services.user_service import subscription_service, user_onboarding_service

router = APIRouter()


@router.post("/analyze", response_model=FacialAnalysisResponse)
async def analyze_facial_features(
    analysis_request: FacialAnalysisRequest,
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
) -> FacialAnalysisResponse:
    """
    Realizar análisis facial con IA - Incluye verificación de límites de suscripción
    """
    try:
        # Verificar límites de uso antes del análisis
        usage_limits = await subscription_service.check_usage_limits(current_user_id)
        
        if not usage_limits.can_analyze:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "message": "Has alcanzado tu límite de análisis",
                    "daily_limit": usage_limits.daily_analyses_limit,
                    "monthly_limit": usage_limits.monthly_analyses_limit,
                    "time_until_reset": usage_limits.time_until_reset,
                    "current_tier": usage_limits.current_tier.value
                }
            )
        
        start_time = datetime.utcnow()
        
        # Realizar análisis con Gemini AI
        ai_result = await gemini_service.analyze_facial_features(
            image_data=analysis_request.image_data,
            user_id=current_user_id,
            preferences=analysis_request.analysis_preferences
        )
        
        # Guardar imagen (opcional - convertir base64 a archivo)
        # Por ahora, generamos una URL ficticia
        image_url = f"/uploads/facial/{current_user_id}_{int(datetime.utcnow().timestamp())}.jpg"
        
        # Crear registro en la base de datos
        analysis_data = {
            "userId": current_user_id,
            "imageUrl": image_url,
            "faceShape": ai_result["forma_rostro"].value,
            "featuresHighlighted": ai_result.get("caracteristicas_destacadas", []),
            "confidenceLevel": ai_result.get("confianza_analisis", 85),
            "analysisData": ai_result
        }
        
        facial_analysis = await db.facialanalysis.create(data=analysis_data)
        
        # Incrementar contadores de uso
        await subscription_service.increment_usage(current_user_id, "facial")
        
        # Verificar si es su primer análisis para onboarding
        user = await db.user.find_unique(where={"id": current_user_id})
        if user and not user.onboardingCompleted:
            await user_onboarding_service.complete_onboarding_step(current_user_id, 4)
        
        # Crear recomendaciones
        recommendations_data = []
        ai_recommendations = ai_result.get("recomendaciones", {})
        
        for category, items in ai_recommendations.items():
            if isinstance(items, list):
                for item in items:
                    rec_data = {
                        "facialAnalysisId": facial_analysis.id,
                        "category": category,
                        "name": item.get("nombre", item.get("tipo", "Recomendación")),
                        "description": item.get("descripcion", ""),
                        "explanation": item.get("explicacion", ""),
                        "priority": 1,
                        "score": 0.9
                    }
                    recommendations_data.append(rec_data)
        
        # Guardar recomendaciones en lote
        if recommendations_data:
            await db.facialrecommendation.create_many(data=recommendations_data)
        
        # Calcular tiempo de procesamiento
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds() * 1000
        
        # Construir respuesta
        analysis_result = FacialAnalysisResult(
            id=facial_analysis.id,
            user_id=current_user_id,
            image_url=image_url,
            face_shape=FaceShapeEnum(ai_result["forma_rostro"]),
            features_highlighted=[
                {"name": feature, "description": feature, "prominence": 0.8}
                for feature in ai_result.get("caracteristicas_destacadas", [])
            ],
            confidence_level=ai_result.get("confianza_analisis", 85),
            ai_analysis_data=ai_result,
            recommendations=[],  # Se poblarán en una consulta separada si es necesario
            created_at=facial_analysis.createdAt,
            updated_at=facial_analysis.updatedAt
        )
        
        return FacialAnalysisResponse(
            analysis=analysis_result,
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error realizando análisis facial: {str(e)}"
        )


@router.get("/history", response_model=PaginatedResponse[FacialAnalysisResult])
async def get_facial_analysis_history(
    pagination: PaginationParams = Depends(),
    face_shapes: Optional[List[FaceShapeEnum]] = Query(None),
    min_confidence: Optional[int] = Query(None, ge=1, le=100),
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Obtener historial de análisis faciales del usuario
    """
    try:
        # Construir filtros
        where_conditions = {"userId": current_user_id}
        
        if face_shapes:
            where_conditions["faceShape"] = {"in": [shape.value for shape in face_shapes]}
        
        if min_confidence:
            where_conditions["confidenceLevel"] = {"gte": min_confidence}
        
        # Contar total
        total = await db.facialanalysis.count(where=where_conditions)
        
        # Obtener análisis paginados
        analyses = await db.facialanalysis.find_many(
            where=where_conditions,
            include={"recommendations": True},
            order={"createdAt": "desc"},
            skip=pagination.offset,
            take=pagination.limit
        )
        
        # Convertir a schema
        analysis_results = []
        for analysis in analyses:
            result = FacialAnalysisResult(
                id=analysis.id,
                user_id=analysis.userId,
                image_url=analysis.imageUrl,
                face_shape=FaceShapeEnum(analysis.faceShape),
                features_highlighted=analysis.featuresHighlighted or [],
                confidence_level=analysis.confidenceLevel,
                ai_analysis_data=analysis.analysisData,
                recommendations=[],  # Simplificado por ahora
                created_at=analysis.createdAt,
                updated_at=analysis.updatedAt
            )
            analysis_results.append(result)
        
        # Crear metadatos de paginación
        from app.schemas.common import PaginationMeta
        meta = PaginationMeta.create(
            page=pagination.page,
            limit=pagination.limit,
            total=total
        )
        
        return PaginatedResponse(
            data=analysis_results,
            meta=meta
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo historial: {str(e)}"
        )


@router.get("/{analysis_id}", response_model=FacialAnalysisResult)
async def get_facial_analysis(
    analysis_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
) -> FacialAnalysisResult:
    """
    Obtener análisis facial específico
    """
    try:
        analysis = await db.facialanalysis.find_unique(
            where={"id": analysis_id},
            include={"recommendations": True}
        )
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Análisis no encontrado"
            )
        
        # Verificar que pertenece al usuario
        if analysis.userId != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver este análisis"
            )
        
        # Convertir recomendaciones
        from app.schemas.facial_analysis import FacialRecommendation, RecommendationCategory
        recommendations = []
        for rec in analysis.recommendations or []:
            recommendation = FacialRecommendation(
                category=RecommendationCategory(rec.category),
                name=rec.name,
                description=rec.description,
                explanation=rec.explanation,
                priority=rec.priority or 1,
                confidence=rec.score or 0.8
            )
            recommendations.append(recommendation)
        
        return FacialAnalysisResult(
            id=analysis.id,
            user_id=analysis.userId,
            image_url=analysis.imageUrl,
            face_shape=FaceShapeEnum(analysis.faceShape),
            features_highlighted=analysis.featuresHighlighted or [],
            confidence_level=analysis.confidenceLevel,
            ai_analysis_data=analysis.analysisData,
            recommendations=recommendations,
            created_at=analysis.createdAt,
            updated_at=analysis.updatedAt
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo análisis: {str(e)}"
        )


@router.delete("/{analysis_id}", response_model=APIResponse)
async def delete_facial_analysis(
    analysis_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
) -> APIResponse:
    """
    Eliminar análisis facial
    """
    try:
        # Verificar que el análisis existe y pertenece al usuario
        analysis = await db.facialanalysis.find_unique(
            where={"id": analysis_id}
        )
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Análisis no encontrado"
            )
        
        if analysis.userId != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para eliminar este análisis"
            )
        
        # Eliminar recomendaciones asociadas
        await db.facialrecommendation.delete_many(
            where={"facialAnalysisId": analysis_id}
        )
        
        # Eliminar análisis
        await db.facialanalysis.delete(
            where={"id": analysis_id}
        )
        
        # Eliminar archivo de imagen si existe
        if analysis.imageUrl:
            try:
                await file_service.delete_file(analysis.imageUrl, current_user_id)
            except:
                pass  # No fallar si no se puede eliminar el archivo
        
        return APIResponse(message="Análisis eliminado exitosamente")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error eliminando análisis: {str(e)}"
        )


@router.get("/stats/summary", response_model=APIResponse)
async def get_facial_analysis_stats(
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
) -> APIResponse:
    """
    Obtener estadísticas de análisis facial del usuario
    """
    try:
        # Contar análisis por forma de rostro
        analyses = await db.facialanalysis.find_many(
            where={"userId": current_user_id}
        )
        
        # Calcular estadísticas
        total_analyses = len(analyses)
        
        if total_analyses == 0:
            return APIResponse(
                message="No hay análisis disponibles",
                data={
                    "total_analyses": 0,
                    "shape_distribution": {},
                    "average_confidence": 0,
                    "most_common_shape": None
                }
            )
        
        # Distribución por forma
        shape_distribution = {}
        total_confidence = 0
        
        for analysis in analyses:
            shape = analysis.faceShape
            shape_distribution[shape] = shape_distribution.get(shape, 0) + 1
            total_confidence += analysis.confidenceLevel
        
        # Forma más común
        most_common_shape = max(shape_distribution, key=shape_distribution.get)
        average_confidence = total_confidence / total_analyses
        
        return APIResponse(
            message="Estadísticas obtenidas exitosamente",
            data={
                "total_analyses": total_analyses,
                "shape_distribution": shape_distribution,
                "average_confidence": round(average_confidence, 1),
                "most_common_shape": most_common_shape
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )
