# docker/backend/ — FastAPI Container

`Dockerfile` is a multi-stage build with two targets:

| Target | Used by | Behavior |
|---|---|---|
| `development` | `docker-compose.yml` | Installs deps, runs `uvicorn --reload`; source is bind-mounted from `../backend` for live reload |
| `production` | `docker-compose.prod.yml` | Copies only the installed venv + source into the image, runs as non-root user, no reload, multiple workers |

Build context is the **repo root** (not `backend/`) so the image build can be invoked consistently from `docker-compose.yml` at the project root. See comments at the top of `Dockerfile` for manual build commands.

A container `HEALTHCHECK` hits `GET /health`, served by [backend/api/health.py](../../backend/api/health.py) (mounted unversioned, outside `/api/v1`, since liveness/readiness probes are infrastructure, not part of the public API contract).

Base image: `python:3.11-slim` (see backend/.python-version).
