"""Post database operations."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from loguru import logger

from qubit.models.post import PostCreate, PostEntry
from qubit.core.cache import cache_result, RedisCache
from qubit.database import Database


class PostsDB(Database):
    """Post database operations."""

    _redis = RedisCache.get_instance()

    def __init__(self, config):
        """Initialize database configuration."""
        super().__init__(config)

    @cache_result(ttl=300)  # Cache for 5 minutes
    async def get_post_by_slug(self, slug: str) -> Optional[PostEntry]:
        """Get post by slug with caching."""
        async with self._pool.acquire() as conn:
            try:
                row = await conn.fetchrow(
                    """
                    SELECT p.id, p.title, p.content, p.content_html, p.slug,
                           p.published, p.published_at, p.author_id,
                           p.created_at, p.updated_at,
                           array_agg(t.name) as tags
                    FROM posts p
                    LEFT JOIN post_tags pt ON p.id = pt.post_id
                    LEFT JOIN tags t ON pt.tag_id = t.id
                    WHERE p.slug = $1
                    GROUP BY p.id
                """,
                    slug,
                )

                if row:
                    return PostEntry(
                        id=row["id"],
                        title=row["title"],
                        content=row["content"],
                        content_html=row["content_html"],
                        slug=row["slug"],
                        published=row["published"],
                        published_at=row["published_at"],
                        author_id=row["author_id"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                        tags=row["tags"] if row["tags"][0] is not None else [],
                    )
                return None

            except Exception as e:
                logger.error(f"Error fetching post by slug: {e}")
                return None

    async def get_post_by_id(self, post_id: UUID) -> Optional[PostEntry]:
        """Get post by ID."""
        async with self._pool.acquire() as conn:
            try:
                row = await conn.fetchrow(
                    """
                    SELECT p.id, p.title, p.content, p.content_html, p.slug,
                           p.published, p.published_at, p.author_id,
                           p.created_at, p.updated_at,
                           array_agg(t.name) as tags
                    FROM posts p
                    LEFT JOIN post_tags pt ON p.id = pt.post_id
                    LEFT JOIN tags t ON pt.tag_id = t.id
                    WHERE p.id = $1
                    GROUP BY p.id
                """,
                    post_id,
                )

                if row:
                    return PostEntry(
                        id=row["id"],
                        title=row["title"],
                        content=row["content"],
                        content_html=row["content_html"],
                        slug=row["slug"],
                        published=row["published"],
                        published_at=row["published_at"],
                        author_id=row["author_id"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                        tags=row["tags"] if row["tags"][0] is not None else [],
                    )
                return None

            except Exception as e:
                logger.error(f"Error fetching post by ID: {e}")
                return None

    @cache_result(ttl=300)  # Cache for 5 minutes
    async def get_posts(
        self,
        limit: int = 10,
        offset: int = 0,
        published_only: bool = True,
        author_id: Optional[int] = None,
        search_query: Optional[str] = None,
    ) -> List[PostEntry]:
        """Get posts with caching."""
        async with self._pool.acquire() as conn:
            try:
                query = """
                    SELECT p.id, p.title, p.content, p.content_html, p.slug,
                           p.published, p.published_at, p.author_id,
                           p.created_at, p.updated_at,
                           array_agg(t.name) as tags
                    FROM posts p
                    LEFT JOIN post_tags pt ON p.id = pt.post_id
                    LEFT JOIN tags t ON pt.tag_id = t.id
                    WHERE 1=1
                """
                params = []
                if published_only:
                    query += " AND p.published = true"
                if author_id:
                    query += f" AND p.author_id = ${len(params) + 1}"
                    params.append(author_id)
                if search_query:
                    query += f" AND to_tsvector('english', p.title || ' ' || p.content) @@ plainto_tsquery('english', ${len(params) + 1})"
                    params.append(search_query)

                query += " GROUP BY p.id"
                query += " ORDER BY p.created_at DESC"
                query += f" LIMIT ${len(params) + 1}"
                params.append(limit)
                query += f" OFFSET ${len(params) + 1}"
                params.append(offset)

                rows = await conn.fetch(query, *params)
                return [
                    PostEntry(
                        id=row["id"],
                        title=row["title"],
                        content=row["content"],
                        content_html=row["content_html"],
                        slug=row["slug"],
                        published=row["published"],
                        published_at=row["published_at"],
                        author_id=row["author_id"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                        tags=row["tags"] if row["tags"][0] is not None else [],
                    )
                    for row in rows
                ]

            except Exception as e:
                logger.error(f"Error fetching posts: {e}")
                return []

    async def search_posts(
        self, query: str, limit: int = 10, offset: int = 0
    ) -> tuple[List[PostEntry], int]:
        """Search posts using PostgreSQL full-text search and return total count."""
        async with self._pool.acquire() as conn:
            try:
                total = await conn.fetchval(
                    """
                    SELECT COUNT(*)
                    FROM posts p
                    WHERE p.published = true
                    AND to_tsvector('english', p.title || ' ' || p.content) @@ plainto_tsquery('english', $1)
                    """,
                    query
                )

                rows = await conn.fetch(
                    """
                    SELECT p.id, p.title, p.content, p.content_html, p.slug,
                           p.published, p.published_at, p.author_id,
                           p.created_at, p.updated_at,
                           array_agg(t.name) as tags,
                           ts_rank(to_tsvector('english', p.title || ' ' || p.content), 
                                 plainto_tsquery('english', $1)) as rank
                    FROM posts p
                    LEFT JOIN post_tags pt ON p.id = pt.post_id
                    LEFT JOIN tags t ON pt.tag_id = t.id
                    WHERE p.published = true
                    AND to_tsvector('english', p.title || ' ' || p.content) @@ plainto_tsquery('english', $1)
                    GROUP BY p.id
                    ORDER BY rank DESC
                    LIMIT $2
                    OFFSET $3
                """,
                    query,
                    limit,
                    offset,
                )

                posts = [
                    PostEntry(
                        id=row["id"],
                        title=row["title"],
                        content=row["content"],
                        content_html=row["content_html"],
                        slug=row["slug"],
                        published=row["published"],
                        published_at=row["published_at"],
                        author_id=row["author_id"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                        tags=row["tags"] if row["tags"][0] is not None else [],
                    )
                    for row in rows
                ]

                return posts, total

            except Exception as e:
                logger.error(f"Error searching posts: {e}")
                return [], 0

    async def create_post(
        self, post: PostCreate, author_id: int, content_html: str
    ) -> Optional[PostEntry]:
        """Create a new post and invalidate relevant caches."""
        async with self._pool.acquire() as conn:
            try:
                async with conn.transaction():
                    now = datetime.utcnow()
                    row = await conn.fetchrow(
                        """
                        INSERT INTO posts (
                            title, content, content_html, slug, published,
                            published_at, author_id,
                            created_at, updated_at
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        RETURNING id, title, content, content_html, slug,
                                 published, published_at, author_id,
                                 created_at, updated_at
                        """,
                        post.title,
                        post.content,
                        content_html,
                        post.slug,
                        post.published,
                        datetime.utcnow() if post.published else None,
                        author_id,
                        now,
                        now,
                    )

                    # Create post entry
                    created_post = PostEntry(
                        id=row["id"],
                        title=row["title"],
                        content=row["content"],
                        content_html=row["content_html"],
                        slug=row["slug"],
                        published=row["published"],
                        published_at=row["published_at"],
                        author_id=row["author_id"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                        tags=post.tags,
                    )

                    # Add tags if any
                    if post.tags:
                        # Get or create tags
                        tag_ids = []
                        for tag_name in post.tags:
                            tag_row = await conn.fetchrow(
                                """
                                INSERT INTO tags (name)
                                VALUES ($1)
                                ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                                RETURNING id
                                """,
                                tag_name,
                            )
                            tag_ids.append(tag_row["id"])

                        # Link tags to post
                        await conn.executemany(
                            """
                            INSERT INTO post_tags (post_id, tag_id)
                            VALUES ($1, $2)
                            ON CONFLICT DO NOTHING
                            """,
                            [(created_post.id, tag_id) for tag_id in tag_ids],
                        )

                    # Invalidate caches
                    await self._redis.delete(f"posts:slug:{created_post.slug}")
                    await self._redis.delete(f"posts:id:{created_post.id}")
                    await self._redis.delete("posts:list")

                    return created_post

            except Exception as e:
                logger.error(f"Error creating post: {e}")
                return None

    async def update_post(
        self, post_id: UUID, post: PostCreate, content_html: str
    ) -> Optional[PostEntry]:
        """Update a post and invalidate relevant caches."""
        async with self._pool.acquire() as conn:
            try:
                async with conn.transaction():
                    current = await conn.fetchrow(
                        "SELECT published, published_at FROM posts WHERE id = $1",
                        post_id,
                    )
                    if not current:
                        return None

                    published_at = None
                    if post.published and not current["published"]:
                        published_at = datetime.now()
                    elif post.published:
                        published_at = current["published_at"]

                    row = await conn.fetchrow(
                        """
                        UPDATE posts
                        SET title = $1, content = $2, content_html = $3,
                            slug = $4, published = $5, published_at = $6,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = $7
                        RETURNING id, title, content, content_html, slug,
                                  published, published_at, author_id,
                                  created_at, updated_at
                    """,
                        post.title,
                        post.content,
                        content_html,
                        post.slug,
                        post.published,
                        published_at,
                        post_id,
                    )

                    # Update tags
                    await conn.execute(
                        "DELETE FROM post_tags WHERE post_id = $1", post_id
                    )

                    if post.tags:
                        for tag_name in post.tags:
                            tag_row = await conn.fetchrow(
                                """
                                INSERT INTO tags (name)
                                VALUES ($1)
                                ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                                RETURNING id
                            """,
                                tag_name,
                            )

                            await conn.execute(
                                """
                                INSERT INTO post_tags (post_id, tag_id)
                                VALUES ($1, $2)
                            """,
                                post_id,
                                tag_row["id"],
                            )

                # Get Redis cache instance and delete relevant keys
                await self._redis.delete("get_post_by_slug:*")
                await self._redis.delete("get_posts:*")

                if row:
                    return PostEntry(
                        id=row["id"],
                        title=row["title"],
                        content=row["content"],
                        content_html=row["content_html"],
                        slug=row["slug"],
                        published=row["published"],
                        published_at=row["published_at"],
                        author_id=row["author_id"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                        tags=post.tags,
                    )
                return None

            except Exception as e:
                logger.error(f"Error updating post: {e}")
                return None

    async def delete_post(self, post_id: UUID) -> bool:
        """Delete a post and invalidate relevant caches."""
        async with self._pool.acquire() as conn:
            try:
                result = await conn.execute(
                    """
                    DELETE FROM posts WHERE id = $1
                """,
                    post_id,
                )

                # Get Redis cache instance and delete relevant keys
                await self._redis.delete("get_post_by_slug:*")
                await self._redis.delete("get_posts:*")

                return "DELETE 1" in result

            except Exception as e:
                logger.error(f"Error deleting post: {e}")
                return False

    async def bulk_delete_posts(self, post_ids: List[UUID]) -> bool:
        """Delete multiple posts."""
        async with self._pool.acquire() as conn:
            try:
                result = await conn.execute(
                    """
                    DELETE FROM posts WHERE id = ANY($1)
                """,
                    post_ids,
                )

                # Get Redis cache instance and delete relevant keys
                await self._redis.delete("get_post_by_slug:*")
                await self._redis.delete("get_posts:*")

                return "DELETE" in result

            except Exception as e:
                logger.error(f"Error bulk deleting posts: {e}")
                return False
