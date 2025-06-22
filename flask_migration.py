# =============================================================================
# SYNTHIA STYLE - ENDPOINTS DE MIGRACIÓN DE FLASK
# =============================================================================
# Endpoints que migran exactamente la funcionalidad del código Flask original

import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
import logging

from fastapi import (
    APIRouter, 
    Depends, 
    HTTPException, 
    status, 
    Request, 
    Response,
    File,
    UploadFile,
    Form
)
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.config import get_settings
from app.schemas.flask_migration import (
    UserLogin, UserSignup, UserResponse, LoginResponse, LogoutResponse,
    FacialAnalysisRequest, FacialAnalysisResponse, FacialAnalysisResult,
    ChromaticQuizAnswers, ChromaticAnalysisResponse, ChromaticAnalysisResult,
    FeedbackSubmission, FeedbackResponse, DashboardResponse, DashboardData,
    AnalysisHistory, FlaskMigrationInfo, HealthCheck,
    ReactFacialAnalysisData, ReactChromaticAnalysisData
)
from app.schemas.common import ResponseModel
from app.services.flask_migration_service import FlaskMigrationService
from app.services.gemini_service import GeminiService
from app.services.cache_service import CacheService
import base64
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()

# Instanciar servicios (en producción usar dependency injection)
cache_service = CacheService()
gemini_service = GeminiService()
flask_service = FlaskMigrationService(gemini_service, cache_service)

# Configuración de archivos (migrada de Flask)
UPLOAD_FOLDER = settings.upload_path
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename: str) -> bool:
    """Verifica si el archivo tiene extensión permitida (migrado de Flask)"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# =============================================================================
# ENDPOINTS DE AUTENTICACIÓN (MIGRADOS DE FLASK)
# =============================================================================

@router.post("/auth/login", response_model=LoginResponse)
async def login(
    user_data: UserLogin,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Login de usuario (migrado de Flask /login)
    Crea sesión como en Flask original
    """
    try:
        logger.info(f"Login attempt for email: {user_data.email}")
        
        # Crear sesión de usuario (como en Flask)
        user_id = await flask_service.create_user_session(user_data.email)
        
        # Establecer cookie de sesión (compatible con Flask)
        response.set_cookie(
            key="user_id",
            value=user_id,
            max_age=86400 * 7,  # 7 días
            httponly=True,
            secure=settings.is_production,
            samesite="lax"
        )
        
        # Respuesta compatible
        user_response = UserResponse(
            id=user_id,
            email=user_data.email,
            created_at=datetime.now()
        )
        
        return ResponseModel(
            success=True,
            data=user_response,
            message="Login exitoso"
        )
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en el proceso de login"
        )

@router.post("/auth/signup", response_model=LoginResponse)
async def signup(
    user_data: UserSignup,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Registro de usuario (nueva funcionalidad para el frontend React)
    """
    try:
        logger.info(f"Signup attempt for email: {user_data.email}")
        
        # Crear sesión de usuario
        user_id = await flask_service.create_user_session(
            email=user_data.email,
            full_name=user_data.full_name
        )
        
        # Establecer cookie de sesión
        response.set_cookie(
            key="user_id",
            value=user_id,
            max_age=86400 * 7,  # 7 días
            httponly=True,
            secure=settings.is_production,
            samesite="lax"
        )
        
        user_response = UserResponse(
            id=user_id,
            email=user_data.email,
            full_name=user_data.full_name,
            created_at=datetime.now()
        )
        
        return ResponseModel(
            success=True,
            data=user_response,
            message="Registro exitoso"
        )
        
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en el proceso de registro"
        )

@router.post("/auth/logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    response: Response
):
    """
    Logout de usuario (migrado de Flask /logout)
    """
    try:
        # Obtener user_id de la cookie
        user_id = request.cookies.get("user_id")
        
        if user_id:
            await flask_service.logout_user(user_id)
        
        # Limpiar cookie
        response.delete_cookie(key="user_id")
        
        return ResponseModel(
            success=True,
            data={"message": "Logout exitoso"},
            message="Sesión cerrada correctamente"
        )
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en el proceso de logout"
        )

# =============================================================================
# MIDDLEWARE DE AUTENTICACIÓN
# =============================================================================

async def get_current_user_session(request: Request) -> str:
    """
    Obtiene la sesión actual del usuario (migrado de Flask session)
    """
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No hay sesión activa. Por favor inicia sesión."
        )
    
    # Verificar que la sesión existe
    session = await flask_service.get_user_session(user_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión inválida. Por favor inicia sesión nuevamente."
        )
    
    return user_id

# =============================================================================
# ENDPOINTS DE ANÁLISIS FACIAL (MIGRADOS DE FLASK)
# =============================================================================

@router.post("/analysis/facial", response_model=FacialAnalysisResponse)
async def facial_analysis(
    request: FacialAnalysisRequest,
    user_id: str = Depends(get_current_user_session),
    db: AsyncSession = Depends(get_db)
):
    """
    Análisis facial con Gemini API (migrado de Flask /facial-analysis)
    """
    try:
        logger.info(f"Facial analysis request for user {user_id}")
        
        # Realizar análisis con Gemini
        analysis_result = await flask_service.analyze_face_with_gemini(request.image_base64)
        
        # Guardar resultado en sesión del usuario
        await flask_service.save_analysis_result(
            user_id=user_id,
            analysis_type="facial",
            result=analysis_result.dict()
        )
        
        return ResponseModel(
            success=True,
            data=analysis_result,
            message="Análisis facial completado exitosamente"
        )
        
    except Exception as e:
        logger.error(f"Facial analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en el análisis facial"
        )

@router.post("/analysis/facial/upload", response_model=FacialAnalysisResponse)
async def facial_analysis_upload(
    facial_image: UploadFile = File(...),
    user_id: str = Depends(get_current_user_session),
    db: AsyncSession = Depends(get_db)
):
    """
    Análisis facial con upload de archivo (compatible con Flask original)
    """
    try:
        # Verificar archivo
        if not facial_image.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se seleccionó archivo"
            )
        
        if not allowed_file(facial_image.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de archivo no permitido. Use JPG, JPEG o PNG."
            )
        
        # Leer y convertir a base64
        image_data = await facial_image.read()
        if len(image_data) > MAX_CONTENT_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Archivo demasiado grande. Máximo 16MB."
            )
        
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Crear request y procesar
        request = FacialAnalysisRequest(image_base64=image_base64)
        
        # Realizar análisis
        analysis_result = await flask_service.analyze_face_with_gemini(request.image_base64)
        
        # Guardar resultado
        await flask_service.save_analysis_result(
            user_id=user_id,
            analysis_type="facial",
            result=analysis_result.dict()
        )
        
        return ResponseModel(
            success=True,
            data=analysis_result,
            message="Análisis facial completado exitosamente"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Facial analysis upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error procesando la imagen"
        )

@router.get("/analysis/facial/results", response_model=FacialAnalysisResponse)
async def get_facial_results(
    user_id: str = Depends(get_current_user_session)
):
    """
    Obtiene resultados del análisis facial (migrado de Flask /facial-results)
    """
    try:
        # Obtener resultados guardados
        results = await flask_service.get_analysis_results(user_id, "facial")
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontraron resultados de análisis facial"
            )
        
        return ResponseModel(
            success=True,
            data=results.get("result"),
            message="Resultados de análisis facial obtenidos"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting facial results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo resultados"
        )

# =============================================================================
# ENDPOINTS DE ANÁLISIS CROMÁTICO (MIGRADOS DE FLASK)
# =============================================================================

@router.post("/analysis/chromatic", response_model=ChromaticAnalysisResponse)
async def chromatic_analysis(
    quiz_answers: ChromaticQuizAnswers,
    user_id: str = Depends(get_current_user_session),
    db: AsyncSession = Depends(get_db)
):
    """
    Análisis cromático basado en quiz (migrado de Flask /color-analysis)
    """
    try:
        logger.info(f"Chromatic analysis request for user {user_id}")
        
        # Realizar análisis cromático
        analysis_result = await flask_service.analyze_chromatic_quiz(quiz_answers)
        
        # Guardar resultado en sesión del usuario
        await flask_service.save_analysis_result(
            user_id=user_id,
            analysis_type="chromatic",
            result=analysis_result.dict()
        )
        
        return ResponseModel(
            success=True,
            data=analysis_result,
            message="Análisis cromático completado exitosamente"
        )
        
    except Exception as e:
        logger.error(f"Chromatic analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en el análisis cromático"
        )

@router.get("/analysis/chromatic/results", response_model=ChromaticAnalysisResponse)
async def get_chromatic_results(
    user_id: str = Depends(get_current_user_session)
):
    """
    Obtiene resultados del análisis cromático (migrado de Flask /color-results)
    """
    try:
        # Obtener resultados guardados
        results = await flask_service.get_analysis_results(user_id, "chromatic")
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontraron resultados de análisis cromático"
            )
        
        return ResponseModel(
            success=True,
            data=results.get("result"),
            message="Resultados de análisis cromático obtenidos"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chromatic results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo resultados"
        )

# =============================================================================
# ENDPOINTS DE FEEDBACK (MIGRADOS DE FLASK)
# =============================================================================

@router.post("/feedback", response_model=ResponseModel[Dict[str, bool]])
async def submit_feedback(
    feedback: FeedbackSubmission,
    user_id: str = Depends(get_current_user_session)
):
    """
    Envío de feedback (migrado de Flask /feedback)
    """
    try:
        logger.info(f"Feedback submission from user {user_id}")
        
        # Guardar feedback
        success = await flask_service.save_user_feedback(
            user_id=user_id,
            feedback_data=feedback.dict()
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error guardando feedback"
            )
        
        return ResponseModel(
            success=True,
            data={"feedback_saved": True},
            message="Feedback enviado exitosamente"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback submission error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error procesando feedback"
        )

# =============================================================================
# ENDPOINTS DE DASHBOARD (MIGRADOS DE FLASK)
# =============================================================================

@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard(
    user_id: str = Depends(get_current_user_session)
):
    """
    Dashboard del usuario (migrado de Flask /dashboard)
    """
    try:
        # Obtener datos del usuario
        user_data = await flask_service.get_user_data(user_id)
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Construir respuesta del dashboard
        user_response = UserResponse(
            id=user_id,
            email=user_data.get("email", ""),
            full_name=user_data.get("full_name"),
            created_at=datetime.fromisoformat(user_data.get("created_at", datetime.now().isoformat()))
        )
        
        # Obtener historial de análisis
        analysis_results = user_data.get("analysis_results", {})
        history = AnalysisHistory(
            facial_analyses=[analysis_results.get("facial")] if "facial" in analysis_results else [],
            chromatic_analyses=[analysis_results.get("chromatic")] if "chromatic" in analysis_results else [],
            total_analyses=len(analysis_results),
            last_analysis=datetime.now() if analysis_results else None
        )
        
        dashboard_data = DashboardData(
            user=user_response,
            analysis_history=history,
            recent_feedback=user_data.get("feedback", [])[-5:],  # Últimos 5
            recommendations_summary={}
        )
        
        return ResponseModel(
            success=True,
            data=dashboard_data,
            message="Dashboard cargado exitosamente"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error cargando dashboard"
        )

# =============================================================================
# ENDPOINTS DE COMPATIBILIDAD CON FRONTEND REACT
# =============================================================================

@router.get("/analysis/facial/react-format")
async def get_facial_results_react_format(
    user_id: str = Depends(get_current_user_session)
):
    """
    Resultados en formato compatible con types.ts del frontend React
    """
    try:
        results = await flask_service.get_analysis_results(user_id, "facial")
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No facial analysis found"
            )
        
        result_data = results.get("result", {})
        
        # Convertir a formato React
        react_format = ReactFacialAnalysisData(
            forma_rostro=result_data.get("forma_rostro", "ovalado"),
            caracteristicas_destacadas=result_data.get("caracteristicas_destacadas", []),
            confianza_analisis=result_data.get("confianza_analisis", 85),
            recomendaciones={
                "cortes_pelo": [
                    {
                        "nombre": rec.get("nombre", ""),
                        "descripcion": rec.get("descripcion", ""),
                        "explicacion": rec.get("explicacion", "")
                    }
                    for rec in result_data.get("recomendaciones", {}).get("cortes_pelo", [])
                ],
                "gafas": [
                    {
                        "tipo": rec.get("tipo", ""),
                        "explicacion": rec.get("explicacion", "")
                    }
                    for rec in result_data.get("recomendaciones", {}).get("gafas", [])
                ],
                "escotes": [
                    {
                        "tipo": rec.get("tipo", ""),
                        "explicacion": rec.get("explicacion", "")
                    }
                    for rec in result_data.get("recomendaciones", {}).get("escotes", [])
                ]
            }
        )
        
        return react_format
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting React format facial results: {e}")
        raise HTTPException(status_code=500, detail="Error getting results")

@router.get("/analysis/chromatic/react-format")
async def get_chromatic_results_react_format(
    user_id: str = Depends(get_current_user_session)
):
    """
    Resultados cromáticos en formato compatible con types.ts del frontend React
    """
    try:
        results = await flask_service.get_analysis_results(user_id, "chromatic")
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No chromatic analysis found"
            )
        
        result_data = results.get("result", {})
        
        # Convertir a formato React
        react_format = ReactChromaticAnalysisData(
            estacion=result_data.get("estacion", "invierno"),
            subtono=result_data.get("subtono", "frío"),
            descripcion=result_data.get("descripcion", ""),
            confianza_analisis=result_data.get("confianza_analisis", 85),
            paleta_primaria=[
                {
                    "color": color.get("color", ""),
                    "codigo_hex": color.get("codigo_hex", "#000000"),
                    "explicacion": color.get("explicacion", "")
                }
                for color in result_data.get("paleta_primaria", [])
            ],
            colores_evitar=[
                {
                    "color": color.get("color", ""),
                    "codigo_hex": color.get("codigo_hex", "#000000"),
                    "explicacion": color.get("explicacion", "")
                }
                for color in result_data.get("colores_evitar", [])
            ]
        )
        
        return react_format
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting React format chromatic results: {e}")
        raise HTTPException(status_code=500, detail="Error getting results")

# =============================================================================
# ENDPOINTS DE HEALTH CHECK Y MIGRACIÓN
# =============================================================================

@router.get("/health", response_model=HealthCheck)
async def health_check():
    """
    Health check del sistema migrado
    """
    try:
        # Verificar servicios
        database_connected = True  # TODO: implementar check real
        gemini_available = bool(settings.GEMINI_API_KEY)
        
        migration_info = FlaskMigrationInfo(
            original_flask_version="1.0.0",
            fastapi_version="0.104.1",
            migration_date=datetime.now(),
            endpoints_migrated=[
                "/auth/login", "/auth/signup", "/auth/logout",
                "/analysis/facial", "/analysis/chromatic",
                "/feedback", "/dashboard"
            ],
            compatibility_mode=True
        )
        
        return HealthCheck(
            status="healthy",
            timestamp=datetime.now(),
            version="1.0.0",
            database_connected=database_connected,
            gemini_api_available=gemini_available,
            migration_info=migration_info
        )
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return HealthCheck(
            status="unhealthy",
            database_connected=False,
            gemini_api_available=False,
            migration_info=FlaskMigrationInfo()
        )
