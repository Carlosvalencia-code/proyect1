import os
import google.generativeai as genai
from fastapi import UploadFile, HTTPException, status
from typing import Dict, Any
import uuid

# Configure the Gemini API key
# It's crucial that GEMINI_API_KEY is set in your environment
try:
    GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
except KeyError:
    # This will prevent the app from starting if the key isn't set,
    # which is good for production. For local dev, you might want a fallback or clearer error.
    raise RuntimeError("GEMINI_API_KEY environment variable not set.")
except Exception as e:
    raise RuntimeError(f"Failed to configure Gemini API: {str(e)}")


# Initialize the GenerativeModel
# Using gemini-1.5-flash-latest as specified
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# Define safety settings if needed, though the prompt doesn't specify them.
# Example:
# safety_settings = [
#     {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
#     {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
#     # ... other categories
# ]

async def analyze_face_with_gemini(image_file: UploadFile) -> Dict[str, Any]:
    """
    Analyzes a facial image using Google Gemini API.

    Args:
        image_file: The uploaded image file.

    Returns:
        A dictionary containing the processed analysis result from Gemini.

    Raises:
        HTTPException: If the API call fails or image processing fails.
    """
    if not image_file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only images are allowed."
        )

    try:
        image_bytes = await image_file.read()

        # Prepare the image part for the Gemini API
        image_parts = [
            {
                "mime_type": image_file.content_type,
                "data": image_bytes
            },
        ]

        # Construct the prompt based on "Desarrollo Final del MVP_ Análisis IA y Consejos Personalizados.md"
        # This is a placeholder. The actual prompt needs to be carefully crafted.
        # It should instruct Gemini on what to analyze and the desired JSON output format.
        # Example: "Analyze this facial image. Identify face shape, skin tone, eye color, hair color.
        # Provide suggestions for clothing styles, makeup, and accessories that would complement these features.
        # Return the response as a JSON object with keys: 'face_shape', 'skin_tone', 'eye_color', 'hair_color',
        # 'clothing_styles', 'makeup_tips', 'accessory_suggestions'."

        # TODO: Retrieve the detailed prompt from "Desarrollo Final del MVP_ Análisis IA y Consejos Personalizados.md"
        # For now, using a simplified placeholder prompt.
        prompt_text_template = """
        Eres SEENTIA, una IA experta en análisis de estilo personal y morfología facial.
        Analiza la siguiente imagen facial y proporciona un análisis detallado en formato JSON.
        El JSON debe incluir los siguientes campos como mínimo:
        - "face_shape": (ej. "Ovalada", "Redonda", "Cuadrada", "Corazón", "Diamante", "Alargada")
        - "skin_tone": (ej. "Cálida Clara", "Fría Oliva", "Neutra Media", "Profunda Cálida")
        - "eye_color_analysis": (Descripción del color de ojos y subtonos)
        - "hair_color_analysis": (Descripción del color de cabello, reflejos y subtonos)
        - "key_features": ["Lista de 2-3 características faciales destacadas"]
        - "style_summary": "Un breve resumen (2-3 frases) de las recomendaciones de estilo generales."
        - "clothing_palette_suggestions": {
            "primary_colors": ["color1", "color2", "color3"],
            "accent_colors": ["colorA", "colorB"]
          }
        - "clothing_style_recommendations": ["tipo de cuello recomendado", "tipo de escote", "estampados favorables"]
        - "accessory_recommendations": {
            "earrings": "tipo/forma de pendientes",
            "necklaces": "tipo/longitud de collares",
            "glasses_frames": "forma de montura de gafas si aplica"
          }
        - "makeup_tips": ["consejo de maquillaje 1", "consejo de maquillaje 2"]
        - "confidence_boost_tip": "Un consejo final para potenciar la confianza."

        Asegúrate de que la respuesta sea únicamente el objeto JSON. No incluyas texto introductorio o explicaciones fuera del JSON.
        Si la imagen no es adecuada para el análisis (no es un rostro, muy baja calidad, etc.),
        el JSON debe tener un único campo "error" con una descripción del problema.
        Ejemplo de error: {"error": "No se detectó un rostro claro en la imagen."}
        """

        # Generate content
        # response = model.generate_content([prompt_text_template, image_parts], safety_settings=safety_settings)
        # The image_parts[0] itself is the blob/dict that Gemini expects.
        response = model.generate_content([prompt_text_template, image_parts[0]])


        # Assuming Gemini returns a JSON string in response.text or a similar attribute.
        # The exact way to get the JSON might vary based on the Gemini SDK version and response object structure.
        # It's often in response.text, but could be response.parts[0].text or similar.
        # Prisma's client generation process might have also failed if the node process failed due to CWD issues.

        # Gemini's response.text often needs to be cleaned if it includes markdown like ```json ... ```
        raw_json_text = response.text
        if raw_json_text.strip().startswith("```json"):
            raw_json_text = raw_json_text.strip()[7:-3].strip() # Remove ```json\n and \n```
        elif raw_json_text.strip().startswith("```"):
             raw_json_text = raw_json_text.strip()[3:-3].strip() # Remove ```\n and \n```

        # It's safer to parse the JSON here to ensure it's valid before returning.
        import json
        analysis_result = json.loads(raw_json_text)

        if "error" in analysis_result:
             raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=analysis_result["error"]
            )

        return analysis_result

    except genai.types.BlockedPromptException as e:
        # Handle cases where the prompt was blocked by safety settings
        # log.error(f"Gemini API request blocked: {e}") # Requires logger setup
        print(f"Gemini API request blocked: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image or prompt content was blocked by safety filters. {str(e)}"
        )
    except genai.types. générations.StopCandidateException as e: # Check exact exception type
        print(f"Gemini API generation stopped: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content generation stopped unexpectedly. {str(e)}"
        )
    except json.JSONDecodeError:
        print(f"Failed to parse Gemini JSON response. Raw response: {response.text}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse analysis result from AI. The response was not valid JSON."
        )
    except Exception as e:
        # Log the exception e (e.g., using a proper logger)
        print(f"Error during Gemini API call: {str(e)}") # Replace with actual logging
        # Consider more specific error handling for different Gemini API errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while analyzing the image: {str(e)}"
        )
