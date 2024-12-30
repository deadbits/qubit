"""Feed API endpoints."""

from typing import List, Annotated
from uuid import UUID
from fastapi import (
    APIRouter,
    Request,
    Depends,
    Query,
    Path,
    Body,
)

from qubit.models.feed import FeedEntry, FeedEntryCreate
from qubit.services.feed import FeedService
from qubit.services.auth import AuthService
from qubit.core.common import get_feed_db, get_users_db
from qubit.api.utils import (
    NotFoundError,
    ForbiddenError,
    create_response,
)


router = APIRouter()


async def get_feed_service(request: Request) -> FeedService:
    """Get feed service instance."""
    db = get_feed_db(request)
    return FeedService(db)


async def check_admin_access(request: Request):
    """Check if user has admin access."""
    users_db = get_users_db(request)
    auth_service = AuthService(users_db, request)
    if not await auth_service.check_admin_access():
        raise ForbiddenError("Admin access required")
    return await auth_service.get_current_user()


@router.get("/feed", response_model=List[FeedEntry])
async def get_feed_posts(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    offset: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
    feed_service: FeedService = Depends(get_feed_service),
):
    """Get feed posts."""
    posts = await feed_service.get_posts(limit=limit, offset=offset)
    return create_response(
        data=posts,
        meta={
            "limit": limit,
            "offset": offset,
            "total": len(posts)
        }
    )


@router.post("/admin/feed", response_model=FeedEntry)
async def create_feed_post(
    request: Request,
    post: Annotated[FeedEntryCreate, Body(description="Feed post data")],
    feed_service: FeedService = Depends(get_feed_service),
    user=Depends(check_admin_access),
):
    """Create a new feed post."""
    created_post = await feed_service.create_post(post, user.id, user.username)
    return create_response(data=created_post)


@router.delete("/admin/feed/{post_id}")
async def delete_feed_post(
    request: Request,
    post_id: Annotated[UUID, Path(description="Feed post ID")],
    feed_service: FeedService = Depends(get_feed_service),
    user=Depends(check_admin_access),
):
    """Delete a feed post."""
    success = await feed_service.delete_post(post_id)
    if not success:
        raise NotFoundError("Post not found")
    return create_response(data={"status": "success"})
