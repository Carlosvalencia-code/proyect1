"""
Endpoints de autenticación para Synthia Style API
Maneja registro, login, logout y gestión de tokens
"""

from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer

from app.schemas.auth import (
    UserRegister, UserLogin, Token, RefreshToken, PasswordChange,
    PasswordReset, PasswordResetConfirm, LogoutRequest
)
from app.schemas.common import APIResponse
from app.schemas.user import UserResponse
from app.core.security import (
    PasswordManager, TokenManager, SecurityLogger,
    get_current_user_id
)
from app.db.database import get_db
from app.core.logging import SecurityLogger

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=APIResponse)
async def register_user(
    user_data: UserRegister,
    request: Request,
    db=Depends(get_db)
) -> APIResponse:
    """
    Registrar nuevo usuario
    """
    try:
        # Verificar si el email ya existe
        existing_user = await db.user.find_unique(
            where={"email": user_data.email}
        )
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )
        
        # Hash de la contraseña
        hashed_password = PasswordManager.hash_password(user_data.password)
        
        # Crear usuario en la base de datos
        new_user = await db.user.create(
            data={
                "email": user_data.email,
                "password": hashed_password,
                "firstName": user_data.first_name,
                "lastName": user_data.last_name,
                "isActive": True
            }
        )
        
        # Crear preferencias por defecto
        await db.userpreferences.create(
            data={
                "userId": new_user.id,
                "emailNotifications": True,
                "pushNotifications": True,
                "shareAnalytics": False,
                "profileVisibility": "private"
            }
        )
        
        # Log de registro exitoso
        SecurityLogger.log_authentication(
            user_id=new_user.id,
            success=True,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        return APIResponse(
            message="Usuario registrado exitosamente",
            data={
                "user_id": new_user.id,
                "email": new_user.email
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Log de error
        SecurityLogger.log_authentication(
            user_id=user_data.email,
            success=False,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/login", response_model=Token)
async def login_user(
    user_data: UserLogin,
    request: Request,
    db=Depends(get_db)
) -> Token:
    """
    Iniciar sesión de usuario
    """
    try:
        # Buscar usuario por email
        user = await db.user.find_unique(
            where={"email": user_data.email},
            include={"preferences": True}
        )
        
        # Verificar si el usuario existe y está activo
        if not user or not user.isActive:
            SecurityLogger.log_authentication(
                user_id=user_data.email,
                success=False,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas"
            )
        
        # Verificar contraseña
        if not PasswordManager.verify_password(user_data.password, user.password):
            SecurityLogger.log_authentication(
                user_id=user.id,
                success=False,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas"
            )
        
        # Generar tokens
        access_token = TokenManager.create_access_token(
            data={"sub": user.id, "email": user.email}
        )
        refresh_token = TokenManager.create_refresh_token(user.id)
        
        # Crear sesión en la base de datos
        session_data = {
            "userId": user.id,
            "token": refresh_token,
            "expiresAt": datetime.utcnow() + timedelta(days=7),
            "isActive": True,
            "userAgent": request.headers.get("user-agent"),
            "ipAddress": request.client.host if request.client else None
        }
        
        await db.usersession.create(data=session_data)
        
        # Log de login exitoso
        SecurityLogger.log_authentication(
            user_id=user.id,
            success=True,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=1800  # 30 minutos
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshToken,
    db=Depends(get_db)
) -> Token:
    """
    Renovar token de acceso usando refresh token
    """
    try:
        # Verificar refresh token
        payload = TokenManager.verify_token(refresh_data.refresh_token, "refresh")
        user_id = payload.get("sub")
        
        # Verificar que la sesión existe y está activa
        session = await db.usersession.find_first(
            where={
                "token": refresh_data.refresh_token,
                "userId": user_id,
                "isActive": True,
                "expiresAt": {"gte": datetime.utcnow()}
            }
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido o expirado"
            )
        
        # Buscar usuario
        user = await db.user.find_unique(
            where={"id": user_id}
        )
        
        if not user or not user.isActive:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario inválido"
            )
        
        # Generar nuevo access token
        new_access_token = TokenManager.create_access_token(
            data={"sub": user.id, "email": user.email}
        )
        
        return Token(
            access_token=new_access_token,
            refresh_token=refresh_data.refresh_token,  # Mantener el mismo refresh token
            token_type="bearer",
            expires_in=1800
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error renovando token"
        )


@router.post("/logout", response_model=APIResponse)
async def logout_user(
    logout_data: LogoutRequest,
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
) -> APIResponse:
    """
    Cerrar sesión de usuario
    """
    try:
        if logout_data.logout_all_devices:
            # Desactivar todas las sesiones del usuario
            await db.usersession.update_many(
                where={"userId": current_user_id},
                data={"isActive": False}
            )
            message = "Sesión cerrada en todos los dispositivos"
        else:
            # Desactivar solo la sesión actual (requeriría token específico)
            # Por simplicidad, desactivamos la más reciente
            recent_session = await db.usersession.find_first(
                where={"userId": current_user_id, "isActive": True},
                order={"createdAt": "desc"}
            )
            
            if recent_session:
                await db.usersession.update(
                    where={"id": recent_session.id},
                    data={"isActive": False}
                )
            
            message = "Sesión cerrada exitosamente"
        
        return APIResponse(message=message)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error cerrando sesión"
        )


@router.post("/change-password", response_model=APIResponse)
async def change_password(
    password_data: PasswordChange,
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
) -> APIResponse:
    """
    Cambiar contraseña del usuario autenticado
    """
    try:
        # Buscar usuario actual
        user = await db.user.find_unique(
            where={"id": current_user_id}
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Verificar contraseña actual
        if not PasswordManager.verify_password(password_data.current_password, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contraseña actual incorrecta"
            )
        
        # Hash de la nueva contraseña
        new_hashed_password = PasswordManager.hash_password(password_data.new_password)
        
        # Actualizar contraseña en la base de datos
        await db.user.update(
            where={"id": current_user_id},
            data={"password": new_hashed_password}
        )
        
        # Invalidar todas las sesiones para forzar re-login
        await db.usersession.update_many(
            where={"userId": current_user_id},
            data={"isActive": False}
        )
        
        return APIResponse(message="Contraseña cambiada exitosamente")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error cambiando contraseña"
        )


@router.post("/forgot-password", response_model=APIResponse)
async def forgot_password(
    reset_data: PasswordReset,
    db=Depends(get_db)
) -> APIResponse:
    """
    Solicitar reset de contraseña
    """
    try:
        # Verificar si el usuario existe
        user = await db.user.find_unique(
            where={"email": reset_data.email}
        )
        
        # Por seguridad, siempre retornamos éxito aunque el email no exista
        if user:
            # Generar token de reset (en producción, enviar por email)
            reset_token = TokenManager.create_access_token(
                data={"sub": user.id, "type": "password_reset"},
                expires_delta=timedelta(hours=1)  # Expira en 1 hora
            )
            
            # TODO: Enviar email con el token de reset
            # EmailService.send_password_reset_email(user.email, reset_token)
        
        return APIResponse(
            message="Si el email existe, recibirás instrucciones para resetear tu contraseña"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error procesando solicitud"
        )


@router.post("/reset-password", response_model=APIResponse)
async def reset_password(
    reset_data: PasswordResetConfirm,
    db=Depends(get_db)
) -> APIResponse:
    """
    Confirmar reset de contraseña con token
    """
    try:
        # Verificar token de reset
        try:
            payload = TokenManager.verify_token(reset_data.token, "access")
            if payload.get("type") != "password_reset":
                raise ValueError("Token inválido")
            user_id = payload.get("sub")
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token de reset inválido o expirado"
            )
        
        # Buscar usuario
        user = await db.user.find_unique(
            where={"id": user_id}
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Hash de la nueva contraseña
        new_hashed_password = PasswordManager.hash_password(reset_data.new_password)
        
        # Actualizar contraseña
        await db.user.update(
            where={"id": user_id},
            data={"password": new_hashed_password}
        )
        
        # Invalidar todas las sesiones
        await db.usersession.update_many(
            where={"userId": user_id},
            data={"isActive": False}
        )
        
        return APIResponse(message="Contraseña restablecida exitosamente")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error restableciendo contraseña"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
) -> UserResponse:
    """
    Obtener información del usuario autenticado
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
        
        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.firstName,
            last_name=user.lastName,
            is_active=user.isActive,
            created_at=user.createdAt,
            updated_at=user.updatedAt,
            preferences=user.preferences
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo información del usuario"
        )


@router.get("/sessions", response_model=APIResponse)
async def get_user_sessions(
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
) -> APIResponse:
    """
    Obtener sesiones activas del usuario
    """
    try:
        sessions = await db.usersession.find_many(
            where={
                "userId": current_user_id,
                "isActive": True,
                "expiresAt": {"gte": datetime.utcnow()}
            },
            order={"createdAt": "desc"}
        )
        
        session_data = [
            {
                "id": session.id,
                "created_at": session.createdAt,
                "expires_at": session.expiresAt,
                "ip_address": session.ipAddress,
                "user_agent": session.userAgent
            }
            for session in sessions
        ]
        
        return APIResponse(
            message="Sesiones obtenidas exitosamente",
            data={"sessions": session_data}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo sesiones"
        )
