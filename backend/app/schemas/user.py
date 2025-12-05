"""User Pydantic schemas for authentication endpoints.

Requirements: 1.4, 11.4
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    name: str | None = None
    avatar_url: str | None = None


class UserResponse(UserBase):
    """User response schema returned from API endpoints."""
    id: UUID
    google_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Token response schema for authentication."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
