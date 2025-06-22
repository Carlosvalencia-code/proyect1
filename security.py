"""
Sistema de seguridad y autenticación para Synthia Style
Maneja autenticación JWT, hashing de contraseñas y validaciones de seguridad
"""

import secrets
from datetime import datetime, timedelta
from typing import Any, Union, Optional

import bcrypt
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.core.logging import SecurityLogger


# Configuración de hash de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuración de JWT
security = HTTPBearer()


class PasswordManager:
    """Gestor de contraseñas con bcrypt"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash de contraseña usando bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verificar contraseña contra hash"""
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'), 
                hashed_password.encode('utf-8')
            )
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def generate_random_password(length: int = 12) -> str:
        """Generar contraseña aleatoria segura"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def validate_password_strength(password: str) -> dict:
        """
        Validar fortaleza de contraseña
        Retorna dict con resultado y mensajes
        """
        errors = []
        
        if len(password) < 8:
            errors.append("La contraseña debe tener al menos 8 caracteres")
        
        if not any(c.islower() for c in password):
            errors.append("La contraseña debe contener al menos una letra minúscula")
        
        if not any(c.isupper() for c in password):
            errors.append("La contraseña debe contener al menos una letra mayúscula")
        
        if not any(c.isdigit() for c in password):
            errors.append("La contraseña debe contener al menos un número")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("La contraseña debe contener al menos un carácter especial")
        
        # Verificar patrones comunes débiles
        weak_patterns = [
            "123456", "password", "qwerty", "abc123", 
            "password123", "admin", "user", "synthia"
        ]
        
        if password.lower() in weak_patterns:
            errors.append("Esta contraseña es demasiado común")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "strength": "strong" if len(errors) == 0 else "weak"
        }


class TokenManager:
    """Gestor de tokens JWT"""
    
    @staticmethod
    def create_access_token(
        data: dict, 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Crear token de acceso JWT"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({"exp": expire})
        to_encode.update({"type": "access"})
        to_encode.update({"iat": datetime.utcnow()})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Crear token de refresh"""
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode = {
            "sub": user_id,
            "exp": expire,
            "type": "refresh",
            "iat": datetime.utcnow()
        }
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> dict:
        """
        Verificar y decodificar token JWT
        Retorna payload si es válido, lanza excepción si no
        """
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            
            # Verificar tipo de token
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Token inválido: tipo esperado {token_type}"
                )
            
            # Verificar expiración
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expirado"
                )
            
            return payload
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token inválido: {str(e)}"
            )
    
    @staticmethod
    def get_user_id_from_token(token: str) -> str:
        """Extraer user_id del token"""
        payload = TokenManager.verify_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: falta user_id"
            )
        
        return user_id


class SessionManager:
    """Gestor de sesiones de usuario"""
    
    @staticmethod
    def generate_session_token() -> str:
        """Generar token de sesión único"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def create_session_data(
        user_id: str,
        user_agent: str = None,
        ip_address: str = None
    ) -> dict:
        """Crear datos de sesión"""
        return {
            "user_id": user_id,
            "token": SessionManager.generate_session_token(),
            "created_at": datetime.utcnow(),
            "user_agent": user_agent,
            "ip_address": ip_address,
            "is_active": True
        }


class SecurityValidator:
    """Validador de seguridad general"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validar formato de email básico"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitizar nombre de archivo"""
        import re
        # Remover caracteres peligrosos
        sanitized = re.sub(r'[^\w\-_\.]', '_', filename)
        # Evitar nombres reservados
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
            'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
            'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        
        name_without_ext = sanitized.rsplit('.', 1)[0]
        if name_without_ext.upper() in reserved_names:
            sanitized = f"file_{sanitized}"
        
        return sanitized
    
    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: list) -> bool:
        """Validar extensión de archivo"""
        if not filename or '.' not in filename:
            return False
        
        extension = filename.rsplit('.', 1)[1].lower()
        return extension in [ext.lower() for ext in allowed_extensions]
    
    @staticmethod
    def check_rate_limit(
        user_id: str, 
        action: str, 
        max_requests: int, 
        time_window: int
    ) -> bool:
        """
        Verificar límite de tasa (rate limiting)
        Implementación básica - en producción usar Redis
        """
        # TODO: Implementar con Redis para persistencia
        # Por ahora retorna True (sin límite)
        return True


class AuthenticationError(Exception):
    """Excepción para errores de autenticación"""
    pass


class AuthorizationError(Exception):
    """Excepción para errores de autorización"""
    pass


# Funciones de utilidad para FastAPI dependencies
def get_current_user_id(credentials: HTTPAuthorizationCredentials = None) -> str:
    """Dependency para obtener user_id del token JWT"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación requerido"
        )
    
    try:
        user_id = TokenManager.get_user_id_from_token(credentials.credentials)
        return user_id
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error de autenticación"
        )


def require_authentication(credentials: HTTPAuthorizationCredentials = security):
    """Dependency que requiere autenticación válida"""
    return get_current_user_id(credentials)


# Configuración de CORS para seguridad
CORS_CONFIG = {
    "allow_origins": settings.CORS_ORIGINS,
    "allow_credentials": settings.CORS_CREDENTIALS,
    "allow_methods": settings.CORS_METHODS,
    "allow_headers": settings.CORS_HEADERS,
}
