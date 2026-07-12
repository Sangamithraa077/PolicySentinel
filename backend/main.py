"""FastAPI application entrypoint.

Wires together configuration, logging, CORS, global exception handling,
the health check endpoint, versioned API routing, and the startup/shutdown
lifespan — the backend foundation only. No business logic is registered
here.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.health import router as health_router
from backend.api.v1.router import api_router
from backend.config.settings import get_settings
from backend.core.exceptions import (
    catch_unhandled_exceptions_middleware,
    register_exception_handlers,
)
from backend.core.lifespan import lifespan
from backend.core.logging import configure_logging

settings = get_settings()
configure_logging(settings)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.APP_DEBUG,
        lifespan=lifespan,
    )

    # Registered before CORSMiddleware deliberately: Starlette's add_middleware
    # prepends, so whichever of these is added *second* ends up outermost.
    # CORSMiddleware needs to be outermost so it can still attach CORS
    # headers to the error responses this middleware builds (see
    # catch_unhandled_exceptions_middleware's docstring).
    application.middleware("http")(catch_unhandled_exceptions_middleware)

    # Configure CORS to allow cross-origin requests from the frontend dev servers
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(application)

    application.include_router(health_router)
    application.include_router(api_router, prefix=settings.API_V1_PREFIX)

    return application


app = create_app()


