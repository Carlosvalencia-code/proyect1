from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional

from .. import schemas  # Pydantic models from the main app.schemas
from ..database import db  # Prisma client instance
from ..security import get_current_user # Dependency to get current authenticated user

router = APIRouter()

# Pydantic schemas for ClothingItem
# These should ideally be in app.schemas.py, but for modularity within this task,
# they can be defined here or imported if already added to the main schemas.py.
# For this exercise, I'll assume they should be added to app.schemas.py and imported.
# If not, I would define them here like this:
#
# from pydantic import BaseModel, Field
# from datetime import datetime
# class ClothingItemBase(BaseModel):
#     category: str
#     type: str
#     color: str
#     pattern: Optional[str] = None
#     material: Optional[str] = None
#     brand: Optional[str] = None
#     imageUrl: Optional[str] = Field(None, alias="image_url")
#     notes: Optional[str] = None
#     isSpring: bool = Field(True, alias="is_spring")
#     isSummer: bool = Field(True, alias="is_summer")
#     isAutumn: bool = Field(True, alias="is_autumn")
#     isWinter: bool = Field(True, alias="is_winter")
#     formality: str = "Casual"

# class ClothingItemCreate(ClothingItemBase):
#     pass

# class ClothingItemUpdate(ClothingItemBase):
#     # All fields optional for update
#     category: Optional[str] = None
#     type: Optional[str] = None
#     color: Optional[str] = None
#     # ... other fields made optional

# class ClothingItemResponse(ClothingItemBase):
#     id: str
#     userId: str = Field(alias="user_id") # To match schema if not using alias in Prisma model for response
#     createdAt: datetime = Field(alias="created_at")
#     updatedAt: datetime = Field(alias="updated_at")

#     class Config:
#         orm_mode = True
#         allow_population_by_field_name = True


# Assuming ClothingItemCreate, ClothingItemUpdate, ClothingItemResponse are defined in app.schemas.py
# For now, I will proceed as if they are. If not, they need to be added there.
# Let's define simplified versions here if not present in the provided schemas.py.
# This is a common point of iteration. For now, I will assume they are defined in the main schemas.py
# and match the fields in prisma.schema.

# Let's add them to app.schemas.py for clarity.
# I will assume `ClothingItemCreate`, `ClothingItemUpdate`, and `ClothingItemResponse`
# have been added to `backend/app/schemas.py` with fields matching the Prisma model.
# If not, the user will need to add them. For this exercise, I'll proceed with this assumption.
# The user's prompt for `backend/app/schemas.py` did *not* include these, so it's a gap.
# I will define them here for now for completeness of this file, but highlight this.

# --- Temporary Schemas (should be in app.schemas.py) ---
from pydantic import BaseModel as PydanticBaseModel, Field as PydanticField # Alias to avoid conflict
from datetime import datetime as PyDateTime # Alias to avoid conflict
from typing import Optional as PyOptional, List as PyList # Alias

class ClothingItemBase(PydanticBaseModel):
    category: str
    type: str
    color: str
    pattern: PyOptional[str] = None
    material: PyOptional[str] = None
    brand: PyOptional[str] = None
    image_url: PyOptional[str] = PydanticField(None, alias="imageUrl") # For request, use DB name
    notes: PyOptional[str] = None
    is_spring: bool = PydanticField(True, alias="isSpring")
    is_summer: bool = PydanticField(True, alias="isSummer")
    is_autumn: bool = PydanticField(True, alias="isAutumn")
    is_winter: bool = PydanticField(True, alias="isWinter")
    formality: str = "Casual"

class ClothingItemCreate(ClothingItemBase):
    pass

class ClothingItemUpdate(PydanticBaseModel): # All fields optional for PATCH-like behavior
    category: PyOptional[str] = None
    type: PyOptional[str] = None
    color: PyOptional[str] = None
    pattern: PyOptional[str] = None
    material: PyOptional[str] = None
    brand: PyOptional[str] = None
    image_url: PyOptional[str] = PydanticField(None, alias="imageUrl")
    notes: PyOptional[str] = None
    is_spring: PyOptional[bool] = PydanticField(None, alias="isSpring")
    is_summer: PyOptional[bool] = PydanticField(None, alias="isSummer")
    is_autumn: PyOptional[bool] = PydanticField(None, alias="isAutumn")
    is_winter: PyOptional[bool] = PydanticField(None, alias="isWinter")
    formality: PyOptional[str] = None


class ClothingItemResponse(ClothingItemBase):
    id: str
    # userId: str # Not typically exposed directly, inferred from authenticated user
    created_at: PyDateTime = PydanticField(alias="createdAt")
    updated_at: PyDateTime = PydanticField(alias="updatedAt")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True # To handle Prisma's camelCase vs Python's snake_case if needed

# --- End of Temporary Schemas ---

@router.post("/items", response_model=ClothingItemResponse, status_code=status.HTTP_201_CREATED)
async def create_clothing_item(
    item_data: ClothingItemCreate,
    current_user: schemas.User = Depends(get_current_user) # schemas.User is the Pydantic model for User
):
    """
    Add a new clothing item to the current user's wardrobe.
    """
    try:
        # Convert Pydantic model to dict, handling potential alias for request body if needed
        data_to_create = item_data.dict(by_alias=False) # Use model field names for Prisma
        data_to_create['userId'] = current_user.id

        new_item = await db.clothingitem.create(data=data_to_create)
        return new_item # Pydantic will convert from ORM model
    except Exception as e:
        # Log e for debugging
        print(f"Error creating clothing item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create clothing item."
        )

@router.get("/items", response_model=PyList[ClothingItemResponse])
async def get_clothing_items(
    current_user: schemas.User = Depends(get_current_user),
    category: PyOptional[str] = Query(None, description="Filter by category, e.g., Top, Bottom"),
    color: PyOptional[str] = Query(None, description="Filter by color"),
    formality: PyOptional[str] = Query(None, description="Filter by formality, e.g., Casual, Formal")
):
    """
    Retrieve all clothing items for the current user, with optional filters.
    """
    filters = {"userId": current_user.id}
    if category:
        filters["category"] = category
    if color:
        filters["color"] = {"contains": color, "mode": "insensitive"} # Case-insensitive color search
    if formality:
        filters["formality"] = formality

    items = await db.clothingitem.find_many(
        where=filters,
        order={"createdAt": "desc"} # Or any other preferred order
    )
    return items

@router.put("/items/{item_id}", response_model=ClothingItemResponse)
async def update_clothing_item(
    item_id: str,
    item_data: ClothingItemUpdate, # Use a separate schema for updates where all fields are optional
    current_user: schemas.User = Depends(get_current_user)
):
    """
    Update an existing clothing item for the current user.
    """
    item_to_update = await db.clothingitem.find_first(
        where={"id": item_id, "userId": current_user.id}
    )
    if not item_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clothing item not found or you don't have permission to update it."
        )

    # Get data to update, excluding unset fields to allow partial updates
    update_data = item_data.dict(exclude_unset=True, by_alias=False)

    if not update_data:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update data provided."
        )

    try:
        updated_item = await db.clothingitem.update(
            where={"id": item_id},
            data=update_data
        )
        return updated_item
    except Exception as e:
        # Log e
        print(f"Error updating clothing item {item_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update clothing item."
        )

@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_clothing_item(
    item_id: str,
    current_user: schemas.User = Depends(get_current_user)
):
    """
    Delete a clothing item for the current user.
    """
    item_to_delete = await db.clothingitem.find_first(
        where={"id": item_id, "userId": current_user.id}
    )
    if not item_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clothing item not found or you don't have permission to delete it."
        )

    try:
        await db.clothingitem.delete(where={"id": item_id})
        return  # No content to return for 204
    except Exception as e:
        # Log e
        print(f"Error deleting clothing item {item_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not delete clothing item."
        )

# The main app (e.g., backend/app/main.py) will need to include this router:
# from app.wardrobe.routes import router as wardrobe_router
# app.include_router(wardrobe_router, prefix="/wardrobe", tags=["Wardrobe"])
