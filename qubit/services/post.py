"""Post service."""

from typing import List, Optional
from uuid import UUID
import markdown
from loguru import logger

from qubit.models.post import PostCreate, PostEntry
from qubit.database.posts import PostsDB
from qubit.core.common import slugify


class PostService:
    """Post service."""

    def __init__(self, db: PostsDB):
        self.db = db
        self.md = markdown.Markdown(extensions=["fenced_code", "tables"])

    async def bulk_delete_posts(self, post_ids: List[UUID]) -> bool:
        """Delete multiple posts."""
        logger.info(f"Bulk deleting posts: ids={post_ids}")
        return await self.db.bulk_delete_posts(post_ids)

    async def create_post(
        self, post: PostCreate, author_id: int
    ) -> Optional[PostEntry]:
        """Create a new post."""
        logger.info(f"Creating post: title={post.title} author_id={author_id}")
        try:
            content_html = self.md.convert(post.content)

            if not post.slug:
                post.slug = slugify(post.title)

            return await self.db.create_post(post, author_id, content_html)
        except Exception as e:
            logger.error(f"Error creating post: {e}")
            raise

    async def get_posts(
        self,
        limit: int = 10,
        offset: int = 0,
        published_only: bool = True,
        author_id: Optional[int] = None,
    ) -> List[PostEntry]:
        """Get posts with pagination."""
        logger.info(
            f"Getting posts: limit={limit} offset={offset} published_only={published_only} author_id={author_id}"
        )
        return await self.db.get_posts(limit, offset, published_only, author_id)

    async def get_post(self, slug: str) -> Optional[PostEntry]:
        """Get post by slug."""
        logger.info(f"Getting post by slug: slug={slug}")
        return await self.db.get_post_by_slug(slug)

    async def search_posts(
        self, query: str, limit: int = 10, offset: int = 0
    ) -> tuple[List[PostEntry], int]:
        """Search posts."""
        logger.info(f"Searching posts: query={query} limit={limit} offset={offset}")
        return await self.db.search_posts(query, limit=limit, offset=offset)

    async def update_post(self, post_id: UUID, post: PostCreate) -> Optional[PostEntry]:
        """Update an existing post."""
        content_html = self.md.convert(post.content)

        logger.info(
            f"Updating post: id={post_id} title={post.title} published={post.published}"
        )
        return await self.db.update_post(post_id, post, content_html)

    async def delete_post(self, post_id: UUID) -> bool:
        """Delete a post."""
        logger.info(f"Deleting post: id={post_id}")
        return await self.db.delete_post(post_id)

    async def get_post_by_id(self, post_id: str) -> Optional[PostEntry]:
        """Get post by ID."""
        logger.info(f"Getting post by ID: id={post_id}")
        return await self.db.get_post_by_id(post_id)
