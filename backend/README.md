# backend/ — FastAPI Service (Clean Architecture)

Python/FastAPI backend for PolicySentinel. Organized into four Clean Architecture layers:

| Layer | Folders |
|---|---|
| **Presentation** | `api/`, `middleware/` |
| **Application** | `services/`, `schemas/` |
| **Domain** | `domain/` (entities, interfaces, exceptions) |
| **Infrastructure** | `database/`, `models/`, `repositories/`, `ai/`, `graph/`, `reasoning/`, `auth/`, `parsing/` |

Cross-cutting: `core/`, `config/`, `utils/`, `uploads/`, `logs/`.

## Dependency rule
Dependencies only point inward: `api` → `services` → `domain` ← `repositories`/`ai`/`graph`/`reasoning` (via `domain/interfaces/`). `domain/` never imports from any other layer.

## Status

The application **foundation** is implemented: `main.py`, `config/` (settings), `core/` (logging, exceptions, lifespan), and `api/` (health check, versioned routing mount point, shared dependencies). No business logic, persistence, AI, graph, or reasoning code exists yet — those folders remain scaffolds.

## Running locally (without Docker)

Requires Python 3.11 (see `.python-version`).

Every internal import in `backend/` is package-qualified (e.g. `from backend.config.settings import ...`), so `backend` must be run as a package with the **repo root** — not `backend/` itself — on `sys.path`. In practice that just means: install dependencies from inside `backend/`, but run `uvicorn` from the repo root, one level up.

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
cd ..
copy .env.example .env        # then fill in real values
uvicorn backend.main:app --reload
```

Visit `http://localhost:8000/health` and `http://localhost:8000/api/v1/`.

## Running via Docker

See root `docker-compose.yml` — `docker compose up backend` builds the `development` target (hot reload) automatically.

