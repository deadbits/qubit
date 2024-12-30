"""API utilities."""

from typing import Any, Dict, Optional, TypeVar, Generic
from pydantic import BaseModel
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder


T = TypeVar("T")


class APIError(HTTPException):
    """Base API exception class."""

    def __init__(
        self, status_code: int, detail: str, headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class NotFoundError(APIError):
    """Resource not found error."""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class UnauthorizedError(APIError):
    """Unauthorized access error."""

    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ForbiddenError(APIError):
    """Forbidden access error."""

    def __init__(self, detail: str = "Not authorized"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ValidationError(APIError):
    """Validation error."""

    def __init__(self, detail: str = "Validation error"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail
        )


class APIResponse(BaseModel, Generic[T]):
    """Standard API response model."""

    success: bool = True
    data: Optional[T] = None
    error: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


def create_response(
    data: Optional[Any] = None,
    meta: Optional[Dict[str, Any]] = None,
    status_code: int = status.HTTP_200_OK,
) -> JSONResponse:
    """Create a standardized API response."""
    response = APIResponse(
        success=True,
        data=jsonable_encoder(data) if data is not None else None,
        meta=meta,
    )
    return JSONResponse(
        status_code=status_code, content=response.dict(exclude_none=True)
    )


async def handle_api_error(exc: APIError) -> JSONResponse:
    """Handle API exceptions."""
    response = APIResponse(success=False, error=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=response.dict(exclude_none=True),
        headers=exc.headers,
    )
