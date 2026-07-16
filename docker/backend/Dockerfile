# syntax=docker/dockerfile:1
#
# Multi-stage Dockerfile for the FastAPI backend.
# Build context is the REPO ROOT (see docker-compose.yml: context: .),
# so all COPY paths below are prefixed with backend/.
#
# Preserves backend/ as an actual subdirectory of WORKDIR (COPY backend/
# backend/, not COPY backend/ .) and runs `backend.main:app` from it —
# every internal import in backend/ is package-qualified as `backend.X`
# (see backend/README.md), which requires /app (the parent of /app/backend)
# on sys.path, not /app/backend itself.
#
# Build targets:
#   development — hot-reload dev server, source mounted as a bind volume
#   production  — immutable image with only installed deps + source baked in
#
# Usage (from repo root):
#   docker build -f docker/backend/Dockerfile --target development .
#   docker build -f docker/backend/Dockerfile --target production  .

# ---------------------------------------------------------------------------
# base: shared system deps for every stage
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# curl is required for the container HEALTHCHECK / compose healthcheck below
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# dependencies: install Python packages into a venv (cached layer)
# ---------------------------------------------------------------------------
FROM base AS dependencies

COPY backend/requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# development: hot-reload server, source provided via bind mount in compose
# ---------------------------------------------------------------------------
FROM dependencies AS development

ENV PATH="/opt/venv/bin:$PATH" \
    APP_ENV=development

# Source is bind-mounted by docker-compose.yml for live reload; COPY here
# only covers the initial build so the image is runnable standalone.
COPY backend/ backend/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ---------------------------------------------------------------------------
# production: immutable image, no reload, non-root user
# ---------------------------------------------------------------------------
FROM base AS production

ENV PATH="/opt/venv/bin:$PATH" \
    APP_ENV=production

COPY --from=dependencies /opt/venv /opt/venv
COPY backend/ backend/

# /app/uploads and /app/logs must exist (owned by appuser) *before* the
# named volumes in docker-compose.prod.yml are mounted over them — Docker
# only carries an image path's ownership into a freshly-created named
# volume if that path already existed in the image; otherwise the volume
# is initialized owned by root, and this non-root user can't write to it
# (verified: without this, the app crashes on startup with
# `PermissionError: [Errno 13] Permission denied: '/app/logs/app.log'`,
# taking every uvicorn worker down with it).
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /app/uploads /app/logs \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Worker count/binding to be tuned at deploy time.
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
