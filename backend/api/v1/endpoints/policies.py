"""Policy management endpoints — list, detail, download, soft-delete.

Only orchestrates: calls into `services/policy_management_service.py`
and shapes the response. No document parsing, no AI.
"""

from __future__ import annotations

import uuid
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query, Response, status

from backend.api.dependencies.policies import get_policy_management_service
from backend.models.enums import PolicyStatus
from backend.models.policy import Policy
from backend.models.policy_version import PolicyVersion
from backend.schemas.policies import (
    PolicyDetail,
    PolicyListResponse,
    PolicySummary,
    PolicyVersionSummary,
)
from backend.services.policy_management_service import PolicyManagementService

router = APIRouter()


def _version_summary(version: PolicyVersion, *, is_current: bool) -> PolicyVersionSummary:
    return PolicyVersionSummary(
        id=version.id,
        version_number=version.version_number,
        status=version.status.value,
        original_filename=version.original_filename,
        file_type=version.file_type.value,
        size_bytes=version.size_bytes,
        description=version.description,
        uploaded_by_user_id=version.uploaded_by_user_id,
        uploaded_at=version.uploaded_at,
        is_current=is_current,
    )


def _current_version_summary(policy: Policy) -> PolicyVersionSummary | None:
    if policy.current_version is None:
        return None
    return _version_summary(policy.current_version, is_current=True)


def _policy_summary(policy: Policy) -> PolicySummary:
    return PolicySummary(
        id=policy.id,
        company_id=policy.company_id,
        company_name=policy.company.name if policy.company else None,
        title=policy.title,
        policy_code=policy.policy_code,
        category=policy.category,
        status=policy.status.value,
        current_version=_current_version_summary(policy),
        created_at=policy.created_at,
        updated_at=policy.updated_at,
    )


def _policy_detail(policy: Policy, versions: list[PolicyVersion]) -> PolicyDetail:
    return PolicyDetail(
        id=policy.id,
        company_id=policy.company_id,
        company_name=policy.company.name if policy.company else None,
        title=policy.title,
        policy_code=policy.policy_code,
        category=policy.category,
        status=policy.status.value,
        current_version=_current_version_summary(policy),
        created_at=policy.created_at,
        updated_at=policy.updated_at,
        owning_department_id=policy.owning_department_id,
        versions=[
            _version_summary(v, is_current=(v.id == policy.current_version_id)) for v in versions
        ],
    )


def _content_disposition(filename: str) -> str:
    # Both forms are sent: a quoted-and-sanitized ASCII fallback for older
    # clients, and the properly percent-encoded UTF-8 form (RFC 5987) for
    # everything else. `original_filename` is client-supplied and stored
    # verbatim at upload time, so the fallback must strip C0 control
    # characters (not just quotes) -- otherwise an embedded CR/LF would
    # land unescaped in this header value, opening the door to HTTP
    # response-splitting / header injection. quote() already
    # percent-encodes everything unsafe for the filename*= form.
    ascii_fallback = "".join(
        "_" if ch == '"' or ord(ch) < 0x20 or ord(ch) == 0x7F else ch
        for ch in filename.encode("ascii", errors="replace").decode("ascii")
    )
    encoded = quote(filename)
    return f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{encoded}"


@router.get("", response_model=PolicyListResponse, summary="List uploaded policies")
def list_policies(
    company_id: uuid.UUID | None = Query(None, description="Filter by company"),
    status_filter: PolicyStatus | None = Query(
        None, alias="status", description="Filter by policy status"
    ),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: PolicyManagementService = Depends(get_policy_management_service),
) -> PolicyListResponse:
    items, total = service.list_policies(
        company_id=company_id, status=status_filter, limit=limit, offset=offset
    )
    return PolicyListResponse(
        items=[_policy_summary(policy) for policy in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{policy_id}", response_model=PolicyDetail, summary="Get policy details")
def get_policy(
    policy_id: uuid.UUID,
    service: PolicyManagementService = Depends(get_policy_management_service),
) -> PolicyDetail:
    policy, versions = service.get_policy(policy_id)
    return _policy_detail(policy, versions)


@router.get("/{policy_id}/download", summary="Download a policy document")
def download_policy(
    policy_id: uuid.UUID,
    version_number: int | None = Query(
        None, ge=1, description="Specific version to download; defaults to the current version"
    ),
    service: PolicyManagementService = Depends(get_policy_management_service),
) -> Response:
    download = service.get_download(policy_id, version_number)
    return Response(
        content=download.content,
        media_type=download.content_type,
        headers={"Content-Disposition": _content_disposition(download.filename)},
    )


@router.delete(
    "/{policy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a policy (soft delete)",
)
def delete_policy(
    policy_id: uuid.UUID,
    service: PolicyManagementService = Depends(get_policy_management_service),
) -> None:
    service.delete_policy(policy_id)
