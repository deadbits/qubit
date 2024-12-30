"""Authentication middleware."""

from typing import Callable
from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse
from starlette import status
from loguru import logger

from qubit.services.auth import AuthService
from qubit.core.common import get_users_db


UNPROTECTED_PATHS = {
    "/",
    "/login",
    "/api/login",
    "/api/logout",
    "/about",
    "/posts",
    "/static",
    "/api/posts/search",
}


async def admin_required(request: Request, call_next: Callable):
    """Middleware to protect admin routes."""
    path = request.url.path

    if path in UNPROTECTED_PATHS or any(
        path.startswith(p) for p in ["/static/", "/posts/"]
    ):
        return await call_next(request)

    requires_admin = path.startswith("/api/admin") or path.startswith("/admin")
    if not requires_admin:
        return await call_next(request)

    db = get_users_db(request)
    auth_service = AuthService(db, request)

    try:
        current_user = await auth_service.get_current_user()

        if not current_user:
            if path.startswith("/api/"):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Not authenticated"},
                )
            return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

        is_admin = await auth_service.check_admin_access()
        if not is_admin:
            if path.startswith("/api/"):
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Not authorized"},
                )
            return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

        request.state.user = current_user
        return await call_next(request)

    except Exception as e:
        logger.error(f"Error in admin middleware: {e}")
        if path.startswith("/api/"):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": str(e)},
            )
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
