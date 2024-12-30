"""Post API endpoints."""

from typing import List, Annotated
from uuid import UUID
import json
from fastapi import APIRouter, Depends, Request, Query, Path, Body
from fastapi.responses import JSONResponse
from starlette import status

from qubit.services.post import PostService
from qubit.services.auth import AuthService
from qubit.models.post import PostCreate, PostEntry
from qubit.database.posts import PostsDB
from qubit.core.common import get_posts_db, get_users_db
from qubit.api.utils import (
    NotFoundError,
    UnauthorizedError,
    create_response,
)


router = APIRouter()


@router.post("/admin/posts/bulk-delete")
async def bulk_delete_posts(
    ids: Annotated[
        List[UUID], Body(min_length=1, description="List of post IDs to delete")
    ],
    request: Request,
    db: PostsDB = Depends(get_posts_db),
):
    """Delete multiple posts (admin only)."""
    users_db = get_users_db(request)
    auth_service = AuthService(users_db, request)
    user = await auth_service.get_current_user()
    if not user:
        raise UnauthorizedError()

    post_service = PostService(db)
    success = await post_service.bulk_delete_posts(ids)
    if not success:
        raise NotFoundError("One or more posts not found")

    return create_response({"status": "success"})


@router.get("/posts")
async def get_posts(
    request: Request,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    limit: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 10,
    db: PostsDB = Depends(get_posts_db),
):
    """Get all published posts."""
    post_service = PostService(db)
    offset = (page - 1) * limit
    posts = await post_service.get_posts(limit=limit, offset=offset)

    posts_dict = [post.to_dict() for post in posts]
    years = {}
    for post in posts_dict:
        year = post["created_at"].split("-")[0]
        if year not in years:
            years[year] = []
        years[year].append(post)

    return create_response(
        data={
            "posts": posts_dict,
            "years": years,
        },
        meta={
            "page": page,
            "total_pages": (len(posts) + limit - 1) // limit,
        },
    )


@router.get("/posts/search")
async def search_posts(
    request: Request,
    q: Annotated[str, Query(min_length=3, max_length=50, description="Search query")],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    limit: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 10,
    db: PostsDB = Depends(get_posts_db),
):
    """Search posts."""
    post_service = PostService(db)
    offset = (page - 1) * limit
    posts, total = await post_service.search_posts(q, limit=limit, offset=offset)

    posts_dict = [post.to_dict() for post in posts]
    years = {}
    for post in posts_dict:
        year = post["created_at"].split("-")[0]
        if year not in years:
            years[year] = []
        years[year].append(post)

    return create_response(
        data={
            "posts": posts_dict,
            "years": years,
        },
        meta={
            "total_pages": (total + limit - 1) // limit,
        },
    )


@router.get("/posts/{slug}", response_model=PostEntry)
async def get_post(
    slug: Annotated[str, Path(min_length=1, max_length=100, description="Post slug")],
    db: PostsDB = Depends(get_posts_db),
):
    """Get post by slug."""
    post_service = PostService(db)
    post = await post_service.get_post(slug)
    if not post:
        raise NotFoundError("Post not found")
    return create_response(data=post)


@router.post("/admin/posts", response_model=PostEntry)
async def create_post(
    post: Annotated[PostCreate, Body(description="Post data")],
    request: Request,
    db: PostsDB = Depends(get_posts_db),
):
    """Create new post (admin only)."""
    users_db = get_users_db(request)
    auth_service = AuthService(users_db, request)
    user = await auth_service.get_current_user()
    if not user:
        raise UnauthorizedError()

    post_service = PostService(db)
    created_post = await post_service.create_post(post, user.id)
    return create_response(data=created_post, status_code=status.HTTP_201_CREATED)


@router.put("/admin/posts/{post_id}", response_model=PostEntry)
async def update_post(
    post_id: Annotated[UUID, Path(description="Post ID")],
    post: Annotated[PostCreate, Body(description="Updated post data")],
    db: PostsDB = Depends(get_posts_db),
):
    """Update existing post (admin only)."""
    post_service = PostService(db)
    updated_post = await post_service.update_post(post_id, post)
    if not updated_post:
        raise NotFoundError("Post not found")
    return create_response(data=updated_post)


@router.delete("/admin/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: Annotated[UUID, Path(description="Post ID")],
    db: PostsDB = Depends(get_posts_db),
):
    """Delete post (admin only)."""
    post_service = PostService(db)
    if not await post_service.delete_post(post_id):
        raise NotFoundError("Post not found")
    return create_response(status_code=status.HTTP_204_NO_CONTENT)
