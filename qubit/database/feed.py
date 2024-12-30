"""Feed database operations."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from loguru import logger

from qubit.database import Database
from qubit.models.feed import FeedEntry


class FeedDB(Database):
    """Feed database operations."""

    async def create_feed_post(
        self, content: str, author_id: int, author_name: str
    ) -> Optional[FeedEntry]:
        """Create a new feed post."""
        async with self._pool.acquire() as conn:
            try:
                now = datetime.utcnow()
                row = await conn.fetchrow(
                    """
                    INSERT INTO feed_posts (
                        content, author_id, author_name,
                        created_at, updated_at
                    )
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id, content, author_id, author_name,
                              created_at, updated_at
                """,
                    content,
                    author_id,
                    author_name,
                    now,
                    now,
                )

                if row:
                    return FeedEntry(
                        id=row["id"],
                        content=row["content"],
                        author_id=row["author_id"],
                        author_name=row["author_name"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                    )
                return None

            except Exception as e:
                logger.error(f"Error creating feed post: {e}")
                return None

    async def get_feed_posts(self, limit: int = 20, offset: int = 0) -> List[FeedEntry]:
        """Get feed posts."""
        async with self._pool.acquire() as conn:
            try:
                rows = await conn.fetch(
                    """
                    SELECT id, content, author_id, author_name, created_at, updated_at
                    FROM feed_posts
                    ORDER BY created_at DESC
                    LIMIT $1 OFFSET $2
                """,
                    limit,
                    offset,
                )

                return [
                    FeedEntry(
                        id=row["id"],
                        content=row["content"],
                        author_id=row["author_id"],
                        author_name=row["author_name"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                    )
                    for row in rows
                ]

            except Exception as e:
                logger.error(f"Error fetching feed posts: {e}")
                return []

    async def delete_feed_post(self, post_id: UUID) -> bool:
        """Delete a feed post."""
        async with self._pool.acquire() as conn:
            try:
                result = await conn.execute(
                    """
                    DELETE FROM feed_posts WHERE id = $1
                """,
                    post_id,
                )

                return "DELETE 1" in result

            except Exception as e:
                logger.error(f"Error deleting feed post: {e}")
                return False
