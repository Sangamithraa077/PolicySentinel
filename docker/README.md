# docker/ — Container Build Contexts

Per-service Dockerfiles and container-specific config, orchestrated together by the root `docker-compose.yml` (development) and `docker-compose.prod.yml` (production overlay placeholder).

- `backend/` — multi-stage Dockerfile for the FastAPI service (`development` / `production` targets). See [backend/README.md](backend/README.md).
- `frontend/` — multi-stage Dockerfile for the React app + `nginx.conf` for production serving. See [frontend/README.md](frontend/README.md).
- `postgres/` — `init/` scripts run once against a fresh PostgreSQL volume. See [postgres/README.md](postgres/README.md).
- `neo4j/` — `conf/` overrides mounted into the Neo4j container. See [neo4j/README.md](neo4j/README.md).

## Build context note

Both `backend/Dockerfile` and `frontend/Dockerfile` are built with the **repo root** as build context (not `backend/`/`frontend/` individually), so the frontend's production stage can pull `docker/frontend/nginx.conf` without crossing outside the Docker build context. See `docker-compose.yml` (`build.context: .`).

## Where the rest of the Docker config lives

- Root `docker-compose.yml` — development stack: networking, volumes, health checks, hot reload
- Root `docker-compose.prod.yml` — production-shape overlay (placeholder — no secrets manager wired up yet)
- Root `.env.example` — all environment variables consumed by the compose files
- Root `.dockerignore` — build context exclusions shared by both image builds
