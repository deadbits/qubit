from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class FeedEntryCreate(BaseModel):
    """Feed post creation model."""

    content: str


class FeedEntry(BaseModel):
    """Feed post model."""

    id: UUID
    content: str
    author_id: int
    author_name: str
    created_at: datetime
    updated_at: datetime
