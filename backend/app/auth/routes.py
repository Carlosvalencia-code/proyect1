from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from .. import schemas, security # Relative imports for modules within the same package (app)
from ..database import db     # Relative import for database

router = APIRouter()

@router.post("/register", response_model=schemas.User)
async def register_user(user_create_data: schemas.UserCreate): # Renamed for clarity
    db_user = await db.user.find_unique(where={"email": user_create_data.email})
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    hashed_password_val = security.get_password_hash(user_create_data.password)

    # Prepare data for Prisma create, ensuring field names match Prisma schema
    user_data_to_create = {
        "email": user_create_data.email,
        "hashed_password": hashed_password_val, # Matches schema.prisma 'hashed_password'
    }
    if user_create_data.name is not None:
        user_data_to_create["name"] = user_create_data.name

    created_user = await db.user.create(data=user_data_to_create)

    # Pydantic's schemas.User (with orm_mode=True) will handle the conversion
    return created_user

@router.post("/login", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.user.find_unique(where={"email": form_data.username})

    # Ensure user exists and password is correct. Field name in DB is hashed_password
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = security.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}
