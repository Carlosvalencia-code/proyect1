"""
Esquemas comunes para la API de Synthia Style
Modelos base y utilitarios reutilizables
"""

from typing import Optional, Any, List, Dict, Generic, TypeVar
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, validator
from pydantic.generics import GenericModel


# Tipos genéricos para respuestas paginadas
T = TypeVar('T')


class ResponseStatus(str, Enum):
    """Estado de respuesta de la API"""
    SUCCESS = "success"
    ERROR = "error" 
    WARNING = "warning"
    INFO = "info"


class APIResponse(BaseModel):
    """Respuesta estándar de la API"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseModel):
    """Respuesta de error estandarizada"""
    status: ResponseStatus = ResponseStatus.ERROR
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class HealthCheck(BaseModel):
    """Schema para health check de la aplicación"""
    status: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    environment: str
    database: Dict[str, Any]
    services: Dict[str, Dict[str, Any]] = {}
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaginationParams(BaseModel):
    """Parámetros de paginación"""
    page: int = Field(default=1, ge=1, description="Número de página (inicia en 1)")
    limit: int = Field(default=20, ge=1, le=100, description="Elementos por página")
    
    @property
    def offset(self) -> int:
        """Calcular offset para base de datos"""
        return (self.page - 1) * self.limit


class PaginationMeta(BaseModel):
    """Metadatos de paginación"""
    page: int
    limit: int
    total: int
    pages: int
    has_next: bool
    has_prev: bool
    
    @classmethod
    def create(cls, page: int, limit: int, total: int) -> "PaginationMeta":
        """Crear metadatos de paginación"""
        pages = (total + limit - 1) // limit  # Redondeo hacia arriba
        return cls(
            page=page,
            limit=limit,
            total=total,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )


class PaginatedResponse(GenericModel, Generic[T]):
    """Respuesta paginada genérica"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str = "Datos obtenidos exitosamente"
    data: List[T]
    meta: PaginationMeta
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FileUpload(BaseModel):
    """Schema para upload de archivos"""
    filename: str
    content_type: str
    size: int
    url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('filename')
    def validate_filename(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('El nombre del archivo es requerido')
        return v.strip()
    
    @validator('size')
    def validate_file_size(cls, v):
        if v <= 0:
            raise ValueError('El tamaño del archivo debe ser mayor a 0')
        return v


class ImageMetadata(BaseModel):
    """Metadatos de imagen"""
    width: int = Field(gt=0, description="Ancho en píxeles")
    height: int = Field(gt=0, description="Alto en píxeles")
    format: str = Field(description="Formato de imagen (JPEG, PNG, etc.)")
    mode: str = Field(description="Modo de color (RGB, RGBA, etc.)")
    size_bytes: int = Field(gt=0, description="Tamaño en bytes")
    has_transparency: bool = Field(default=False, description="Tiene transparencia")
    
    @validator('format')
    def validate_format(cls, v):
        allowed_formats = ['JPEG', 'PNG', 'WEBP', 'GIF']
        if v.upper() not in allowed_formats:
            raise ValueError(f'Formato no soportado: {v}. Permitidos: {allowed_formats}')
        return v.upper()


class SortParams(BaseModel):
    """Parámetros de ordenamiento"""
    field: str = Field(description="Campo por el cual ordenar")
    direction: str = Field(default="asc", regex="^(asc|desc)$", description="Dirección del ordenamiento")
    
    @validator('field')
    def validate_field(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('El campo de ordenamiento es requerido')
        return v.strip()


class FilterParams(BaseModel):
    """Parámetros de filtrado genéricos"""
    search: Optional[str] = Field(None, description="Término de búsqueda")
    date_from: Optional[datetime] = Field(None, description="Fecha desde")
    date_to: Optional[datetime] = Field(None, description="Fecha hasta")
    
    @validator('date_to')
    def validate_date_range(cls, v, values):
        if v and 'date_from' in values and values['date_from']:
            if v < values['date_from']:
                raise ValueError('date_to debe ser posterior a date_from')
        return v


class CoordinatesData(BaseModel):
    """Coordenadas geográficas"""
    latitude: float = Field(ge=-90, le=90, description="Latitud")
    longitude: float = Field(ge=-180, le=180, description="Longitud")
    
    class Config:
        schema_extra = {
            "example": {
                "latitude": -12.0464,
                "longitude": -77.0428
            }
        }


class ContactInfo(BaseModel):
    """Información de contacto"""
    email: Optional[str] = Field(None, regex=r'^[^@]+@[^@]+\.[^@]+$')
    phone: Optional[str] = Field(None, regex=r'^\+?[1-9]\d{1,14}$')
    website: Optional[str] = Field(None, regex=r'^https?://.+')
    
    @validator('email')
    def validate_email(cls, v):
        if v and len(v) > 254:
            raise ValueError('Email demasiado largo')
        return v


class SystemInfo(BaseModel):
    """Información del sistema"""
    version: str
    environment: str
    python_version: str
    uptime_seconds: float
    memory_usage_mb: float
    cpu_usage_percent: float
    
    class Config:
        schema_extra = {
            "example": {
                "version": "1.0.0",
                "environment": "production",
                "python_version": "3.11.0",
                "uptime_seconds": 3600.0,
                "memory_usage_mb": 128.5,
                "cpu_usage_percent": 25.3
            }
        }


class ValidationError(BaseModel):
    """Error de validación detallado"""
    field: str
    message: str
    code: str
    value: Any
    
    class Config:
        schema_extra = {
            "example": {
                "field": "email",
                "message": "Formato de email inválido",
                "code": "invalid_format",
                "value": "email-invalido"
            }
        }


class BulkOperation(BaseModel):
    """Operación en lote"""
    operation: str = Field(description="Tipo de operación")
    ids: List[str] = Field(description="Lista de IDs a procesar")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Parámetros adicionales")
    
    @validator('ids')
    def validate_ids(cls, v):
        if len(v) == 0:
            raise ValueError('La lista de IDs no puede estar vacía')
        if len(v) > 100:
            raise ValueError('Máximo 100 IDs por operación')
        return v


class BulkOperationResult(BaseModel):
    """Resultado de operación en lote"""
    total: int
    successful: int
    failed: int
    errors: List[ValidationError] = []
    results: List[Dict[str, Any]] = []
    
    @property
    def success_rate(self) -> float:
        """Tasa de éxito de la operación"""
        if self.total == 0:
            return 0.0
        return (self.successful / self.total) * 100


# Configuración base para todos los modelos
class BaseConfig:
    """Configuración base para modelos Pydantic"""
    use_enum_values = True
    validate_assignment = True
    extra = "forbid"
    json_encoders = {
        datetime: lambda v: v.isoformat() if v else None,
    }


# Mixin para timestamps
class TimestampMixin(BaseModel):
    """Mixin para campos de timestamp"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Config(BaseConfig):
        pass


# Mixin para metadatos
class MetadataMixin(BaseModel):
    """Mixin para campos de metadatos"""
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadatos adicionales")
    
    class Config(BaseConfig):
        pass
