"""Global exception types and handlers.

Defines a generic, HTTP-semantics exception hierarchy and registers
FastAPI exception handlers that translate them (plus validation errors
and unhandled exceptions) into a consistent JSON error envelope:

    {"error": {"code": "...", "message": "...", "details": ...}}

No business-rule exceptions live here — those belong in domain/exceptions/.
"""

import logging
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from domain.exceptions.file_storage_exceptions import FileStorageError
from domain.exceptions.policy_exceptions import (
    CompanyNotFoundError,
    PolicyNotFoundError,
    PolicyVersionNotFoundError,
    UserNotFoundError,
)
from domain.exceptions.upload_exceptions import (
    FileTooLargeError,
    InvalidFileContentError,
    UnsupportedFileTypeError,
)

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


async def catch_unhandled_exceptions_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Last-resort catch-all for exceptions no registered handler catches.

    Deliberately middleware, not `add_exception_handler(Exception, ...)`:
    Starlette pulls a handler registered for the bare `Exception` class
    out to `ServerErrorMiddleware`, which sits *outside* CORSMiddleware —
    so a response built that way never gets a CORS header, and a
    cross-origin caller sees an opaque network error instead of the
    actual status/body (verified directly: a 500 from that path came
    back with no `Access-Control-Allow-Origin` at all, while every
    exception-handler-based 4xx response had one). Catching here as
    middleware placed inside CORSMiddleware (see main.py's registration
    order — this one must be added *before* CORSMiddleware) keeps error
    responses on the same footing as everything else.
    """
    try:
        return await call_next(request)
    except Exception:
        logger.exception("Unhandled exception while processing request")
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "internal_error", "An unexpected error occurred"
        )


async def unsupported_file_type_handler(
    request: Request, exc: UnsupportedFileTypeError
) -> JSONResponse:
    return _error_response(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "unsupported_file_type", str(exc)
    )


async def file_too_large_handler(request: Request, exc: FileTooLargeError) -> JSONResponse:
    return _error_response(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "file_too_large", str(exc))


async def invalid_file_content_handler(
    request: Request, exc: InvalidFileContentError
) -> JSONResponse:
    return _error_response(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "invalid_file_content", str(exc))


async def company_not_found_handler(request: Request, exc: CompanyNotFoundError) -> JSONResponse:
    return _error_response(status.HTTP_404_NOT_FOUND, "company_not_found", str(exc))


async def user_not_found_handler(request: Request, exc: UserNotFoundError) -> JSONResponse:
    return _error_response(status.HTTP_404_NOT_FOUND, "user_not_found", str(exc))


async def policy_not_found_handler(request: Request, exc: PolicyNotFoundError) -> JSONResponse:
    return _error_response(status.HTTP_404_NOT_FOUND, "policy_not_found", str(exc))


async def policy_version_not_found_handler(
    request: Request, exc: PolicyVersionNotFoundError
) -> JSONResponse:
    return _error_response(status.HTTP_404_NOT_FOUND, "policy_version_not_found", str(exc))


async def file_storage_error_handler(request: Request, exc: FileStorageError) -> JSONResponse:
    logger.error("File storage error: %s", exc)
    return _error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "file_storage_error", str(exc))


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(UnsupportedFileTypeError, unsupported_file_type_handler)
    app.add_exception_handler(FileTooLargeError, file_too_large_handler)
    app.add_exception_handler(InvalidFileContentError, invalid_file_content_handler)
    app.add_exception_handler(CompanyNotFoundError, company_not_found_handler)
    app.add_exception_handler(UserNotFoundError, user_not_found_handler)
    app.add_exception_handler(PolicyNotFoundError, policy_not_found_handler)
    app.add_exception_handler(PolicyVersionNotFoundError, policy_version_not_found_handler)
    app.add_exception_handler(FileStorageError, file_storage_error_handler)
    # No app.add_exception_handler(Exception, ...) here -- see
    # catch_unhandled_exceptions_middleware's docstring for why that
    # specific registration is deliberately avoided.
