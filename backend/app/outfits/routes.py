from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, Dict, Any, List # Added List

from .. import schemas  # Main Pydantic models
from ..security import get_current_user
from . import services  # The outfit suggestion services

router = APIRouter()

# Define Pydantic models for request and response if not already in app.schemas
# For now, assuming the response structure from services.suggest_outfit_for_user is a dict
# and we can create a Pydantic model for it.

# --- Temporary Schemas (should be in app.schemas.py) ---
from pydantic import BaseModel as PydanticBaseModel, Field as PydanticField
from datetime import datetime as PyDateTime

# This schema should match the one used in wardrobe/routes.py and services.py
# If it's defined in app.schemas.py, import it from there.
class TempOutfitClothingItemResponse(PydanticBaseModel): # Prefixed to avoid name clash if already in schemas
    id: str
    category: str
    type: str
    color: str
    pattern: PyOptional[str] = None
    material: PyOptional[str] = None
    brand: PyOptional[str] = None
    image_url: PyOptional[str] = PydanticField(None, alias="imageUrl")
    notes: PyOptional[str] = None
    is_spring: bool = PydanticField(True, alias="isSpring")
    is_summer: bool = PydanticField(True, alias="isSummer")
    is_autumn: bool = PydanticField(True, alias="isAutumn")
    is_winter: bool = PydanticField(True, alias="isWinter")
    formality: str = "Casual"
    created_at: PyDateTime = PydanticField(alias="createdAt")
    updated_at: PyDateTime = PydanticField(alias="updatedAt")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class SuggestedOutfitItems(PydanticBaseModel):
    top: PyOptional[TempOutfitClothingItemResponse] = None
    bottom: PyOptional[TempOutfitClothingItemResponse] = None
    outerwear: PyOptional[TempOutfitClothingItemResponse] = None
    shoes: PyOptional[TempOutfitClothingItemResponse] = None
    accessory: PyOptional[TempOutfitClothingItemResponse] = None

class OutfitSuggestionResponse(PydanticBaseModel):
    occasion: str
    temperature_consideration: str
    items: SuggestedOutfitItems
    notes: str

class OutfitSuggestionErrorResponse(PydanticBaseModel):
    error: str

# --- End of Temporary Schemas ---


@router.post(
    "/suggest",
    response_model=OutfitSuggestionResponse, # Or a Union if error is also a Pydantic model
    responses={
        status.HTTP_404_NOT_FOUND: {"model": OutfitSuggestionErrorResponse, "description": "Could not generate outfit"},
        status.HTTP_400_BAD_REQUEST: {"model": schemas.ErrorResponse, "description": "Invalid input"} # Generic error
    }
)
async def suggest_outfit_route(
    occasion: str = Query(..., description="The occasion for the outfit (e.g., 'Work', 'Casual', 'Evening')."),
    current_temp_celsius: Optional[int] = Query(None, description="Optional current temperature in Celsius for weather-based suggestions (e.g., 15)."),
    current_user: schemas.User = Depends(get_current_user)
):
    """
    Suggests an outfit based on the user's wardrobe, occasion, and optional temperature.
    """
    if not occasion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Occasion parameter is required."
        )

    try:
        suggestion_result = await services.suggest_outfit_for_user(
            user_id=current_user.id,
            occasion=occasion,
            current_temp_celsius=current_temp_celsius
        )

        if "error" in suggestion_result:
            # This means the service logic determined no suitable outfit could be formed
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, # Or 422 if input valid but no combo
                detail=suggestion_result["error"]
            )

        # Validate and return the successful suggestion
        # The structure of suggestion_result must match OutfitSuggestionResponse
        return OutfitSuggestionResponse(**suggestion_result)

    except HTTPException:
        raise # Re-raise HTTPExceptions from service or above
    except Exception as e:
        # Log e for debugging
        print(f"Error suggesting outfit for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while generating outfit suggestion: {str(e)}"
        )

# The main app (e.g., backend/app/main.py) will need to include this router:
# from app.outfits.routes import router as outfits_router
# app.include_router(outfits_router, prefix="/outfits", tags=["Outfits"])
