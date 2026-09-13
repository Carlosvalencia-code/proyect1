"""
Modelo de usuario de dominio
"""
from typing import Optional
from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: str = "usr_demo_123"
    email: EmailStr = "demo@synthia.style"
    first_name: Optional[str] = "Demo"
    last_name: Optional[str] = "Merchant"
    is_active: bool = True
