"""Authentication endpoints."""

from typing import Annotated
from fastapi import (
    APIRouter,
    Depends,
    Request,
    Response,
    Body,
)
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from starlette import status

from qubit.services.auth import AuthService
from qubit.core.common import get_users_db
from qubit.api.utils import (
    ForbiddenError,
    create_response,
)


router = APIRouter()


@router.post("/login")
async def login(
    request: Request,
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    """Login endpoint rate limited to 15 attempts per minute."""
    limiter = request.app.state.limiter

    @limiter.limit("15/minute")
    async def rate_limited_login(request: Request):
        db = get_users_db(request)
        auth_service = AuthService(db, request)
        user = await auth_service.authenticate_user(
            form_data.username, form_data.password
        )
        if not user:
            request.session["login_error"] = "invalid_credentials"
            return RedirectResponse(
                url="/login",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        auth_service.set_session_cookie(response, user.username, is_admin=user.is_admin)
        return RedirectResponse(url="/admin/hub", status_code=status.HTTP_303_SEE_OTHER)

    try:
        return await rate_limited_login(request)
    except Exception as e:
        if "Retry-After" in str(e):
            request.session["login_error"] = "too_many_attempts"
            return RedirectResponse(
                url="/login",
                status_code=status.HTTP_303_SEE_OTHER,
            )
        raise


@router.post("/logout")
async def logout(request: Request, response: Response):
    """Logout endpoint."""
    db = get_users_db(request)
    auth_service = AuthService(db, request)
    auth_service.clear_session(response)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/admin/check")
async def check_admin_access(request: Request):
    """Check if user has admin access."""
    db = get_users_db(request)
    auth_service = AuthService(db, request)
    is_admin = await auth_service.check_admin_access()
    if not is_admin:
        raise ForbiddenError()
    return create_response(data={"is_admin": True})
