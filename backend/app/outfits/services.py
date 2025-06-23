import random
from typing import List, Dict, Optional, Any
from ..database import db # Prisma client
# Assuming ClothingItemResponse is defined in app.schemas (or will be moved there)
# from ..schemas import ClothingItemResponse

# For now, to make this file self-contained for generation if schemas are not yet updated by user:
# --- Temporary Schema (should be in app.schemas.py) ---
from pydantic import BaseModel as PydanticBaseModel, Field as PydanticField
from datetime import datetime as PyDateTime

class TempClothingItemResponse(PydanticBaseModel): # Using Temp prefix
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
# --- End of Temporary Schema ---


async def suggest_outfit_for_user(user_id: str, occasion: str, current_temp_celsius: Optional[int] = None) -> Dict[str, Any]:
    """
    Suggests an outfit for a given user and occasion based on items in their virtual wardrobe.
    Includes basic temperature considerations if current_temp_celsius is provided.

    Args:
        user_id: The ID of the user.
        occasion: The occasion for the outfit (e.g., "Casual", "Work", "Evening", "Sport").
        current_temp_celsius: Optional current temperature in Celsius for weather-based suggestions.

    Returns:
        A dictionary representing the suggested outfit, e.g.,
        {
            "occasion": "Work",
            "temperature_consideration": "Cool weather (10°C)", // or "Not specified"
            "top": TempClothingItemResponse,
            "bottom": TempClothingItemResponse,
            "outerwear": TempClothingItemResponse (optional),
            "shoes": TempClothingItemResponse,
            "accessory": TempClothingItemResponse (optional),
            "notes": "This outfit is suitable for a professional work environment."
        }
        Returns an error message if a suitable outfit cannot be generated.
    """

    # 1. Determine Formality Level from Occasion
    # This is a simplified mapping. A more complex system might be needed.
    formality_map = {
        "casual": ["Casual"],
        "work": ["Business Casual", "Smart Casual"],
        "office": ["Business Casual", "Smart Casual"],
        "business": ["Business Formal", "Business Casual"],
        "evening": ["Formal/Evening", "Smart Casual"],
        "party": ["Formal/Evening", "Smart Casual", "Casual"],
        "sport": ["Casual"], # Assuming sportswear is 'Casual' formality in the DB
        "gym": ["Casual"],
        "errands": ["Casual"],
        "weekend": ["Casual", "Smart Casual"],
        "date_night": ["Smart Casual", "Casual"] # Can vary
    }
    target_formalities = formality_map.get(occasion.lower(), ["Casual", "Smart Casual"]) # Default if occasion not mapped

    # 2. Determine Seasonality based on Temperature (if provided)
    # Simplified seasonality. This could be enhanced with user preferences or actual date.
    target_seasons_flags = {}
    temperature_consideration = "Not specified"
    if current_temp_celsius is not None:
        temperature_consideration = f"{current_temp_celsius}°C"
        if current_temp_celsius < 10: # Cold
            target_seasons_flags = {"isWinter": True}
            temperature_consideration = f"Cold weather ({current_temp_celsius}°C)"
        elif 10 <= current_temp_celsius < 20: # Cool / Mild
            target_seasons_flags = {"isSpring": True, "isAutumn": True}
            temperature_consideration = f"Cool/mild weather ({current_temp_celsius}°C)"
        elif current_temp_celsius >= 20: # Warm / Hot
            target_seasons_flags = {"isSummer": True, "isSpring": True} # Spring can be warm too
            temperature_consideration = f"Warm weather ({current_temp_celsius}°C)"

    # 3. Fetch relevant clothing items from the user's wardrobe
    wardrobe_items_db = await db.clothingitem.find_many(
        where={
            "userId": user_id,
            "formality": {"in": target_formalities},
            **target_seasons_flags # Spread season flags if they exist
        }
    )

    # Convert Prisma models to Pydantic models (TempClothingItemResponse for now)
    wardrobe_items = [TempClothingItemResponse.from_orm(item) for item in wardrobe_items_db]

    if not wardrobe_items:
        return {"error": "No suitable items found in your wardrobe for this occasion/weather. Try adding more items!"}

    # 4. Basic Outfit Generation Logic (Rule-Based)
    # This is a very simplified version. A real system would use more complex rules,
    # color matching, style compatibility, user preferences, etc.

    outfit: Dict[str, Optional[TempClothingItemResponse]] = {
        "top": None, "bottom": None, "outerwear": None, "shoes": None, "accessory": None
    }

    available_items_by_category: Dict[str, List[TempClothingItemResponse]] = {
        "Top": [], "Bottom": [], "Outerwear": [], "Shoes": [], "Accessory": []
    }
    for item in wardrobe_items:
        if item.category in available_items_by_category:
            available_items_by_category[item.category].append(item)

    # Select a top
    if available_items_by_category["Top"]:
        outfit["top"] = random.choice(available_items_by_category["Top"])

    # Select a bottom
    if available_items_by_category["Bottom"]:
        outfit["bottom"] = random.choice(available_items_by_category["Bottom"])

    # Select shoes
    if available_items_by_category["Shoes"]:
        outfit["shoes"] = random.choice(available_items_by_category["Shoes"])

    # Optionally select outerwear (more likely in cold/cool weather)
    if current_temp_celsius is not None and current_temp_celsius < 18: # Threshold for outerwear
        if available_items_by_category["Outerwear"]:
            outfit["outerwear"] = random.choice(available_items_by_category["Outerwear"])

    # Optionally select an accessory
    if available_items_by_category["Accessory"] and random.random() < 0.5: # 50% chance of adding an accessory
        outfit["accessory"] = random.choice(available_items_by_category["Accessory"])

    # Check if a basic outfit (top and bottom, or a dress-like item if you add that category) was formed
    if not outfit["top"] or not outfit["bottom"]: # Simplistic check, assumes no dresses/jumpsuits
        # If you add "Dress" or "Jumpsuit" categories, this logic needs to be smarter.
        # E.g., if a "Dress" is chosen, "bottom" might not be needed.
        return {"error": "Could not form a basic outfit (top & bottom) with available items for this occasion/weather."}
    if not outfit["shoes"]:
         return {"error": "Could not find suitable shoes for this outfit."}


    # 5. Construct and return the response
    outfit_suggestion = {
        "occasion": occasion.capitalize(),
        "temperature_consideration": temperature_consideration,
        "items": {k: v.dict(by_alias=True) if v else None for k, v in outfit.items()}, # Convert Pydantic models to dicts
        "notes": "This is a basic outfit suggestion. Consider color coordination and your personal style!"
    }

    # Filter out None items from the 'items' dict for cleaner response
    outfit_suggestion["items"] = {k: v for k,v in outfit_suggestion["items"].items() if v is not None}

    return outfit_suggestion
