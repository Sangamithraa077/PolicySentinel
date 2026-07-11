"""Global exception types and handlers.

Defines a generic, HTTP-semantics exception hierarchy and registers
FastAPI exception handlers that translate them (plus validation errors
and unhandled exceptions) into a consistent JSON error envelope:

    {"error": {"code": "...", "message": "...", "details": ...}}

No business-rule exceptions live here — those belong in domain/exceptions/.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Base class for application-level exceptions mapped to HTTP responses."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "internal_error"

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        error_code: str | None = None,
    ) -> None:
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code
        super().__init__(message)


class NotFoundError(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "not_found"


class BadRequestError(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "bad_request"


class UnauthorizedError(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "unauthorized"


class ForbiddenError(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "forbidden"


def _error_response(
    status_code: int, error_code: str, message: str, details: object = None
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": error_code, "message": message, "details": details}},
    )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.warning("Handled application exception [%s]: %s", exc.error_code, exc.message)
    return _error_response(exc.status_code, exc.error_code, exc.message)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _error_response(exc.status_code, "http_error", str(exc.detail))


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return _error_response(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "validation_error",
        "Request validation failed",
        details=exc.errors(),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception while processing request")
    return _error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR, "internal_error", "An unexpected error occurred"
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
