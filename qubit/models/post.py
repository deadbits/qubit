"""Post models."""

from typing import List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class PostBase(BaseModel):
    """Base post model."""

    title: str = Field(..., min_length=1, max_length=255)
    content: str
    slug: str = Field(..., min_length=1, max_length=255)
    published: bool = False


class PostCreate(BaseModel):
    """Post creation model."""

    title: str
    content: str
    slug: Optional[str] = None
    tags: List[str] = []
    published: bool = False


class PostEntry(PostBase):
    """Post database model."""

    id: UUID
    content_html: str
    author_id: int
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    tags: List[str] = []

    class Config:
        """Config."""
        from_attributes = True

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "title": self.title,
            "content": self.content,
            "content_html": self.content_html,
            "slug": self.slug,
            "published": self.published,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "author_id": self.author_id,
            "created_at": self.created_at.strftime('%Y-%m-%d @ %I:%M %p UTC'),
            "updated_at": self.updated_at.isoformat(),
            "tags": self.tags,
        }
