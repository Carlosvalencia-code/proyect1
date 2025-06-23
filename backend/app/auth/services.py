from typing import Optional
from prisma.models import User
from prisma.errors import UniqueViolationError, PrismaError

from ..db import db_client # Prisma client instance
from .schemas import UserCreate
from .security import get_password_hash, verify_password

async def get_user_by_email(email: str) -> Optional[User]:
    """
    Retrieves a user by their email address.
    Returns the User object or None if not found.
    """
    user = await db_client.user.find_unique(where={"email": email})
    return user

async def create_new_user(user_data: UserCreate) -> User:
    """
    Creates a new user in the database.
    Hashes the password before storing.
    Raises UniqueViolationError if the email already exists.
    """
    hashed_password = get_password_hash(user_data.password)
    try:
        new_user = await db_client.user.create(
            data={
                "email": user_data.email,
                "hashedPassword": hashed_password,
                "name": user_data.name,
            }
        )
        return new_user
    except UniqueViolationError as e:
        # Re-raise the specific error to be handled by the endpoint
        raise e
    except PrismaError as e:
        # Handle other potential Prisma errors or log them
        # For now, re-raise a generic exception or a custom one
        print(f"PrismaError during user creation: {e}") # TODO: Replace with proper logging
        raise Exception("Could not create user due to a database error.")


async def authenticate_user(email: str, password: str) -> Optional[User]:
    """
    Authenticates a user by email and password.
    Returns the User object if authentication is successful, None otherwise.
    """
    user = await get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user.hashedPassword):
        return None
    return user
