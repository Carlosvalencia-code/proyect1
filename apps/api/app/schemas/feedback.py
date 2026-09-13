"""
Esquemas Pydantic para Feedback
"""

from typing import Optional
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class FeedbackCategory(str, Enum):
    STYLE = "STYLE"
    ACCURACY = "ACCURACY"
    BUG = "BUG"
    FEATURE_REQUEST = "FEATURE_REQUEST"
    GENERAL = "GENERAL"


class FeedbackStatus(str, Enum):
    PENDING = "PENDING"
    REVIEWED = "REVIEWED"
    RESOLVED = "RESOLVED"


class FeedbackCreate(BaseModel):
    category: FeedbackCategory = FeedbackCategory.GENERAL
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    context_id: Optional[str] = None


class FeedbackUpdate(BaseModel):
    status: Optional[FeedbackStatus] = None
    admin_response: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: str = "fb_sample_id"
    user_id: str
    category: FeedbackCategory
    rating: int
    comment: Optional[str] = None
    status: FeedbackStatus = FeedbackStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FeedbackFilter(BaseModel):
    category: Optional[FeedbackCategory] = None
    status: Optional[FeedbackStatus] = None
