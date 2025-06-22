"""
Endpoints de feedback para Synthia Style API
Maneja comentarios, valoraciones y sugerencias de usuarios
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.schemas.feedback import (
    FeedbackCreate, FeedbackResponse, FeedbackUpdate, FeedbackFilter,
    FeedbackCategory, FeedbackStatus
)
from app.schemas.common import APIResponse, PaginationParams, PaginatedResponse
from app.core.security import get_current_user_id
from app.db.database import get_db

router = APIRouter()


@router.post("/", response_model=FeedbackResponse)
async def create_feedback(
    feedback_data: FeedbackCreate,
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
) -> FeedbackResponse:
    """
    Crear nuevo feedback
    """
    try:
        # Preparar datos para la base de datos
        create_data = {
            "userId": current_user_id,
            "category": feedback_data.category.value,
            "content": feedback_data.content,
            "status": FeedbackStatus.PENDING.value
        }
        
        # Campos opcionales
        if feedback_data.rating:
            create_data["rating"] = feedback_data.rating
        
        # Crear contexto adicional si se proporciona
        context_data = {}
        if feedback_data.related_analysis_id:
            context_data["related_analysis_id"] = feedback_data.related_analysis_id
        if feedback_data.related_recommendation_id:
            context_data["related_recommendation_id"] = feedback_data.related_recommendation_id
        if feedback_data.user_agent:
            context_data["user_agent"] = feedback_data.user_agent
        if feedback_data.page_url:
            context_data["page_url"] = feedback_data.page_url
        if feedback_data.context_data:
            context_data.update(feedback_data.context_data)
        
        if context_data:
            create_data["contextData"] = context_data
        
        # Crear feedback en la base de datos
        feedback = await db.feedback.create(data=create_data)
        
        return FeedbackResponse(
            id=feedback.id,
            user_id=feedback.userId,
            category=FeedbackCategory(feedback.category),
            title=feedback_data.title,
            content=feedback.content,
            rating=feedback.rating,
            status=FeedbackStatus(feedback.status),
            context_data=feedback.contextData,
            created_at=feedback.createdAt,
            updated_at=feedback.updatedAt
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creando feedback: {str(e)}"
        )


@router.get("/", response_model=PaginatedResponse[FeedbackResponse])
async def get_user_feedback(
    pagination: PaginationParams = Depends(),
    categories: Optional[List[FeedbackCategory]] = Query(None),
    statuses: Optional[List[FeedbackStatus]] = Query(None),
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Obtener feedback del usuario con filtros
    """
    try:
        # Construir filtros
        where_conditions = {"userId": current_user_id}
        
        if categories:
            where_conditions["category"] = {"in": [cat.value for cat in categories]}
        
        if statuses:
            where_conditions["status"] = {"in": [status.value for status in statuses]}
        
        # Contar total
        total = await db.feedback.count(where=where_conditions)
        
        # Obtener feedback paginado
        feedbacks = await db.feedback.find_many(
            where=where_conditions,
            order={"createdAt": "desc"},
            skip=pagination.offset,
            take=pagination.limit
        )
        
        # Convertir a schema
        feedback_responses = []
        for feedback in feedbacks:
            response = FeedbackResponse(
                id=feedback.id,
                user_id=feedback.userId,
                category=FeedbackCategory(feedback.category),
                title=feedback.content[:50] + "..." if len(feedback.content) > 50 else feedback.content,
                content=feedback.content,
                rating=feedback.rating,
                status=FeedbackStatus(feedback.status),
                context_data=feedback.contextData,
                created_at=feedback.createdAt,
                updated_at=feedback.updatedAt
            )
            feedback_responses.append(response)
        
        # Crear metadatos de paginación
        from app.schemas.common import PaginationMeta
        meta = PaginationMeta.create(
            page=pagination.page,
            limit=pagination.limit,
            total=total
        )
        
        return PaginatedResponse(
            data=feedback_responses,
            meta=meta
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo feedback: {str(e)}"
        )


@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
    feedback_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
) -> FeedbackResponse:
    """
    Obtener feedback específico
    """
    try:
        feedback = await db.feedback.find_unique(
            where={"id": feedback_id}
        )
        
        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback no encontrado"
            )
        
        # Verificar que pertenece al usuario
        if feedback.userId != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver este feedback"
            )
        
        return FeedbackResponse(
            id=feedback.id,
            user_id=feedback.userId,
            category=FeedbackCategory(feedback.category),
            title=feedback.content[:50] + "..." if len(feedback.content) > 50 else feedback.content,
            content=feedback.content,
            rating=feedback.rating,
            status=FeedbackStatus(feedback.status),
            context_data=feedback.contextData,
            created_at=feedback.createdAt,
            updated_at=feedback.updatedAt
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo feedback: {str(e)}"
        )


@router.put("/{feedback_id}", response_model=FeedbackResponse)
async def update_feedback(
    feedback_id: str,
    feedback_update: FeedbackUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
) -> FeedbackResponse:
    """
    Actualizar feedback del usuario
    """
    try:
        # Verificar que el feedback existe y pertenece al usuario
        existing_feedback = await db.feedback.find_unique(
            where={"id": feedback_id}
        )
        
        if not existing_feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback no encontrado"
            )
        
        if existing_feedback.userId != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para actualizar este feedback"
            )
        
        # Construir datos de actualización
        update_data = {}
        if feedback_update.content is not None:
            update_data["content"] = feedback_update.content
        if feedback_update.rating is not None:
            update_data["rating"] = feedback_update.rating
        if feedback_update.status is not None:
            update_data["status"] = feedback_update.status.value
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay datos para actualizar"
            )
        
        # Actualizar feedback
        updated_feedback = await db.feedback.update(
            where={"id": feedback_id},
            data=update_data
        )
        
        return FeedbackResponse(
            id=updated_feedback.id,
            user_id=updated_feedback.userId,
            category=FeedbackCategory(updated_feedback.category),
            title=feedback_update.title or existing_feedback.content[:50],
            content=updated_feedback.content,
            rating=updated_feedback.rating,
            status=FeedbackStatus(updated_feedback.status),
            context_data=updated_feedback.contextData,
            created_at=updated_feedback.createdAt,
            updated_at=updated_feedback.updatedAt
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error actualizando feedback: {str(e)}"
        )


@router.delete("/{feedback_id}", response_model=APIResponse)
async def delete_feedback(
    feedback_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
) -> APIResponse:
    """
    Eliminar feedback del usuario
    """
    try:
        # Verificar que el feedback existe y pertenece al usuario
        feedback = await db.feedback.find_unique(
            where={"id": feedback_id}
        )
        
        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback no encontrado"
            )
        
        if feedback.userId != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para eliminar este feedback"
            )
        
        # Eliminar feedback
        await db.feedback.delete(
            where={"id": feedback_id}
        )
        
        return APIResponse(message="Feedback eliminado exitosamente")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error eliminando feedback: {str(e)}"
        )


@router.get("/stats/summary", response_model=APIResponse)
async def get_feedback_stats(
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
) -> APIResponse:
    """
    Obtener estadísticas de feedback del usuario
    """
    try:
        # Obtener feedback del usuario
        feedbacks = await db.feedback.find_many(
            where={"userId": current_user_id}
        )
        
        total_feedback = len(feedbacks)
        
        if total_feedback == 0:
            return APIResponse(
                message="No hay feedback disponible",
                data={
                    "total_feedback": 0,
                    "average_rating": 0,
                    "category_distribution": {},
                    "status_distribution": {}
                }
            )
        
        # Calcular estadísticas
        category_distribution = {}
        status_distribution = {}
        total_rating = 0
        rating_count = 0
        
        for feedback in feedbacks:
            # Por categoría
            category = feedback.category
            category_distribution[category] = category_distribution.get(category, 0) + 1
            
            # Por estado
            status = feedback.status
            status_distribution[status] = status_distribution.get(status, 0) + 1
            
            # Rating promedio
            if feedback.rating:
                total_rating += feedback.rating
                rating_count += 1
        
        average_rating = total_rating / rating_count if rating_count > 0 else 0
        
        return APIResponse(
            message="Estadísticas de feedback obtenidas exitosamente",
            data={
                "total_feedback": total_feedback,
                "average_rating": round(average_rating, 1),
                "category_distribution": category_distribution,
                "status_distribution": status_distribution
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )
