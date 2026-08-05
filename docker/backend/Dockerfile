# syntax=docker/dockerfile:1
#
# Multi-stage Dockerfile for the FastAPI backend.
#

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# dependencies
# ---------------------------------------------------------------------------

FROM base AS dependencies

COPY backend/requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# development
# ---------------------------------------------------------------------------

FROM dependencies AS development

ENV PATH="/opt/venv/bin:$PATH" \
    APP_ENV=development

COPY backend/ backend/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ---------------------------------------------------------------------------
# production
# ---------------------------------------------------------------------------

FROM base AS production

ENV PATH="/opt/venv/bin:$PATH" \
    APP_ENV=production

COPY --from=dependencies /opt/venv /opt/venv
COPY backend/ backend/

RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /app/uploads /app/logs \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]