from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime # Added for timestamp fields in User schema

class UserBase(BaseModel): # Added UserBase for consistency
    email: EmailStr
    name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8) # Added min_length for password

class User(UserBase): # Inherits from UserBase
    id: str
    # Adding timestamps as they are in the Prisma schema and good practice
    createdAt: datetime = Field(alias="createdAt") # Alias to match Prisma field if needed
    updatedAt: datetime = Field(alias="updatedAt") # Alias to match Prisma field if needed

    class Config:
        orm_mode = True
        allow_population_by_field_name = True # If using aliases like createdAt for created_at


class Token(BaseModel):
    access_token: str
    token_type: str

# Added TokenData as it's used in security.py and good practice
class TokenData(BaseModel):
    email: Optional[str] = None
    # Potentially other fields like user_id if stored in token

# Added Schemas for Analysis based on gemini_service.py and analysis/routes.py from prompt
class FacialAnalysisResponseData(BaseModel): # Renamed for clarity
    forma_rostro: str
    caracteristicas_destacadas: List[str]
    confianza_analisis_facial: int
    recomendaciones_estilo_facial: dict # This will be a nested dict as per Gemini prompt

    class Config:
        orm_mode = True # If it ever needs to be created from an ORM model

class ErrorResponse(BaseModel): # Generic error response
    detail: str
