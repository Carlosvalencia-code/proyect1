"""
Servicio de manejo de archivos para Synthia Style
Gestiona uploads, validación y almacenamiento de imágenes
"""

import os
import uuid
import shutil
import hashlib
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from pathlib import Path

import aiofiles
from PIL import Image, ExifTags
from fastapi import UploadFile, HTTPException, status

from app.core.config import settings
from app.core.security import SecurityValidator
from app.core.logging import DatabaseLogger
from app.schemas.common import ImageMetadata, FileUpload


class FileService:
    """Servicio para manejo de archivos e imágenes"""
    
    def __init__(self):
        """Inicializar servicio de archivos"""
        self.upload_dir = Path(settings.upload_path)
        self.max_file_size = settings.MAX_FILE_SIZE
        self.allowed_extensions = settings.ALLOWED_EXTENSIONS
        
        # Crear directorios necesarios
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Crear directorios de upload si no existen"""
        directories = [
            self.upload_dir,
            self.upload_dir / "facial",
            self.upload_dir / "temp",
            self.upload_dir / "thumbnails"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _generate_unique_filename(self, original_filename: str, user_id: str) -> str:
        """Generar nombre único para archivo"""
        # Sanitizar nombre original
        sanitized = SecurityValidator.sanitize_filename(original_filename)
        
        # Extraer extensión
        name, ext = os.path.splitext(sanitized)
        
        # Generar ID único
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Construir nombre único
        unique_name = f"{user_id}_{timestamp}_{unique_id}{ext}"
        
        return unique_name
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calcular hash SHA-256 del archivo"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def _get_image_metadata(self, image_path: Path) -> ImageMetadata:
        """Extraer metadatos de imagen"""
        try:
            with Image.open(image_path) as img:
                # Obtener información básica
                width, height = img.size
                format_name = img.format or "UNKNOWN"
                mode = img.mode
                
                # Calcular tamaño en bytes
                size_bytes = image_path.stat().st_size
                
                # Verificar transparencia
                has_transparency = (
                    mode in ('RGBA', 'LA', 'P') or 
                    (mode == 'P' and 'transparency' in img.info)
                )
                
                return ImageMetadata(
                    width=width,
                    height=height,
                    format=format_name,
                    mode=mode,
                    size_bytes=size_bytes,
                    has_transparency=has_transparency
                )
                
        except Exception as e:
            raise ValueError(f"Error leyendo metadatos de imagen: {str(e)}")
    
    def _rotate_image_by_exif(self, image_path: Path) -> None:
        """Rotar imagen basado en datos EXIF"""
        try:
            with Image.open(image_path) as img:
                # Verificar si hay datos EXIF
                if hasattr(img, '_getexif') and img._getexif() is not None:
                    exif = img._getexif()
                    
                    # Buscar orientación
                    for tag, value in exif.items():
                        if tag in ExifTags.TAGS and ExifTags.TAGS[tag] == 'Orientation':
                            # Aplicar rotación según orientación
                            if value == 3:
                                img = img.rotate(180, expand=True)
                            elif value == 6:
                                img = img.rotate(270, expand=True)
                            elif value == 8:
                                img = img.rotate(90, expand=True)
                            
                            # Guardar imagen corregida
                            img.save(image_path)
                            break
                            
        except Exception:
            # Si falla la corrección EXIF, continuar sin error
            pass
    
    def _create_thumbnail(self, image_path: Path, thumbnail_size: Tuple[int, int] = (300, 300)) -> Path:
        """Crear thumbnail de imagen"""
        try:
            thumbnail_dir = self.upload_dir / "thumbnails"
            thumbnail_path = thumbnail_dir / f"thumb_{image_path.name}"
            
            with Image.open(image_path) as img:
                # Crear thumbnail manteniendo proporción
                img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
                
                # Convertir a RGB si es necesario para JPEG
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Guardar thumbnail
                img.save(thumbnail_path, "JPEG", quality=85, optimize=True)
            
            return thumbnail_path
            
        except Exception as e:
            raise ValueError(f"Error creando thumbnail: {str(e)}")
    
    async def validate_upload_file(self, file: UploadFile) -> None:
        """Validar archivo antes de upload"""
        # Verificar nombre de archivo
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nombre de archivo requerido"
            )
        
        # Verificar extensión
        if not SecurityValidator.validate_file_extension(file.filename, self.allowed_extensions):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Extensión no permitida. Permitidas: {self.allowed_extensions}"
            )
        
        # Verificar tamaño
        if file.size and file.size > self.max_file_size:
            size_mb = self.max_file_size / (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Archivo demasiado grande. Máximo: {size_mb}MB"
            )
        
        # Verificar content type
        if file.content_type and not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se permiten archivos de imagen"
            )
    
    async def save_upload_file(
        self, 
        file: UploadFile, 
        user_id: str,
        subfolder: str = "facial"
    ) -> FileUpload:
        """
        Guardar archivo subido
        """
        try:
            # Validar archivo
            await self.validate_upload_file(file)
            
            # Generar nombre único
            unique_filename = self._generate_unique_filename(file.filename, user_id)
            
            # Ruta de destino
            subfolder_path = self.upload_dir / subfolder
            subfolder_path.mkdir(exist_ok=True)
            file_path = subfolder_path / unique_filename
            
            # Guardar archivo
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            # Verificar que es una imagen válida
            try:
                with Image.open(file_path) as img:
                    img.verify()
            except Exception:
                # Eliminar archivo inválido
                if file_path.exists():
                    file_path.unlink()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Archivo de imagen inválido"
                )
            
            # Corregir orientación EXIF
            self._rotate_image_by_exif(file_path)
            
            # Obtener metadatos
            image_metadata = self._get_image_metadata(file_path)
            
            # Crear thumbnail
            thumbnail_path = self._create_thumbnail(file_path)
            
            # Calcular hash
            file_hash = self._calculate_file_hash(file_path)
            
            # Construir URL relativa
            relative_path = file_path.relative_to(self.upload_dir)
            file_url = f"/uploads/{relative_path.as_posix()}"
            
            # Construir respuesta
            file_upload = FileUpload(
                filename=unique_filename,
                content_type=file.content_type or "image/jpeg",
                size=file_path.stat().st_size,
                url=file_url,
                metadata={
                    "original_filename": file.filename,
                    "user_id": user_id,
                    "subfolder": subfolder,
                    "file_hash": file_hash,
                    "image_metadata": image_metadata.dict(),
                    "thumbnail_url": f"/uploads/thumbnails/thumb_{unique_filename}",
                    "upload_timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Log de operación
            DatabaseLogger.log_query(
                operation="file_upload",
                table="files",
                affected_rows=1
            )
            
            return file_upload
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error guardando archivo: {str(e)}"
            )
    
    async def delete_file(self, file_path: str, user_id: str) -> bool:
        """
        Eliminar archivo del sistema
        """
        try:
            # Construir ruta completa
            full_path = self.upload_dir / file_path.lstrip("/uploads/")
            
            # Verificar que el archivo existe
            if not full_path.exists():
                return False
            
            # Verificar permisos (el archivo debe pertenecer al usuario)
            if user_id not in full_path.name:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tiene permisos para eliminar este archivo"
                )
            
            # Eliminar archivo principal
            full_path.unlink()
            
            # Eliminar thumbnail si existe
            thumbnail_path = self.upload_dir / "thumbnails" / f"thumb_{full_path.name}"
            if thumbnail_path.exists():
                thumbnail_path.unlink()
            
            # Log de operación
            DatabaseLogger.log_query(
                operation="file_delete",
                table="files",
                affected_rows=1
            )
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            DatabaseLogger.log_error("file_delete", "files", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error eliminando archivo: {str(e)}"
            )
    
    async def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Obtener información de archivo
        """
        try:
            # Construir ruta completa
            full_path = self.upload_dir / file_path.lstrip("/uploads/")
            
            if not full_path.exists():
                return None
            
            # Obtener estadísticas del archivo
            stat = full_path.stat()
            
            # Construir información
            file_info = {
                "filename": full_path.name,
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "is_image": any(full_path.suffix.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp'])
            }
            
            # Si es imagen, obtener metadatos
            if file_info["is_image"]:
                try:
                    image_metadata = self._get_image_metadata(full_path)
                    file_info["image_metadata"] = image_metadata.dict()
                except Exception:
                    pass
            
            return file_info
            
        except Exception as e:
            return None
    
    async def cleanup_old_files(self, days: int = 30) -> int:
        """
        Limpiar archivos antiguos
        """
        try:
            cutoff_time = datetime.utcnow().timestamp() - (days * 24 * 3600)
            deleted_count = 0
            
            # Recorrer directorio de uploads
            for file_path in self.upload_dir.rglob("*"):
                if file_path.is_file():
                    # Verificar edad del archivo
                    if file_path.stat().st_mtime < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1
            
            # Log de operación
            DatabaseLogger.log_query(
                operation="file_cleanup",
                table="files",
                affected_rows=deleted_count
            )
            
            return deleted_count
            
        except Exception as e:
            DatabaseLogger.log_error("file_cleanup", "files", e)
            return 0
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de almacenamiento
        """
        try:
            stats = {
                "total_files": 0,
                "total_size_bytes": 0,
                "by_type": {},
                "by_folder": {}
            }
            
            # Recorrer archivos
            for file_path in self.upload_dir.rglob("*"):
                if file_path.is_file():
                    stats["total_files"] += 1
                    
                    file_size = file_path.stat().st_size
                    stats["total_size_bytes"] += file_size
                    
                    # Por extensión
                    ext = file_path.suffix.lower()
                    if ext not in stats["by_type"]:
                        stats["by_type"][ext] = {"count": 0, "size": 0}
                    stats["by_type"][ext]["count"] += 1
                    stats["by_type"][ext]["size"] += file_size
                    
                    # Por carpeta
                    folder = file_path.parent.name
                    if folder not in stats["by_folder"]:
                        stats["by_folder"][folder] = {"count": 0, "size": 0}
                    stats["by_folder"][folder]["count"] += 1
                    stats["by_folder"][folder]["size"] += file_size
            
            # Convertir tamaño a MB
            stats["total_size_mb"] = round(stats["total_size_bytes"] / (1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            return {"error": str(e)}


# Instancia global del servicio
file_service = FileService()
