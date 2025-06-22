"""
Servicio de integración con Google Gemini AI con cache Redis
Maneja análisis facial y cromático usando la API de Gemini con optimización de performance
"""

import json
import asyncio
import base64
from typing import Optional, Dict, Any, List
from datetime import datetime

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from PIL import Image
import io

from app.core.config import settings
from app.core.logging import AILogger
from app.schemas.facial_analysis import FaceShapeEnum
from app.schemas.chromatic_analysis import ColorSeasonEnum, SkinUndertoneEnum

# Importación dinámica para evitar dependencias circulares
try:
    from app.services.cache_service import cache_service
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False


class GeminiService:
    """Servicio para interacciones con Google Gemini AI"""
    
    def __init__(self):
        """Inicializar servicio Gemini"""
        self.api_key = settings.GEMINI_API_KEY
        self.facial_model_name = "gemini-2.5-flash"
        self.chromatic_model_name = "gemini-2.5-flash"
        
        # Configurar Gemini
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.facial_model_name)
        else:
            self.model = None
            
        # Configuración de seguridad
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
    
    def _parse_json_response(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Parsear respuesta JSON de Gemini, manejando formato markdown
        """
        if not text:
            return None
        
        # Limpiar texto
        processed_text = text.strip()
        
        # Remover markdown fences si existen
        if processed_text.startswith("```json"):
            processed_text = processed_text[7:]
        if processed_text.startswith("```"):
            processed_text = processed_text[3:]
        if processed_text.endswith("```"):
            processed_text = processed_text[:-3]
        
        processed_text = processed_text.strip()
        
        # Extraer JSON entre llaves
        first_brace = processed_text.find('{')
        last_brace = processed_text.rfind('}')
        
        if first_brace == -1 or last_brace == -1 or last_brace < first_brace:
            raise ValueError("No se encontró estructura JSON válida")
        
        json_str = processed_text[first_brace:last_brace + 1]
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            # Intentar corregir errores comunes
            try:
                # Remover comas finales
                fixed_str = json_str.replace(',}', '}').replace(',]', ']')
                return json.loads(fixed_str)
            except json.JSONDecodeError:
                raise ValueError(f"Error parseando JSON: {str(e)}")
    
    def _validate_image_data(self, image_data: str) -> Image.Image:
        """
        Validar y procesar datos de imagen base64
        """
        try:
            # Decodificar base64
            image_bytes = base64.b64decode(image_data)
            
            # Abrir imagen con PIL
            image = Image.open(io.BytesIO(image_bytes))
            
            # Validar formato
            if image.format not in ['JPEG', 'PNG', 'WEBP']:
                raise ValueError(f"Formato de imagen no soportado: {image.format}")
            
            # Validar dimensiones
            if image.width < 100 or image.height < 100:
                raise ValueError("La imagen es demasiado pequeña (mínimo 100x100)")
            
            if image.width > 4096 or image.height > 4096:
                raise ValueError("La imagen es demasiado grande (máximo 4096x4096)")
            
            # Convertir a RGB si es necesario
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            return image
            
        except Exception as e:
            raise ValueError(f"Error procesando imagen: {str(e)}")
    
    def _generate_facial_analysis_prompt(self) -> str:
        """Generar prompt para análisis facial"""
        return """
Actúa como un experto en análisis facial y asesoría de imagen. Analiza la imagen proporcionada y determina:

1. Forma del rostro: Identifica la forma principal del rostro (ovalado, redondo, cuadrado, rectangular, corazón, diamante o triangular).

2. Características destacadas: Identifica 3-5 características faciales destacadas específicas.

3. Nivel de confianza: Indica tu nivel de confianza en el análisis en una escala del 1 al 100.

Basado en la forma del rostro identificada, proporciona recomendaciones específicas para:
A. Cortes de pelo: 3 estilos que favorezcan esta forma facial, con explicación detallada.
B. Gafas: 2 tipos de monturas que complementen esta forma facial, con explicación.
C. Escotes: 2 tipos de escotes que favorezcan esta forma facial, con explicación.

Responde ÚNICAMENTE con un JSON válido con la siguiente estructura exacta:
{
  "forma_rostro": "forma identificada",
  "caracteristicas_destacadas": ["característica 1", "característica 2", "característica 3"],
  "confianza_analisis": número_del_1_al_100,
  "recomendaciones": {
    "cortes_pelo": [
      {"nombre": "nombre del corte", "descripcion": "descripción breve", "explicacion": "explicación detallada de por qué favorece esta forma"}
    ],
    "gafas": [
      {"tipo": "tipo de montura", "explicacion": "explicación detallada de por qué es adecuada"}
    ],
    "escotes": [
      {"tipo": "tipo de escote", "explicacion": "explicación detallada de por qué favorece"}
    ]
  }
}

IMPORTANTE: Responde SOLO con el JSON, sin texto adicional antes o después.
"""
    
    def _generate_chromatic_analysis_prompt(self, quiz_responses: Dict[str, str]) -> str:
        """Generar prompt para análisis cromático"""
        responses_text = "\n".join([
            f"- {key.replace('_', ' ').title()}: {value}"
            for key, value in quiz_responses.items()
        ])
        
        return f"""
Actúa como un experto en análisis cromático y colorimetría personal. Analiza las siguientes respuestas de un quiz de análisis cromático:

{responses_text}

Basado en estas respuestas, determina:

1. Estación de color: Identifica la estación de color principal (invierno, primavera, verano u otoño).

2. Subtono: Indica si el subtono es frío, cálido o neutro.

3. Nivel de confianza: Indica tu nivel de confianza en el análisis en una escala del 1 al 100.

4. Descripción: Proporciona una breve descripción general de la estación de color identificada.

Proporciona una paleta de colores personalizada con:
A. Paleta primaria: 5 colores que favorezcan esta estación, con nombre, código hexadecimal y explicación.
B. Colores a evitar: 3 colores que no favorezcan esta estación, con explicación.

Responde ÚNICAMENTE con un JSON válido con la siguiente estructura exacta:
{{
  "estacion": "estación identificada",
  "subtono": "frío/cálido/neutro", 
  "confianza_analisis": número_del_1_al_100,
  "descripcion": "descripción general de esta estación de color",
  "paleta_primaria": [
    {{"color": "nombre del color", "codigo_hex": "#RRGGBB", "explicacion": "explicación detallada"}}
  ],
  "colores_evitar": [
    {{"color": "nombre del color", "codigo_hex": "#RRGGBB", "explicacion": "explicación detallada"}}
  ]
}}

IMPORTANTE: Responde SOLO con el JSON, sin texto adicional antes o después.
"""
    
    async def analyze_facial_features(
        self, 
        image_data: str, 
        user_id: str,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Realizar análisis facial usando Gemini AI con cache inteligente
        """
        if not self.model:
            raise ValueError("Servicio Gemini no configurado correctamente")
        
        start_time = datetime.utcnow()
        
        try:
            # Generar hash de la imagen para cache
            image_hash = None
            cached_result = None
            
            if CACHE_AVAILABLE:
                image_hash = await cache_service.create_image_hash(image_data)
                cached_result = await cache_service.get_analysis_cache(image_hash, "facial")
                
                if cached_result:
                    # Cache hit - log y retornar resultado
                    AILogger.log_analysis_request(
                        user_id=user_id,
                        analysis_type="facial",
                        metadata={"cache_hit": True, "preferences": preferences}
                    )
                    
                    # Agregar información de cache al resultado
                    result = cached_result.get("result", cached_result)
                    result["cache_info"] = {
                        "cached": True,
                        "cached_at": cached_result.get("cached_at"),
                        "image_hash": image_hash
                    }
                    
                    return result
            
            # Cache miss - proceder con análisis
            AILogger.log_analysis_request(
                user_id=user_id,
                analysis_type="facial",
                metadata={"cache_hit": False, "preferences": preferences}
            )
            
            # Validar imagen
            image = self._validate_image_data(image_data)
            
            # Generar prompt
            prompt = self._generate_facial_analysis_prompt()
            
            # Realizar consulta a Gemini
            response = await asyncio.to_thread(
                self.model.generate_content,
                [prompt, image],
                safety_settings=self.safety_settings
            )
            
            # Parsear respuesta
            result = self._parse_json_response(response.text)
            
            if not result:
                raise ValueError("Respuesta vacía de Gemini")
            
            # Validar estructura de respuesta
            required_fields = ['forma_rostro', 'caracteristicas_destacadas', 'confianza_analisis']
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Campo requerido faltante: {field}")
            
            # Normalizar forma de rostro
            face_shape = result['forma_rostro'].lower()
            face_shape_mapping = {
                'ovalado': FaceShapeEnum.OVALADO,
                'redondo': FaceShapeEnum.REDONDO,
                'cuadrado': FaceShapeEnum.CUADRADO,
                'rectangular': FaceShapeEnum.RECTANGULAR,
                'corazón': FaceShapeEnum.CORAZÓN,
                'diamante': FaceShapeEnum.DIAMANTE,
                'triangular': FaceShapeEnum.TRIANGULAR
            }
            
            result['forma_rostro'] = face_shape_mapping.get(face_shape, FaceShapeEnum.UNKNOWN)
            
            # Calcular tiempo de respuesta
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds()
            
            # Cachear resultado si está disponible
            if CACHE_AVAILABLE and image_hash:
                cache_success = await cache_service.set_analysis_cache(
                    image_hash, 
                    "facial", 
                    result
                )
                
                # Agregar información de cache al resultado
                result["cache_info"] = {
                    "cached": False,
                    "cache_saved": cache_success,
                    "image_hash": image_hash
                }
            
            # Log de éxito
            AILogger.log_analysis_response(
                user_id=user_id,
                analysis_type="facial",
                success=True,
                response_time=response_time,
                confidence=result.get('confianza_analisis'),
                metadata={"cached": False, "image_hash": image_hash}
            )
            
            return result
            
        except Exception as e:
            # Calcular tiempo de respuesta
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds()
            
            # Log de error
            AILogger.log_analysis_response(
                user_id=user_id,
                analysis_type="facial",
                success=False,
                response_time=response_time,
                error=str(e)
            )
            
            raise
    
    async def analyze_chromatic_profile(
        self, 
        quiz_responses: Dict[str, str], 
        user_id: str,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Realizar análisis cromático usando Gemini AI con cache inteligente
        """
        if not self.model:
            raise ValueError("Servicio Gemini no configurado correctamente")
        
        start_time = datetime.utcnow()
        
        try:
            # Generar hash de las respuestas para cache
            responses_hash = None
            cached_result = None
            
            if CACHE_AVAILABLE:
                # Crear hash basado en respuestas del quiz
                cache_data = {
                    "quiz_responses": quiz_responses,
                    "preferences": preferences or {}
                }
                responses_hash = cache_service.key_generator.create_hash(cache_data)
                cached_result = await cache_service.get_analysis_cache(responses_hash, "chromatic")
                
                if cached_result:
                    # Cache hit - log y retornar resultado
                    AILogger.log_analysis_request(
                        user_id=user_id,
                        analysis_type="chromatic",
                        metadata={"cache_hit": True, "quiz_responses": quiz_responses, "preferences": preferences}
                    )
                    
                    # Agregar información de cache al resultado
                    result = cached_result.get("result", cached_result)
                    result["cache_info"] = {
                        "cached": True,
                        "cached_at": cached_result.get("cached_at"),
                        "responses_hash": responses_hash
                    }
                    
                    return result
            
            # Cache miss - proceder con análisis
            AILogger.log_analysis_request(
                user_id=user_id,
                analysis_type="chromatic",
                metadata={"cache_hit": False, "quiz_responses": quiz_responses, "preferences": preferences}
            )
            
            # Generar prompt
            prompt = self._generate_chromatic_analysis_prompt(quiz_responses)
            
            # Realizar consulta a Gemini
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                safety_settings=self.safety_settings
            )
            
            # Parsear respuesta
            result = self._parse_json_response(response.text)
            
            if not result:
                raise ValueError("Respuesta vacía de Gemini")
            
            # Validar estructura de respuesta
            required_fields = ['estacion', 'subtono', 'confianza_analisis']
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Campo requerido faltante: {field}")
            
            # Normalizar estación y subtono
            season_mapping = {
                'invierno': ColorSeasonEnum.INVIERNO,
                'primavera': ColorSeasonEnum.PRIMAVERA,
                'verano': ColorSeasonEnum.VERANO,
                'otoño': ColorSeasonEnum.OTOÑO
            }
            
            undertone_mapping = {
                'frío': SkinUndertoneEnum.FRIO,
                'cálido': SkinUndertoneEnum.CALIDO,
                'neutro': SkinUndertoneEnum.NEUTRO
            }
            
            season = result['estacion'].lower()
            undertone = result['subtono'].lower()
            
            result['estacion'] = season_mapping.get(season, ColorSeasonEnum.UNKNOWN)
            result['subtono'] = undertone_mapping.get(undertone, SkinUndertoneEnum.UNKNOWN)
            
            # Calcular tiempo de respuesta
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds()
            
            # Cachear resultado si está disponible
            if CACHE_AVAILABLE and responses_hash:
                cache_success = await cache_service.set_analysis_cache(
                    responses_hash, 
                    "chromatic", 
                    result
                )
                
                # Agregar información de cache al resultado
                result["cache_info"] = {
                    "cached": False,
                    "cache_saved": cache_success,
                    "responses_hash": responses_hash
                }
            
            # Log de éxito
            AILogger.log_analysis_response(
                user_id=user_id,
                analysis_type="chromatic",
                success=True,
                response_time=response_time,
                confidence=result.get('confianza_analisis'),
                metadata={"cached": False, "responses_hash": responses_hash}
            )
            
            return result
            
        except Exception as e:
            # Calcular tiempo de respuesta
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds()
            
            # Log de error
            AILogger.log_analysis_response(
                user_id=user_id,
                analysis_type="chromatic",
                success=False,
                response_time=response_time,
                error=str(e)
            )
            
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Verificar salud del servicio Gemini
        """
        try:
            if not self.model:
                return {
                    "status": "error",
                    "message": "Gemini no configurado"
                }
            
            # Test simple
            start_time = datetime.utcnow()
            response = await asyncio.to_thread(
                self.model.generate_content,
                "Responde solo 'OK'",
                safety_settings=self.safety_settings
            )
            end_time = datetime.utcnow()
            
            response_time = (end_time - start_time).total_seconds() * 1000
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "message": "Servicio Gemini funcionando correctamente"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error en servicio Gemini: {str(e)}"
            }
    
    def get_service_info(self) -> Dict[str, Any]:
        """Obtener información del servicio"""
        return {
            "service": "Google Gemini AI",
            "facial_model": self.facial_model_name,
            "chromatic_model": self.chromatic_model_name,
            "configured": self.model is not None,
            "safety_settings_enabled": True
        }


# Instancia global del servicio
gemini_service = GeminiService()
