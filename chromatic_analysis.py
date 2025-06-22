"""
Endpoints de análisis cromático para Synthia Style API
Maneja análisis de color y paletas personalizadas con sistema de suscripciones
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.schemas.chromatic_analysis import (
    ChromaticAnalysisRequest, ChromaticAnalysisResponse, ChromaticAnalysisResult,
    ColorSeasonEnum, SkinUndertoneEnum, ChromaticAnalysisFilter
)
from app.schemas.common import APIResponse, PaginationParams, PaginatedResponse
from app.core.security import get_current_user_id
from app.db.database import get_db
from app.services.gemini_service import gemini_service
from app.services.user_service import subscription_service, user_onboarding_service

router = APIRouter()


@router.post("/analyze", response_model=ChromaticAnalysisResponse)
async def analyze_chromatic_profile(
    analysis_request: ChromaticAnalysisRequest,
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
) -> ChromaticAnalysisResponse:
    """
    Realizar análisis cromático con IA - Incluye verificación de límites de suscripción
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
        
        # Convertir respuestas del quiz a diccionario
        quiz_responses_dict = {
            response.question_id: response.answer
            for response in analysis_request.quiz_responses
        }
        
        # Realizar análisis con Gemini AI
        ai_result = await gemini_service.analyze_chromatic_profile(
            quiz_responses=quiz_responses_dict,
            user_id=current_user_id,
            preferences=analysis_request.analysis_preferences
        )
        
        # Preparar datos para la base de datos
        quiz_responses_data = [
            {
                "question_id": resp.question_id,
                "answer": resp.answer,
                "confidence": resp.confidence
            }
            for resp in analysis_request.quiz_responses
        ]
        
        analysis_data = {
            "userId": current_user_id,
            "quizResponses": quiz_responses_data,
            "colorSeason": ai_result["estacion"].value,
            "skinUndertone": ai_result["subtono"].value,
            "confidenceLevel": ai_result.get("confianza_analisis", 85),
            "description": ai_result.get("descripcion", ""),
            "analysisData": ai_result
        }
        
        # Crear registro en la base de datos
        chromatic_analysis = await db.chromaticanalysis.create(data=analysis_data)
        
        # Incrementar contadores de uso
        await subscription_service.increment_usage(current_user_id, "chromatic")
        
        # Verificar si es su primer análisis para onboarding
        user = await db.user.find_unique(where={"id": current_user_id})
        if user and not user.onboardingCompleted:
            await user_onboarding_service.complete_onboarding_step(current_user_id, 4)
        
        # Crear recomendaciones de color
        recommendations_data = []
        
        # Procesar paleta primaria
        for color_item in ai_result.get("paleta_primaria", []):
            rec_data = {
                "chromaticAnalysisId": chromatic_analysis.id,
                "type": "primary_palette",
                "colorName": color_item.get("color", "Color"),
                "hexCode": color_item.get("codigo_hex", "#000000"),
                "explanation": color_item.get("explicacion", ""),
                "priority": 1,
                "score": 0.9
            }
            recommendations_data.append(rec_data)
        
        # Procesar colores a evitar
        for color_item in ai_result.get("colores_evitar", []):
            rec_data = {
                "chromaticAnalysisId": chromatic_analysis.id,
                "type": "colors_to_avoid",
                "colorName": color_item.get("color", "Color"),
                "hexCode": color_item.get("codigo_hex", "#000000"),
                "explanation": color_item.get("explicacion", ""),
                "priority": 1,
                "score": 0.1
            }
            recommendations_data.append(rec_data)
        
        # Guardar recomendaciones en lote
        if recommendations_data:
            await db.colorrecommendation.create_many(data=recommendations_data)
        
        # Calcular tiempo de procesamiento
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds() * 1000
        
        # Construir respuesta
        from app.schemas.chromatic_analysis import SeasonCharacteristics
        season_characteristics = SeasonCharacteristics(
            season=ai_result["estacion"],
            undertone=ai_result["subtono"],
            description=ai_result.get("descripcion", ""),
            key_characteristics=[],  # Se puede mejorar con más datos de Gemini
            contrast_level="alto" if ai_result["estacion"] == ColorSeasonEnum.INVIERNO else "medio",
            intensity_level="alto" if ai_result["estacion"] == ColorSeasonEnum.INVIERNO else "medio"
        )
        
        analysis_result = ChromaticAnalysisResult(
            id=chromatic_analysis.id,
            user_id=current_user_id,
            quiz_responses=analysis_request.quiz_responses,
            color_season=ai_result["estacion"],
            skin_undertone=ai_result["subtono"],
            confidence_level=ai_result.get("confianza_analisis", 85),
            season_characteristics=season_characteristics,
            ai_analysis_data=ai_result,
            color_recommendations=[],  # Se poblarán en consulta separada si es necesario
            created_at=chromatic_analysis.createdAt,
            updated_at=chromatic_analysis.updatedAt
        )
        
        return ChromaticAnalysisResponse(
            analysis=analysis_result,
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error realizando análisis cromático: {str(e)}"
        )


@router.get("/history", response_model=PaginatedResponse[ChromaticAnalysisResult])
async def get_chromatic_analysis_history(
    pagination: PaginationParams = Depends(),
    seasons: Optional[List[ColorSeasonEnum]] = Query(None),
    undertones: Optional[List[SkinUndertoneEnum]] = Query(None),
    min_confidence: Optional[int] = Query(None, ge=1, le=100),
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Obtener historial de análisis cromáticos del usuario
    """
    try:
        # Construir filtros
        where_conditions = {"userId": current_user_id}
        
        if seasons:
            where_conditions["colorSeason"] = {"in": [season.value for season in seasons]}
        
        if undertones:
            where_conditions["skinUndertone"] = {"in": [undertone.value for undertone in undertones]}
        
        if min_confidence:
            where_conditions["confidenceLevel"] = {"gte": min_confidence}
        
        # Contar total
        total = await db.chromaticanalysis.count(where=where_conditions)
        
        # Obtener análisis paginados
        analyses = await db.chromaticanalysis.find_many(
            where=where_conditions,
            include={"colorRecommendations": True},
            order={"createdAt": "desc"},
            skip=pagination.offset,
            take=pagination.limit
        )
        
        # Convertir a schema
        analysis_results = []
        for analysis in analyses:
            # Convertir quiz responses
            from app.schemas.chromatic_analysis import QuizResponse
            quiz_responses = []
            for resp_data in analysis.quizResponses or []:
                quiz_responses.append(QuizResponse(
                    question_id=resp_data.get("question_id", ""),
                    answer=resp_data.get("answer", ""),
                    confidence=resp_data.get("confidence")
                ))
            
            # Crear características de estación básicas
            from app.schemas.chromatic_analysis import SeasonCharacteristics
            season_characteristics = SeasonCharacteristics(
                season=ColorSeasonEnum(analysis.colorSeason),
                undertone=SkinUndertoneEnum(analysis.skinUndertone),
                description=analysis.description or "",
                key_characteristics=[],
                contrast_level="alto",
                intensity_level="alto"
            )
            
            result = ChromaticAnalysisResult(
                id=analysis.id,
                user_id=analysis.userId,
                quiz_responses=quiz_responses,
                color_season=ColorSeasonEnum(analysis.colorSeason),
                skin_undertone=SkinUndertoneEnum(analysis.skinUndertone),
                confidence_level=analysis.confidenceLevel,
                season_characteristics=season_characteristics,
                ai_analysis_data=analysis.analysisData,
                color_recommendations=[],  # Simplificado por ahora
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


@router.get("/{analysis_id}", response_model=ChromaticAnalysisResult)
async def get_chromatic_analysis(
    analysis_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
) -> ChromaticAnalysisResult:
    """
    Obtener análisis cromático específico
    """
    try:
        analysis = await db.chromaticanalysis.find_unique(
            where={"id": analysis_id},
            include={"colorRecommendations": True}
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
        
        # Convertir quiz responses
        from app.schemas.chromatic_analysis import QuizResponse
        quiz_responses = []
        for resp_data in analysis.quizResponses or []:
            quiz_responses.append(QuizResponse(
                question_id=resp_data.get("question_id", ""),
                answer=resp_data.get("answer", ""),
                confidence=resp_data.get("confidence")
            ))
        
        # Convertir recomendaciones de color
        from app.schemas.chromatic_analysis import ColorRecommendation, ColorRecommendationType
        color_recommendations = []
        for rec in analysis.colorRecommendations or []:
            recommendation = ColorRecommendation(
                type=ColorRecommendationType(rec.type),
                color_name=rec.colorName,
                hex_code=rec.hexCode,
                explanation=rec.explanation,
                priority=rec.priority or 1,
                confidence=rec.score or 0.8
            )
            color_recommendations.append(recommendation)
        
        # Crear características de estación
        from app.schemas.chromatic_analysis import SeasonCharacteristics
        season_characteristics = SeasonCharacteristics(
            season=ColorSeasonEnum(analysis.colorSeason),
            undertone=SkinUndertoneEnum(analysis.skinUndertone),
            description=analysis.description or "",
            key_characteristics=[],
            contrast_level="alto",
            intensity_level="alto"
        )
        
        return ChromaticAnalysisResult(
            id=analysis.id,
            user_id=analysis.userId,
            quiz_responses=quiz_responses,
            color_season=ColorSeasonEnum(analysis.colorSeason),
            skin_undertone=SkinUndertoneEnum(analysis.skinUndertone),
            confidence_level=analysis.confidenceLevel,
            season_characteristics=season_characteristics,
            ai_analysis_data=analysis.analysisData,
            color_recommendations=color_recommendations,
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
async def delete_chromatic_analysis(
    analysis_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
) -> APIResponse:
    """
    Eliminar análisis cromático
    """
    try:
        # Verificar que el análisis existe y pertenece al usuario
        analysis = await db.chromaticanalysis.find_unique(
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
        await db.colorrecommendation.delete_many(
            where={"chromaticAnalysisId": analysis_id}
        )
        
        # Eliminar análisis
        await db.chromaticanalysis.delete(
            where={"id": analysis_id}
        )
        
        return APIResponse(message="Análisis cromático eliminado exitosamente")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error eliminando análisis: {str(e)}"
        )


@router.get("/stats/summary", response_model=APIResponse)
async def get_chromatic_analysis_stats(
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
) -> APIResponse:
    """
    Obtener estadísticas de análisis cromático del usuario
    """
    try:
        # Obtener análisis del usuario
        analyses = await db.chromaticanalysis.find_many(
            where={"userId": current_user_id}
        )
        
        total_analyses = len(analyses)
        
        if total_analyses == 0:
            return APIResponse(
                message="No hay análisis disponibles",
                data={
                    "total_analyses": 0,
                    "season_distribution": {},
                    "undertone_distribution": {},
                    "average_confidence": 0,
                    "most_common_season": None
                }
            )
        
        # Calcular distribuciones
        season_distribution = {}
        undertone_distribution = {}
        total_confidence = 0
        
        for analysis in analyses:
            # Por estación
            season = analysis.colorSeason
            season_distribution[season] = season_distribution.get(season, 0) + 1
            
            # Por subtono
            undertone = analysis.skinUndertone
            undertone_distribution[undertone] = undertone_distribution.get(undertone, 0) + 1
            
            total_confidence += analysis.confidenceLevel
        
        # Estación más común
        most_common_season = max(season_distribution, key=season_distribution.get)
        average_confidence = total_confidence / total_analyses
        
        return APIResponse(
            message="Estadísticas obtenidas exitosamente",
            data={
                "total_analyses": total_analyses,
                "season_distribution": season_distribution,
                "undertone_distribution": undertone_distribution,
                "average_confidence": round(average_confidence, 1),
                "most_common_season": most_common_season
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )
