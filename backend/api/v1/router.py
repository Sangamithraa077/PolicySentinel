"""Aggregate router for API version 1.

Feature routers are registered here as they are implemented, e.g.:

    from backend.api.v1.endpoints import policies
    api_router.include_router(policies.router, prefix="/policies", tags=["Policies"])
"""

from fastapi import APIRouter, Depends

from backend.api.dependencies.common import get_app_settings
from backend.api.v1.endpoints import clauses, debug, policies, uploads, obligations, comparison, conflicts, recommendations, compliance_dashboard, relationships, findings, regulatory_mappings, graph
from backend.config.settings import Settings

api_router = APIRouter()

api_router.include_router(policies.router, prefix="/policies", tags=["Policies"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["Uploads"])
api_router.include_router(clauses.router, prefix="/clauses", tags=["Clauses"])
api_router.include_router(obligations.router, prefix="/obligations", tags=["Obligations"])
api_router.include_router(comparison.router, prefix="/comparison", tags=["Comparison"])
api_router.include_router(conflicts.router, prefix="/conflicts", tags=["Conflicts"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
api_router.include_router(compliance_dashboard.router, prefix="/compliance-dashboard", tags=["Compliance Dashboard"])
api_router.include_router(relationships.router, prefix="/relationships", tags=["Relationships"])
api_router.include_router(findings.router, prefix="/findings", tags=["Findings"])
api_router.include_router(regulatory_mappings.router, prefix="/regulatory-mappings", tags=["Regulatory Mappings"])
api_router.include_router(graph.router, prefix="/graph", tags=["Knowledge Graph"])
api_router.include_router(debug.router, prefix="/debug", tags=["Debug"])


@api_router.get("/", tags=["Meta"], summary="API version metadata")
def api_metadata(settings: Settings = Depends(get_app_settings)) -> dict:
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "api_version": "v1",
    }
