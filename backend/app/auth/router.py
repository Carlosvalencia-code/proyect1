from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm # For login form dependency

from prisma.errors import UniqueViolationError

from . import services
from . import schemas
from .security import create_access_token #, get_current_user # get_current_user will be for protected routes

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register_new_user(user_data: schemas.UserCreate):
    """
    Register a new user.
    - Accepts email, password, and optional name.
    - Hashes the password before storing.
    - Returns the created user's information (without password).
    """
    existing_user = await services.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered.",
        )
    try:
        new_user = await services.create_new_user(user_data)
        return new_user
    except UniqueViolationError: # Should be caught by the check above, but as a safeguard
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered (database constraint).",
        )
    except Exception as e:
        # Log the exception e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during user registration: {str(e)}",
        )


@router.post("/login", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Log in a user and return an access token.
    - Accepts email (as username) and password from a form.
    - Verifies credentials.
    - Returns a JWT access token if successful.
    """
    user = await services.authenticate_user(email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.email} # "sub" (subject) is a standard claim for JWT
        # You can add more data to the token if needed, e.g., user_id: str(user.id)
    )
    return {"access_token": access_token, "token_type": "bearer"}


# Example of a protected route (to be implemented/used later if needed)
# @router.get("/users/me", response_model=schemas.UserResponse)
# async def read_users_me(current_user: schemas.UserResponse = Depends(get_current_user)):
#     """
#     Get the current authenticated user's details.
#     This is an example of a protected route.
#     """
#     # In a real scenario, get_current_user would return a full User model instance
#     # For now, if get_current_user returns TokenData, you'd fetch user from DB here.
#     # This endpoint might need adjustment based on what get_current_user actually returns.
#     return current_user
