"""Web routes."""

from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette import status
from loguru import logger

from qubit.services.auth import AuthService
from qubit.services.post import PostService
from qubit.core.common import get_users_db, get_posts_db
from qubit.core.dependencies import get_current_user


LOGIN_ERROR_MESSAGES = {
    "invalid_credentials": "Invalid username or password",
    "too_many_attempts": "Too many login attempts. Please try again later.",
}


async def get_admin_status(request: Request) -> bool:
    """Get admin status from session."""
    db = get_users_db(request)
    auth_service = AuthService(db, request)
    return await auth_service.check_admin_access()


async def feed(request: Request) -> HTMLResponse:
    """Feed page."""
    templates = request.app.state.templates
    user = await get_current_user(request)
    return templates.TemplateResponse("feed.html", {"request": request, "user": user})


async def list_posts(request: Request) -> HTMLResponse:
    """List all posts."""
    templates = request.app.state.templates
    db = get_posts_db(request)
    user = await get_current_user(request)
    post_service = PostService(db)
    posts = await post_service.get_posts(
        limit=100,
        offset=0,
        published_only=True,
    )
    logger.debug(f"Found {len(posts)} published posts for index")

    years = {}
    for post in posts:
        year = post.created_at.strftime("%Y")
        if year not in years:
            years[year] = []
        years[year].append(post)

    return templates.TemplateResponse(
        "posts.html", {"request": request, "user": user, "posts": posts, "years": years}
    )


async def view_post(request: Request, post_id: str) -> HTMLResponse:
    """View single post."""
    templates = request.app.state.templates
    db = get_posts_db(request)
    user = await get_current_user(request)
    post_service = PostService(db)
    post = await post_service.get_post_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return templates.TemplateResponse(
        "post.html",
        {"request": request, "post_id": post_id, "user": user, "post": post},
    )


async def writer_hub(request: Request) -> HTMLResponse:
    """Writer hub page."""
    templates = request.app.state.templates
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    db = get_posts_db(request)
    post_service = PostService(db)
    drafts = await post_service.get_posts(
        limit=100,
        offset=0,
        published_only=False,
        author_id=user["id"],
    )

    drafts = [post for post in drafts if not post.published]
    logger.debug(f"Found {len(drafts)} drafts")

    published = await post_service.get_posts(
        limit=100,
        offset=0,
        published_only=True,
        author_id=user["id"],
    )
    logger.debug(f"Found {len(published)} published posts")

    return templates.TemplateResponse(
        "hub/index.html",
        {
            "request": request,
            "user": user,
            "drafts": drafts,
            "published": published,
            "config": request.app.state.config,
        },
    )


async def hub_new_post(request: Request) -> HTMLResponse:
    """New post page."""
    templates = request.app.state.templates
    user = await get_current_user(request)
    return templates.TemplateResponse(
        "hub/write.html", {"request": request, "user": user}
    )


async def hub_edit_post(request: Request, post_id: str) -> HTMLResponse:
    """Edit post page."""
    templates = request.app.state.templates
    db = get_posts_db(request)
    user = await get_current_user(request)
    post_service = PostService(db)
    post = await post_service.get_post_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return templates.TemplateResponse(
        "hub/write.html", {"request": request, "user": user, "post": post}
    )


async def about(request: Request) -> HTMLResponse:
    """About page."""
    templates = request.app.state.templates
    user = await get_current_user(request)
    return templates.TemplateResponse(
        "about.html",
        {"request": request, "author": request.app.state.config.author, "user": user},
    )


async def login(request: Request) -> HTMLResponse:
    """Admin login page."""
    templates = request.app.state.templates
    user = await get_current_user(request)

    error_code = request.session.pop("login_error", None)
    error = LOGIN_ERROR_MESSAGES.get(error_code) if error_code else None

    return templates.TemplateResponse(
        "login.html", {"request": request, "user": user, "error": error}
    )


async def admin_settings(request: Request) -> HTMLResponse:
    """Admin settings page."""
    templates = request.app.state.templates
    user = await get_current_user(request)
    return templates.TemplateResponse(
        "admin/settings.html",
        {"request": request, "config": request.app.state.config, "user": user},
    )
