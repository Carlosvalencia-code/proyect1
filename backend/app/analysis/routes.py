# import base64 # Not currently used
# import json # Parsing is handled in the service

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from .. import schemas, security # Relative imports
from ..services import gemini_service # Relative import for service

router = APIRouter()

@router.post(
    "/facial",
    response_model=schemas.FacialAnalysisResponseData, # Use the Pydantic model for response
    responses={ # Define potential error responses for OpenAPI documentation
        status.HTTP_400_BAD_REQUEST: {"model": schemas.ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": schemas.ErrorResponse},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": schemas.ErrorResponse}, # If Gemini service is down
    }
)
async def perform_facial_analysis_route( # Renamed to avoid conflict if schemas.User is also named User
    file: UploadFile = File(..., description="Image file for facial analysis (e.g., JPEG, PNG)."),
    # The get_current_user dependency should return a Pydantic model (schemas.User)
    # as defined in the updated security.py for type safety and proper data exposure.
    current_user: schemas.User = Depends(security.get_current_user)
):
    """
    Endpoint to perform facial analysis on an uploaded image.
    - Requires user authentication.
    - Accepts an image file.
    - Returns a structured JSON analysis based on the `FacialAnalysisResponseData` schema.
    """
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only images are allowed."
        )

    image_bytes = await file.read()

    try:
        # Pass the actual mime_type of the uploaded file to the service
        analysis_result_dict = await gemini_service.analyze_face_with_gemini(
            image_bytes,
            image_mime_type=file.content_type
        )

        # If Gemini service returns a dict with an "error" key, it means Gemini
        # itself identified an issue with the image or analysis.
        if "error" in analysis_result_dict:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, # Or 400 depending on error type
                detail=analysis_result_dict["error"]
            )

        # FastAPI will validate analysis_result_dict against schemas.FacialAnalysisResponseData
        # If it matches, it will be returned. If not, FastAPI raises a validation error.
        return analysis_result_dict

    except ValueError as e: # Catches errors from gemini_service (e.g., config, API interaction, JSON parsing)
        # Log the error internally
        print(f"ValueError in facial analysis for user {current_user.email}: {e}")
        if "Gemini model not initialized" in str(e) or "GEMINI_API_KEY" in str(e):
             raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The AI analysis service is temporarily unavailable due to configuration issues."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during AI analysis: {str(e)}"
        )
    except HTTPException: # Re-raise HTTPExceptions (like 400 for bad file type)
        raise
    except Exception as e: # Catch any other unexpected errors
        print(f"Unexpected error in facial analysis for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during the analysis process: {str(e)}"
        )
