"""Aggregate router for API version 1.

Feature routers are registered here as they are implemented, e.g.:

    from api.v1.endpoints import policies
    api_router.include_router(policies.router, prefix="/policies", tags=["Policies"])
"""

from fastapi import APIRouter, Depends

from api.dependencies.common import get_app_settings
from api.v1.endpoints import policies, uploads
from config.settings import Settings

api_router = APIRouter()

api_router.include_router(policies.router, prefix="/policies", tags=["Policies"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["Uploads"])


@api_router.get("/", tags=["Meta"], summary="API version metadata")
def api_metadata(settings: Settings = Depends(get_app_settings)) -> dict:
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "api_version": "v1",
    }
