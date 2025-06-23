import os
import json # Added import for json.loads
import google.generativeai as genai

# Configure Gemini API
# It's better to handle potential errors during configuration
try:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is not set or is empty.")
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model_instance = genai.GenerativeModel('gemini-1.5-flash-latest')
except (ValueError, Exception) as e: # Catch specific configuration errors if possible
    print(f"CRITICAL: Failed to configure Gemini API or initialize model: {e}")
    # Depending on desired behavior, you might raise the error to stop app startup
    # or set gemini_model_instance to None and handle it in analyze_face_with_gemini.
    gemini_model_instance = None


def get_facial_analysis_prompt() -> str: # Removed image_base64_string as it's not used
    # This is the prompt defined in the strategic documents
    # IMPORTANT: Ensure this prompt consistently makes Gemini return ONLY JSON.
    prompt = f"""
    Eres un asesor de imagen experto y un analista facial altamente preciso.
    Analiza la siguiente imagen facial.

    Realiza las siguientes determinaciones:
    1.  **FORMA_DEL_ROSTRO:** Identifica la forma principal del rostro (Ovalado, Redondo, Cuadrado, Corazón, Diamante, Alargado).
    2.  **CARACTERISTICAS_DESTACADAS:** Describe brevemente 3-5 características faciales prominentes (ej: "Ojos almendrados", "Nariz aguileña", "Labios finos").
    3.  **NIVEL_DE_CONFIANZA_ANALISIS:** En una escala del 1 al 100, indica tu nivel de confianza en el análisis facial general.

    Basado en la FORMA_DEL_ROSTRO, proporciona recomendaciones específicas para Cortes de pelo, Gafas y Escotes.

    IMPORTANTE: Responde ÚNICAMENTE en formato JSON válido, sin texto introductorio ni explicaciones adicionales fuera del JSON.
    La estructura del JSON DEBE SER la siguiente:
    {{
        "forma_rostro": "VALOR_DETECTADO",
        "caracteristicas_destacadas": ["CARACTERISTICA_1", "CARACTERISTICA_2", "CARACTERISTICA_3"],
        "confianza_analisis_facial": VALOR_NUMERICO_ENTRE_1_Y_100,
        "recomendaciones_estilo_facial": {{
            "cortes_pelo": [
                {{"nombre_corte": "Ej: Bob Asimétrico", "descripcion_corte": "Breve descripción del corte.", "explicacion_corte": "Por qué favorece a esta forma de rostro."}},
                {{"nombre_corte": "Ej: Capas Largas", "descripcion_corte": "...", "explicacion_corte": "..."}}
            ],
            "gafas_monturas": [
                {{"tipo_montura": "Ej: Cat-Eye", "explicacion_montura": "Por qué este tipo de montura es adecuado."}},
                {{"tipo_montura": "Ej: Aviador", "explicacion_montura": "..."}}
            ],
            "escotes_prendas": [
                {{"tipo_escote": "Ej: Escote en V", "explicacion_escote": "Por qué este escote complementa la forma del rostro."}},
                {{"tipo_escote": "Ej: Cuello Barco", "explicacion_escote": "..."}}
            ]
        }}
    }}
    Si la imagen no es clara, no es un rostro, o no se puede analizar, responde con:
    {{"error": "No se pudo realizar el análisis facial. Asegúrate de que la imagen sea clara, frontal y de buena calidad."}}
    """
    return prompt.strip()

async def analyze_face_with_gemini(image_bytes: bytes, image_mime_type: str = "image/jpeg"):
    """
    Analyzes an image using Google Gemini API.
    image_mime_type defaults to "image/jpeg" but should be passed from UploadFile.content_type.
    """
    if not gemini_model_instance:
        raise ValueError("Gemini model not initialized. Check API key and configuration.")

    image_part = {
        "mime_type": image_mime_type, # Use the actual mime_type of the uploaded file
        "data": image_bytes
    }

    prompt_text = get_facial_analysis_prompt()

    try:
        # Using await for async call if SDK supports it, otherwise use synchronous version
        # The prompt had model.generate_content_async, so sticking with that.
        response = await gemini_model_instance.generate_content_async([prompt_text, image_part])

        # Robustly extract text content
        try:
            # Standard way to get text from the first candidate's first part
            json_text_content = response.candidates[0].content.parts[0].text
        except (IndexError, AttributeError, TypeError):
            # Fallback if the structure is different or no content/parts
            # Some models might just use response.text directly if not multimodal or no complex parts
            json_text_content = response.text # This might be the case for simpler responses

        json_text = json_text_content.strip()

        # Clean potential markdown formatting for JSON
        if json_text.startswith("```json"):
            json_text = json_text[7:] # Remove ```json\n
            if json_text.endswith("```"): # Remove trailing ```
                json_text = json_text[:-3]
        elif json_text.startswith("```"): # More generic ``` removal
             json_text = json_text[3:]
             if json_text.endswith("```"):
                json_text = json_text[:-3]
        json_text = json_text.strip()

        return json.loads(json_text)

    except json.JSONDecodeError as e:
        print(f"Error parsing Gemini JSON response: {e}")
        print(f"Raw response text was: '{json_text if 'json_text' in locals() else 'Unavailable (error before extraction)'}'")
        raise ValueError("Failed to get a valid JSON response from the AI model.")
    except Exception as e: # Catch other specific Gemini exceptions if known, then generic Exception
        print(f"An error occurred during Gemini API call: {e}")
        # Log response details if available for debugging
        if 'response' in locals() and hasattr(response, 'prompt_feedback'):
             print(f"Gemini Prompt Feedback: {response.prompt_feedback}")
        raise ValueError(f"AI model interaction failed: {str(e)}")
