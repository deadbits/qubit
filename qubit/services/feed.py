"""Feed service."""

from typing import List, Optional
from uuid import UUID
from loguru import logger

from qubit.models.feed import FeedEntry, FeedEntryCreate
from qubit.database.feed import FeedDB


class FeedService:
    """Service for managing feed posts."""

    def __init__(self, db: FeedDB):
        """Initialize feed service."""
        self.db = db

    async def create_post(
        self, post: FeedEntryCreate, author_id: int, author_name: str
    ) -> Optional[FeedEntry]:
        """Create a new feed post."""
        try:
            created_post = await self.db.create_feed_post(
                content=post.content,
                author_id=author_id,
                author_name=author_name,
            )
            return created_post
        except Exception as e:
            logger.error(f"Error creating feed post: {e}")
            return None

    async def get_posts(self, limit: int = 20, offset: int = 0) -> List[FeedEntry]:
        """Get feed posts with pagination."""
        try:
            return await self.db.get_feed_posts(limit=limit, offset=offset)
        except Exception as e:
            logger.error(f"Error fetching feed posts: {e}")
            return []

    async def delete_post(self, post_id: UUID) -> bool:
        """Delete a feed post."""
        try:
            return await self.db.delete_feed_post(post_id)
        except Exception as e:
            logger.error(f"Error deleting feed post: {e}")
            return False
