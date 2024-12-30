"""Tag models."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class TagBase(BaseModel):
    """Base tag model."""

    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)


class TagCreate(TagBase):
    """Tag creation model."""
    pass

class TagDB(TagBase):
    """Tag database model."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Config."""
        from_attributes = True
