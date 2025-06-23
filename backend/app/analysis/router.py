import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from typing import Dict, Any

from . import services
from .schemas import FacialAnalysisResponse #, FacialAnalysisRequest (if defined and needed)
from ..auth.security import get_current_active_user
from ..auth.schemas import UserResponse # To type hint current_user

router = APIRouter(
    prefix="/api/analysis", # Changed from /api/analysis/facial to make it more general for future analysis types
    tags=["Analysis Services"],
    dependencies=[Depends(get_current_active_user)] # Protect all routes in this router
)

@router.post("/facial", response_model=FacialAnalysisResponse)
async def perform_facial_analysis(
    image: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_active_user) # Get authenticated user
):
    """
    Perform facial analysis on an uploaded image.
    - Requires authentication.
    - Accepts an image file.
    - Returns a structured JSON analysis from Google Gemini.
    """
    # Log which user is making the request (optional)
    print(f"Facial analysis request by user: {current_user.email} (ID: {current_user.id})")

    try:
        gemini_result = await services.analyze_face_with_gemini(image_file=image)

        # Construct the response. You might want to save the analysis linked to the user,
        # generate a unique ID for it, etc.
        analysis_id = str(uuid.uuid4()) # Generate a unique ID for this analysis

        # Adapt this based on how you want to structure FacialAnalysisResponse
        # and what's actually in gemini_result
        response_data = FacialAnalysisResponse(
            analysis_id=analysis_id,
            summary=gemini_result.get("style_summary", "No summary available."), # Example access
            face_shape=gemini_result.get("face_shape"),
            skin_tone=gemini_result.get("skin_tone"),
            suggested_styles=gemini_result.get("clothing_style_recommendations", []),
            raw_gemini_response=gemini_result # Store the full response if needed
            # Populate other fields from gemini_result as defined in FacialAnalysisResponse
        )
        return response_data

    except HTTPException as e:
        # Re-raise HTTPExceptions directly (e.g., from image validation or Gemini error handling)
        raise e
    except Exception as e:
        # Log the exception e
        print(f"Unexpected error in /facial endpoint: {str(e)}") # Replace with proper logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while processing the facial analysis: {str(e)}"
        )
