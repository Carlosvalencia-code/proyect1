"""
Esquemas de autenticación para Synthia Style API
Modelos para login, registro, tokens y gestión de sesiones
"""

from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field, validator, EmailStr
from .common import BaseConfig, TimestampMixin


class UserRegister(BaseModel):
    """Schema para registro de usuario"""
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(
        ..., 
        min_length=8, 
        max_length=128,
        description="Contraseña (mínimo 8 caracteres)"
    )
    first_name: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=50,
        description="Nombre"
    )
    last_name: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=50,
        description="Apellido"
    )
    
    @validator('password')
    def validate_password(cls, v):
        """Validar fortaleza de contraseña"""
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        
        # Verificar que contenga al menos una letra y un número
        has_letter = any(c.isalpha() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not has_letter:
            raise ValueError('La contraseña debe contener al menos una letra')
        if not has_digit:
            raise ValueError('La contraseña debe contener al menos un número')
        
        return v
    
    @validator('email')
    def validate_email_domain(cls, v):
        """Validaciones adicionales de email"""
        if len(v) > 254:
            raise ValueError('Email demasiado largo')
        
        # Lista de dominios temporales comunes (opcional)
        temp_domains = [
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com'
        ]
        
        domain = v.split('@')[1].lower()
        if domain in temp_domains:
            raise ValueError('No se permiten emails temporales')
        
        return v.lower()
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "email": "maria@example.com",
                "password": "miContraseñaSegura123",
                "first_name": "María",
                "last_name": "García"
            }
        }


class UserLogin(BaseModel):
    """Schema para login de usuario"""
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(..., description="Contraseña")
    remember_me: bool = Field(default=False, description="Recordar sesión")
    
    @validator('email')
    def normalize_email(cls, v):
        """Normalizar email a minúsculas"""
        return v.lower()
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "email": "maria@example.com",
                "password": "miContraseñaSegura123",
                "remember_me": false
            }
        }


class Token(BaseModel):
    """Schema para token de acceso"""
    access_token: str = Field(..., description="Token de acceso JWT")
    refresh_token: str = Field(..., description="Token de refresh")
    token_type: str = Field(default="bearer", description="Tipo de token")
    expires_in: int = Field(..., description="Tiempo de expiración en segundos")
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }


class TokenData(BaseModel):
    """Schema para datos del token decodificado"""
    user_id: str = Field(..., description="ID del usuario")
    email: Optional[str] = Field(None, description="Email del usuario")
    token_type: str = Field(default="access", description="Tipo de token")
    expires_at: datetime = Field(..., description="Fecha de expiración")
    issued_at: datetime = Field(..., description="Fecha de emisión")
    
    class Config(BaseConfig):
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RefreshToken(BaseModel):
    """Schema para refresh de token"""
    refresh_token: str = Field(..., description="Token de refresh")
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4..."
            }
        }


class PasswordReset(BaseModel):
    """Schema para solicitud de reset de contraseña"""
    email: EmailStr = Field(..., description="Email del usuario")
    
    @validator('email')
    def normalize_email(cls, v):
        return v.lower()
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "email": "maria@example.com"
            }
        }


class PasswordResetConfirm(BaseModel):
    """Schema para confirmación de reset de contraseña"""
    token: str = Field(..., description="Token de reset")
    new_password: str = Field(
        ..., 
        min_length=8, 
        max_length=128,
        description="Nueva contraseña"
    )
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validar nueva contraseña"""
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        
        has_letter = any(c.isalpha() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not has_letter:
            raise ValueError('La contraseña debe contener al menos una letra')
        if not has_digit:
            raise ValueError('La contraseña debe contener al menos un número')
        
        return v
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "token": "reset-token-here",
                "new_password": "miNuevaContraseñaSegura123"
            }
        }


class PasswordChange(BaseModel):
    """Schema para cambio de contraseña"""
    current_password: str = Field(..., description="Contraseña actual")
    new_password: str = Field(
        ..., 
        min_length=8, 
        max_length=128,
        description="Nueva contraseña"
    )
    
    @validator('new_password')
    def validate_new_password(cls, v, values):
        """Validar nueva contraseña"""
        if 'current_password' in values and v == values['current_password']:
            raise ValueError('La nueva contraseña debe ser diferente a la actual')
        
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        
        has_letter = any(c.isalpha() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not has_letter:
            raise ValueError('La contraseña debe contener al menos una letra')
        if not has_digit:
            raise ValueError('La contraseña debe contener al menos un número')
        
        return v
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "current_password": "miContraseñaActual123",
                "new_password": "miNuevaContraseñaSegura456"
            }
        }


class SessionInfo(BaseModel, TimestampMixin):
    """Schema para información de sesión"""
    session_id: str = Field(..., description="ID de la sesión")
    user_id: str = Field(..., description="ID del usuario")
    ip_address: Optional[str] = Field(None, description="Dirección IP")
    user_agent: Optional[str] = Field(None, description="User Agent")
    is_active: bool = Field(default=True, description="Sesión activa")
    expires_at: datetime = Field(..., description="Fecha de expiración")
    last_activity: Optional[datetime] = Field(None, description="Última actividad")
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "session_id": "sess_123456789",
                "user_id": "user_abcdef123",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0...",
                "is_active": True,
                "expires_at": "2024-01-01T12:00:00Z",
                "last_activity": "2024-01-01T11:30:00Z"
            }
        }


class LogoutRequest(BaseModel):
    """Schema para logout"""
    logout_all_devices: bool = Field(
        default=False, 
        description="Cerrar sesión en todos los dispositivos"
    )
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "logout_all_devices": False
            }
        }


class LoginHistory(BaseModel, TimestampMixin):
    """Schema para historial de login"""
    user_id: str = Field(..., description="ID del usuario")
    ip_address: Optional[str] = Field(None, description="Dirección IP")
    user_agent: Optional[str] = Field(None, description="User Agent")
    success: bool = Field(..., description="Login exitoso")
    failure_reason: Optional[str] = Field(None, description="Razón de falla")
    location: Optional[str] = Field(None, description="Ubicación aproximada")
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "user_id": "user_abcdef123",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0...",
                "success": True,
                "failure_reason": None,
                "location": "Lima, Peru"
            }
        }


class TwoFactorSetup(BaseModel):
    """Schema para configuración de 2FA"""
    enable: bool = Field(..., description="Habilitar/deshabilitar 2FA")
    method: str = Field(
        default="totp", 
        regex="^(totp|sms|email)$",
        description="Método de 2FA"
    )
    phone: Optional[str] = Field(None, description="Teléfono para SMS")
    backup_codes: Optional[list] = Field(None, description="Códigos de respaldo")
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "enable": True,
                "method": "totp",
                "phone": "+51987654321",
                "backup_codes": ["123456", "789012", "345678"]
            }
        }


class TwoFactorVerify(BaseModel):
    """Schema para verificación de 2FA"""
    code: str = Field(
        ..., 
        min_length=6, 
        max_length=8,
        description="Código de verificación"
    )
    remember_device: bool = Field(
        default=False,
        description="Recordar este dispositivo"
    )
    
    @validator('code')
    def validate_code(cls, v):
        """Validar código de verificación"""
        if not v.isdigit():
            raise ValueError('El código debe contener solo números')
        return v
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "code": "123456",
                "remember_device": False
            }
        }


class AuthChallenge(BaseModel):
    """Schema para desafío de autenticación"""
    challenge_type: str = Field(..., description="Tipo de desafío")
    challenge_data: dict = Field(..., description="Datos del desafío")
    expires_in: int = Field(..., description="Expiración en segundos")
    
    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "challenge_type": "2fa_required",
                "challenge_data": {
                    "methods": ["totp", "backup_code"],
                    "qr_code": "data:image/png;base64,..."
                },
                "expires_in": 300
            }
        }
