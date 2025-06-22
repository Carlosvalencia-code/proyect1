"""
Endpoints de archivos para Synthia Style API
Maneja upload, validación y gestión de archivos e imágenes
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import JSONResponse

from app.schemas.common import APIResponse, FileUpload
from app.core.security import get_current_user_id
from app.services.file_service import file_service

router = APIRouter()


@router.post("/upload", response_model=FileUpload)
async def upload_file(
    file: UploadFile = File(...),
    subfolder: str = Query(default="facial", regex="^(facial|general|temp)$"),
    current_user_id: str = Depends(get_current_user_id)
) -> FileUpload:
    """
    Subir archivo de imagen
    """
    try:
        # Validar y guardar archivo
        file_info = await file_service.save_upload_file(
            file=file,
            user_id=current_user_id,
            subfolder=subfolder
        )
        
        return file_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error subiendo archivo: {str(e)}"
        )


@router.delete("/delete", response_model=APIResponse)
async def delete_file(
    file_path: str = Query(..., description="Ruta del archivo a eliminar"),
    current_user_id: str = Depends(get_current_user_id)
) -> APIResponse:
    """
    Eliminar archivo del usuario
    """
    try:
        success = await file_service.delete_file(
            file_path=file_path,
            user_id=current_user_id
        )
        
        if success:
            return APIResponse(message="Archivo eliminado exitosamente")
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Archivo no encontrado"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error eliminando archivo: {str(e)}"
        )


@router.get("/info", response_model=APIResponse)
async def get_file_info(
    file_path: str = Query(..., description="Ruta del archivo"),
    current_user_id: str = Depends(get_current_user_id)
) -> APIResponse:
    """
    Obtener información de archivo
    """
    try:
        # Verificar que el archivo pertenece al usuario
        if current_user_id not in file_path:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para acceder a este archivo"
            )
        
        file_info = await file_service.get_file_info(file_path)
        
        if file_info:
            return APIResponse(
                message="Información de archivo obtenida exitosamente",
                data=file_info
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Archivo no encontrado"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo información: {str(e)}"
        )


@router.get("/storage/stats", response_model=APIResponse)
async def get_storage_stats(
    current_user_id: str = Depends(get_current_user_id)
) -> APIResponse:
    """
    Obtener estadísticas de almacenamiento (solo para administradores)
    """
    try:
        stats = file_service.get_storage_stats()
        
        return APIResponse(
            message="Estadísticas de almacenamiento obtenidas exitosamente",
            data=stats
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )


@router.post("/cleanup", response_model=APIResponse)
async def cleanup_old_files(
    days: int = Query(default=30, ge=1, le=365, description="Días de antigüedad"),
    current_user_id: str = Depends(get_current_user_id)
) -> APIResponse:
    """
    Limpiar archivos antiguos (solo para administradores)
    """
    try:
        # TODO: Verificar permisos de administrador
        
        deleted_count = await file_service.cleanup_old_files(days=days)
        
        return APIResponse(
            message=f"Limpieza completada. {deleted_count} archivos eliminados",
            data={"deleted_files": deleted_count}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en limpieza: {str(e)}"
        )


@router.get("/allowed-formats", response_model=APIResponse)
async def get_allowed_formats() -> APIResponse:
    """
    Obtener formatos de archivo permitidos
    """
    from app.core.config import settings
    
    return APIResponse(
        message="Formatos permitidos obtenidos exitosamente",
        data={
            "allowed_extensions": settings.ALLOWED_EXTENSIONS,
            "max_file_size": settings.MAX_FILE_SIZE,
            "max_file_size_mb": round(settings.MAX_FILE_SIZE / (1024 * 1024), 1)
        }
    )
