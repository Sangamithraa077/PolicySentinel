"""Health check endpoint.

Mounted at the application root (unversioned) rather than under
/api/v1, since liveness/readiness probes (Docker, Kubernetes, load
balancers) are an infrastructure concern, not part of the versioned
public API contract.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from api.dependencies.common import get_app_settings
from config.settings import Settings

router = APIRouter()


@router.get("/health", tags=["Health"], summary="Liveness / readiness health check")
def health_check(settings: Settings = Depends(get_app_settings)) -> dict:
    return {
        "status": "ok",
        "environment": settings.APP_ENV,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
