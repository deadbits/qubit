"""User models."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user model."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    display_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)


class UserCreate(UserBase):
    """User creation model."""

    password: str = Field(..., min_length=8)


class UserDB(UserBase):
    """User database model."""

    id: int
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        """Config."""
        from_attributes = True


class AuthUser(UserDB):
    """User model with password hash for authentication."""

    password_hash: str

    class Config:
        """Config."""
        from_attributes = True
