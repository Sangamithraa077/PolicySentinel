"""Health check endpoint.

Mounted at the application root (unversioned) rather than under
/api/v1, since liveness/readiness probes (Docker, Kubernetes, load
balancers) are an infrastructure concern, not part of the versioned
public API contract.

Reports readiness, not just liveness: a 503 here means "don't route
traffic here yet/anymore" (e.g. Postgres unreachable), distinct from the
process being alive at all.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Response, status

from backend.api.dependencies.common import get_app_settings
from backend.config.settings import Settings
from backend.database.health import check_database_connection

router = APIRouter()


@router.get("/health", tags=["Health"], summary="Liveness / readiness health check")
def health_check(response: Response, settings: Settings = Depends(get_app_settings)) -> dict:
    database_ok = check_database_connection()
    response.status_code = (
        status.HTTP_200_OK if database_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return {
        "status": "ok" if database_ok else "degraded",
        "environment": settings.APP_ENV,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(UTC).isoformat(),
        "dependencies": {
            "database": "ok" if database_ok else "unreachable",
        },
    }
