from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

class FacialAnalysisRequest(BaseModel):
    # Placeholder if we need any specific fields with the image upload.
    # For now, the image will be handled as UploadFile directly in the endpoint.
    # user_id: Optional[str] = None # Could be injected from auth dependency
    pass

class FacialAnalysisResponse(BaseModel):
    """
    Defines the expected structure of the analysis result returned to the client.
    This should align with the processed JSON from Gemini.
    Example fields (adapt based on actual Gemini output and desired structure):
    """
    analysis_id: str
    summary: str
    face_shape: Optional[str] = None
    skin_tone: Optional[str] = None
    suggested_styles: List[str] = []
    raw_gemini_response: Optional[Dict[str, Any]] = None # For debugging or future use
    # Add more specific fields based on "Desarrollo Final del MVP_ Análisis IA y Consejos Personalizados.md"

class GeminiApiError(BaseModel):
    error_code: Optional[str] = None
    message: str
