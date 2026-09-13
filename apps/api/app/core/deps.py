"""
Dependencias comunes de FastAPI
"""
from app.db.database import get_db
from app.core.security import get_current_user_id, get_current_user

__all__ = ["get_db", "get_current_user_id", "get_current_user"]
