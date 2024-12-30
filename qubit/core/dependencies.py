"""Common dependencies for API and web routes."""

from typing import Optional, Union
from fastapi import Request, HTTPException, status
from loguru import logger

from qubit.models.user import UserDB
from qubit.services.auth import AuthService
from qubit.core.common import get_users_db


async def get_current_user(
    request: Request,
    raise_on_missing: bool = False,
    return_model: bool = False,
) -> Union[Optional[UserDB], Optional[dict]]:
    """Get current user from session."""
    db = get_users_db(request)
    auth_service = AuthService(db, request)

    try:
        user = await auth_service.get_current_user()
        if not user and raise_on_missing:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

        if user and not return_model:
            return user.model_dump()

        return user

    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        if raise_on_missing:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            ) from e
        return None
