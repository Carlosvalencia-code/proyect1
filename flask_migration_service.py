# =============================================================================
# SYNTHIA STYLE - SERVICIO DE MIGRACIÓN DE FLASK
# =============================================================================
# Servicio que encapsula toda la lógica migrada del código Flask original

import os
import json
import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from PIL import Image
import io
import base64

from app.core.config import get_settings
from app.services.gemini_service import GeminiService
from app.services.cache_service import CacheService
from app.schemas.flask_migration import (
    FaceShape, ColorSeason, SkinUndertone,
    FacialAnalysisResult, ChromaticAnalysisResult,
    ChromaticQuizAnswers, UserSession,
    FacialRecommendations, HaircutRecommendation,
    GlassesRecommendation, NecklineRecommendation,
    ColorRecommendation
)

logger = logging.getLogger(__name__)
settings = get_settings()

class FlaskMigrationService:
    """
    Servicio que contiene toda la lógica migrada del código Flask original
    """
    
    def __init__(self, gemini_service: GeminiService, cache_service: CacheService):
        self.gemini_service = gemini_service
        self.cache_service = cache_service
        
        # Base de datos en memoria para compatibilidad (como en Flask original)
        # En producción, esto se movería a PostgreSQL
        self.users_db: Dict[str, Dict] = {}
        self.sessions_db: Dict[str, UserSession] = {}
        
        # Cache TTL para análisis
        self.analysis_cache_ttl = 86400  # 24 horas
        
        # Inicializar recomendaciones estáticas
        self.recommendations_db = self._initialize_recommendations_db()
    
    def _initialize_recommendations_db(self) -> Dict[str, Any]:
        """
        Inicializa la base de datos de recomendaciones (migrada de Flask)
        """
        return {
            "facial_shapes": {
                "ovalado": {
                    "descripcion": "Considerada la forma facial más equilibrada y versátil",
                    "recomendaciones": {
                        "cortes_pelo": [
                            {
                                "nombre": "Bob clásico",
                                "descripcion": "Corte recto a la altura de la mandíbula",
                                "explicacion": "Enmarca el rostro resaltando los pómulos sin modificar las proporciones naturales"
                            },
                            {
                                "nombre": "Largo con capas",
                                "descripcion": "Pelo largo con capas suaves desde la barbilla",
                                "explicacion": "Añade movimiento manteniendo la armonía natural del rostro ovalado"
                            },
                            {
                                "nombre": "Pixie elegante",
                                "descripcion": "Corte muy corto con textura",
                                "explicacion": "Resalta los rasgos equilibrados sin competir con la forma natural"
                            }
                        ],
                        "gafas": [
                            {
                                "tipo": "Wayfarer",
                                "explicacion": "Su forma equilibrada complementa la simetría del rostro ovalado"
                            },
                            {
                                "tipo": "Aviador",
                                "explicacion": "La forma ligeramente angular contrasta sutilmente con las curvas del rostro"
                            }
                        ],
                        "escotes": [
                            {
                                "tipo": "V profunda",
                                "explicacion": "Alarga visualmente el rostro y destaca el cuello"
                            },
                            {
                                "tipo": "Barco",
                                "explicacion": "Ensancha visualmente los hombros, equilibrando las proporciones"
                            }
                        ]
                    }
                },
                "redondo": {
                    "descripcion": "Rostro con anchura y longitud similares, con mejillas redondeadas",
                    "recomendaciones": {
                        "cortes_pelo": [
                            {
                                "nombre": "Pixie asimétrico",
                                "descripcion": "Corto en los lados y más largo en la parte superior",
                                "explicacion": "Añade ángulos y alarga visualmente el rostro"
                            },
                            {
                                "nombre": "Largo con capas y flequillo lateral",
                                "descripcion": "Pelo por debajo de los hombros con capas desde la barbilla",
                                "explicacion": "Las capas crean líneas verticales que estilizan el rostro"
                            },
                            {
                                "nombre": "Bob asimétrico",
                                "descripcion": "Bob más largo de un lado que del otro",
                                "explicacion": "Rompe la simetría del rostro redondo añadiendo dinamismo"
                            }
                        ],
                        "gafas": [
                            {
                                "tipo": "Rectangulares",
                                "explicacion": "Los ángulos contrastan con la redondez, añadiendo definición"
                            },
                            {
                                "tipo": "Cuadradas",
                                "explicacion": "Añaden estructura y equilibran la suavidad del rostro redondo"
                            }
                        ],
                        "escotes": [
                            {
                                "tipo": "V",
                                "explicacion": "Crea una línea vertical que alarga visualmente el rostro"
                            },
                            {
                                "tipo": "Asimétrico",
                                "explicacion": "Rompe la simetría del rostro redondo, añadiendo dinamismo"
                            }
                        ]
                    }
                },
                "cuadrado": {
                    "descripcion": "Rostro con mandíbula prominente y frente amplia, líneas angulares",
                    "recomendaciones": {
                        "cortes_pelo": [
                            {
                                "nombre": "Ondas suaves por debajo de los hombros",
                                "descripcion": "Pelo largo con ondas naturales",
                                "explicacion": "Suaviza los ángulos del rostro con curvas naturales"
                            },
                            {
                                "nombre": "Bob redondeado",
                                "descripcion": "Bob con líneas curvas y volumen en las puntas",
                                "explicacion": "Contrarresta la angularidad con formas suaves"
                            }
                        ],
                        "gafas": [
                            {
                                "tipo": "Redondas",
                                "explicacion": "Suavizan los ángulos marcados del rostro cuadrado"
                            },
                            {
                                "tipo": "Ovaladas",
                                "explicacion": "Añaden suavidad y contrastan con la estructura angular"
                            }
                        ],
                        "escotes": [
                            {
                                "tipo": "Redondo",
                                "explicacion": "Suaviza la línea de la mandíbula con curvas"
                            },
                            {
                                "tipo": "V suave",
                                "explicacion": "Crea un punto focal que alarga el rostro"
                            }
                        ]
                    }
                }
            },
            "color_seasons": {
                "invierno": {
                    "descripcion": "Colores intensos y contrastantes que complementan tonos fríos",
                    "colores_favorables": [
                        {
                            "color": "Negro intenso",
                            "codigo_hex": "#000000",
                            "explicacion": "Color característico que realza la intensidad natural"
                        },
                        {
                            "color": "Blanco puro",
                            "codigo_hex": "#FFFFFF",
                            "explicacion": "Contraste perfecto que aporta luminosidad"
                        },
                        {
                            "color": "Rojo verdadero",
                            "codigo_hex": "#FF0000",
                            "explicacion": "Color vibrante que complementa la intensidad del invierno"
                        },
                        {
                            "color": "Azul eléctrico",
                            "codigo_hex": "#0066FF",
                            "explicacion": "Azul puro que realza los subtonos fríos"
                        },
                        {
                            "color": "Fucsia",
                            "codigo_hex": "#FF00FF",
                            "explicacion": "Color intenso que aporta energía y vitalidad"
                        }
                    ],
                    "colores_evitar": [
                        {
                            "color": "Beige cálido",
                            "explicacion": "Puede hacer que la piel parezca apagada"
                        },
                        {
                            "color": "Naranja",
                            "explicacion": "Choca con los subtonos fríos naturales"
                        },
                        {
                            "color": "Amarillo dorado",
                            "explicacion": "Puede crear un efecto amarillento poco favorecedor"
                        }
                    ]
                },
                "verano": {
                    "descripcion": "Colores suaves y apagados con subtonos fríos",
                    "colores_favorables": [
                        {
                            "color": "Rosa polvos",
                            "codigo_hex": "#F8BBD0",
                            "explicacion": "Aporta luminosidad y frescura a tu rostro"
                        },
                        {
                            "color": "Gris perla",
                            "codigo_hex": "#C0C0C0",
                            "explicacion": "Neutral que armoniza perfectamente con tu coloración"
                        },
                        {
                            "color": "Azul marino suave",
                            "codigo_hex": "#000080",
                            "explicacion": "Alternativa suavizada al negro que no resulta demasiado contrastante"
                        },
                        {
                            "color": "Malva",
                            "codigo_hex": "#E0B0FF",
                            "explicacion": "Realza el subtono rosado natural de tu piel"
                        },
                        {
                            "color": "Verde menta",
                            "codigo_hex": "#98FB98",
                            "explicacion": "Color fresco que complementa los tonos suaves"
                        }
                    ],
                    "colores_evitar": [
                        {
                            "color": "Naranja brillante",
                            "explicacion": "Demasiado intenso, puede hacer que tu piel parezca apagada"
                        },
                        {
                            "color": "Negro intenso",
                            "explicacion": "Puede resultar demasiado contrastante y crear un efecto duro"
                        },
                        {
                            "color": "Amarillo mostaza",
                            "explicacion": "Puede crear un efecto amarillento o verdoso en la piel"
                        }
                    ]
                }
            }
        }
    
    async def create_user_session(self, email: str, full_name: Optional[str] = None) -> str:
        """
        Crea una nueva sesión de usuario (migrado de Flask login)
        """
        user_id = str(uuid.uuid4())
        
        # Crear usuario en "base de datos"
        self.users_db[user_id] = {
            'email': email,
            'full_name': full_name,
            'created_at': datetime.now().isoformat(),
            'analysis_results': {},
            'feedback': []
        }
        
        # Crear sesión
        session = UserSession(
            user_id=user_id,
            email=email,
            created_at=datetime.now(),
            analysis_results={},
            feedback=[]
        )
        
        self.sessions_db[user_id] = session
        
        logger.info(f"Created new user session for {email}")
        return user_id
    
    async def get_user_session(self, user_id: str) -> Optional[UserSession]:
        """
        Obtiene datos de sesión del usuario
        """
        return self.sessions_db.get(user_id)
    
    async def get_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos del usuario de la "base de datos"
        """
        return self.users_db.get(user_id)
    
    async def analyze_face_with_gemini(self, image_base64: str) -> FacialAnalysisResult:
        """
        Analiza una imagen facial usando Gemini API (migrado de Flask)
        """
        try:
            # Cache key para evitar análisis duplicados
            image_hash = hash(image_base64[:100])  # Hash de los primeros 100 chars
            cache_key = f"facial_analysis:{image_hash}"
            
            # Verificar cache
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                logger.info("Returning cached facial analysis result")
                return FacialAnalysisResult(**cached_result)
            
            # Prompt mejorado para Gemini
            prompt = """
            Actúa como un experto en análisis facial y asesoría de imagen. Analiza la imagen proporcionada y determina:
            1. La forma del rostro (ovalado, redondo, cuadrado, rectangular, corazón, diamante o triangular)
            2. Características faciales destacadas (pómulos, mandíbula, frente)
            3. Proporciones faciales generales

            Responde en formato JSON con la siguiente estructura:
            {
              "forma_rostro": "tipo",
              "caracteristicas_destacadas": ["rasgo1", "rasgo2"],
              "proporciones": "descripción",
              "confianza_analisis": porcentaje
            }
            """
            
            # Llamar a Gemini
            gemini_result = await self.gemini_service.analyze_image(
                image_base64=image_base64,
                prompt=prompt
            )
            
            if not gemini_result:
                raise Exception("No response from Gemini API")
            
            # Procesar respuesta de Gemini
            face_shape_str = gemini_result.get('forma_rostro', 'ovalado').lower()
            face_shape = self._normalize_face_shape(face_shape_str)
            
            # Obtener recomendaciones
            recommendations = self._get_facial_recommendations(face_shape)
            
            # Crear resultado estructurado
            result = FacialAnalysisResult(
                forma_rostro=face_shape,
                caracteristicas_destacadas=gemini_result.get('caracteristicas_destacadas', []),
                proporciones=gemini_result.get('proporciones', 'Proporciones equilibradas'),
                confianza_analisis=int(gemini_result.get('confianza_analisis', 85)),
                recomendaciones=recommendations
            )
            
            # Guardar en cache
            await self.cache_service.set(
                cache_key, 
                result.dict(), 
                ttl=self.analysis_cache_ttl
            )
            
            logger.info(f"Facial analysis completed with shape: {face_shape}")
            return result
            
        except Exception as e:
            logger.error(f"Error in facial analysis: {e}")
            # Fallback como en Flask original
            return FacialAnalysisResult(
                forma_rostro=FaceShape.OVALADO,
                caracteristicas_destacadas=["pómulos definidos", "mandíbula suave"],
                proporciones="equilibradas",
                confianza_analisis=85,
                recomendaciones=self._get_facial_recommendations(FaceShape.OVALADO)
            )
    
    def _normalize_face_shape(self, face_shape_str: str) -> FaceShape:
        """
        Normaliza la forma facial desde string a enum (migrado de Flask)
        """
        shape_mapping = {
            "rectangular": FaceShape.CUADRADO,
            "diamante": FaceShape.OVALADO,
            "triangular": FaceShape.CORAZON,
            "corazón": FaceShape.OVALADO,
            "triangulo_invertido": FaceShape.CORAZON
        }
        
        # Intentar mapeo directo primero
        try:
            return FaceShape(face_shape_str)
        except ValueError:
            # Usar mapeo de compatibilidad
            return shape_mapping.get(face_shape_str, FaceShape.OVALADO)
    
    def _get_facial_recommendations(self, face_shape: FaceShape) -> FacialRecommendations:
        """
        Obtiene recomendaciones faciales basadas en la forma (migrado de Flask)
        """
        shape_data = self.recommendations_db["facial_shapes"].get(
            face_shape.value, 
            self.recommendations_db["facial_shapes"]["ovalado"]
        )
        
        rec_data = shape_data.get("recomendaciones", {})
        
        # Convertir a schemas estructurados
        cortes_pelo = [
            HaircutRecommendation(**haircut) 
            for haircut in rec_data.get("cortes_pelo", [])
        ]
        
        gafas = [
            GlassesRecommendation(**glasses)
            for glasses in rec_data.get("gafas", [])
        ]
        
        escotes = [
            NecklineRecommendation(**neckline)
            for neckline in rec_data.get("escotes", [])
        ]
        
        return FacialRecommendations(
            cortes_pelo=cortes_pelo,
            gafas=gafas,
            escotes=escotes
        )
    
    async def analyze_chromatic_quiz(self, quiz_answers: ChromaticQuizAnswers) -> ChromaticAnalysisResult:
        """
        Analiza respuestas del quiz cromático (migrado de Flask)
        """
        try:
            # Cache key basado en las respuestas
            answers_hash = hash(str(quiz_answers.dict()))
            cache_key = f"chromatic_analysis:{answers_hash}"
            
            # Verificar cache
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                logger.info("Returning cached chromatic analysis result")
                return ChromaticAnalysisResult(**cached_result)
            
            # Algoritmo simplificado (migrado de Flask)
            season = self._determine_color_season(quiz_answers)
            
            # Obtener recomendaciones de color
            season_data = self.recommendations_db["color_seasons"].get(
                season.value,
                self.recommendations_db["color_seasons"]["invierno"]
            )
            
            # Determinar subtono
            subtono = self._determine_undertone(quiz_answers)
            
            # Crear recomendaciones estructuradas
            paleta_primaria = [
                ColorRecommendation(**color)
                for color in season_data.get("colores_favorables", [])
            ]
            
            colores_evitar = [
                ColorRecommendation(
                    color=color.get("color", "Color desconocido"),
                    codigo_hex="#000000",  # Default hex
                    explicacion=color.get("explicacion", "No recomendado para tu estación")
                )
                for color in season_data.get("colores_evitar", [])
            ]
            
            result = ChromaticAnalysisResult(
                estacion=season,
                subtono=subtono,
                confianza_analisis=self._calculate_confidence(quiz_answers),
                descripcion=season_data.get("descripcion", "Análisis cromático personalizado"),
                paleta_primaria=paleta_primaria,
                colores_evitar=colores_evitar
            )
            
            # Guardar en cache
            await self.cache_service.set(
                cache_key,
                result.dict(),
                ttl=self.analysis_cache_ttl
            )
            
            logger.info(f"Chromatic analysis completed with season: {season}")
            return result
            
        except Exception as e:
            logger.error(f"Error in chromatic analysis: {e}")
            # Fallback
            return ChromaticAnalysisResult(
                estacion=ColorSeason.INVIERNO,
                subtono=SkinUndertone.FRIO,
                confianza_analisis=75,
                descripcion="Análisis cromático con configuración por defecto",
                paleta_primaria=[],
                colores_evitar=[]
            )
    
    def _determine_color_season(self, quiz_answers: ChromaticQuizAnswers) -> ColorSeason:
        """
        Determina la estación de color basada en respuestas (migrado de Flask)
        """
        # Lógica migrada del Flask original
        if quiz_answers.vein_color == 'green' and quiz_answers.sun_reaction == 'tan':
            season = ColorSeason.OTONO
        elif quiz_answers.vein_color == 'blue' and quiz_answers.sun_reaction == 'burn':
            season = ColorSeason.INVIERNO
        elif quiz_answers.vein_color == 'blue' and quiz_answers.sun_reaction == 'tan':
            season = ColorSeason.VERANO
        elif quiz_answers.vein_color == 'both':
            season = ColorSeason.PRIMAVERA
        else:
            season = ColorSeason.INVIERNO  # Default
        
        # Ajustar basado en preferencias de joyería
        if quiz_answers.jewelry == 'gold' and season in [ColorSeason.INVIERNO, ColorSeason.VERANO]:
            season = ColorSeason.PRIMAVERA if season == ColorSeason.INVIERNO else ColorSeason.OTONO
        
        return season
    
    def _determine_undertone(self, quiz_answers: ChromaticQuizAnswers) -> SkinUndertone:
        """
        Determina el subtono de piel
        """
        if quiz_answers.vein_color == 'blue':
            return SkinUndertone.FRIO
        elif quiz_answers.vein_color == 'green':
            return SkinUndertone.CALIDO
        else:
            return SkinUndertone.NEUTRO
    
    def _calculate_confidence(self, quiz_answers: ChromaticQuizAnswers) -> int:
        """
        Calcula nivel de confianza del análisis cromático
        """
        confidence = 60  # Base
        
        # Incrementar confianza según consistencia de respuestas
        if quiz_answers.vein_color in ['blue', 'green']:
            confidence += 10
        
        if quiz_answers.sun_reaction in ['burn', 'tan']:
            confidence += 10
        
        if quiz_answers.jewelry in ['gold', 'silver']:
            confidence += 10
        
        if len(quiz_answers.best_colors) >= 3:
            confidence += 10
        
        return min(confidence, 95)  # Máximo 95%
    
    async def save_analysis_result(
        self, 
        user_id: str, 
        analysis_type: str, 
        result: Dict[str, Any]
    ) -> bool:
        """
        Guarda resultado de análisis en sesión del usuario (migrado de Flask)
        """
        try:
            if user_id in self.users_db:
                if 'analysis_results' not in self.users_db[user_id]:
                    self.users_db[user_id]['analysis_results'] = {}
                
                self.users_db[user_id]['analysis_results'][analysis_type] = {
                    'timestamp': datetime.now().isoformat(),
                    'result': result
                }
                
                # También actualizar sesión
                if user_id in self.sessions_db:
                    self.sessions_db[user_id].analysis_results[analysis_type] = result
                
                logger.info(f"Saved {analysis_type} analysis for user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error saving analysis result: {e}")
            return False
    
    async def get_analysis_results(self, user_id: str, analysis_type: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene resultados de análisis guardados
        """
        try:
            user_data = self.users_db.get(user_id, {})
            analysis_results = user_data.get('analysis_results', {})
            return analysis_results.get(analysis_type)
        except Exception as e:
            logger.error(f"Error getting analysis results: {e}")
            return None
    
    async def save_user_feedback(
        self, 
        user_id: str, 
        feedback_data: Dict[str, Any]
    ) -> bool:
        """
        Guarda feedback del usuario (migrado de Flask)
        """
        try:
            if user_id in self.users_db:
                if 'feedback' not in self.users_db[user_id]:
                    self.users_db[user_id]['feedback'] = []
                
                feedback_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'content': feedback_data
                }
                
                self.users_db[user_id]['feedback'].append(feedback_entry)
                
                logger.info(f"Saved feedback for user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error saving feedback: {e}")
            return False
    
    async def logout_user(self, user_id: str) -> bool:
        """
        Cierra sesión del usuario
        """
        try:
            if user_id in self.sessions_db:
                del self.sessions_db[user_id]
                logger.info(f"User {user_id} logged out")
                return True
            return False
        except Exception as e:
            logger.error(f"Error logging out user: {e}")
            return False
