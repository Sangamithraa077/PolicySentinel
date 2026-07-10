# PolicySentinel

**AI-Powered Policy Conflict, Redundancy & Staleness Detection Platform for Financial Institutions**

> Hackathon project scaffold. This repository currently contains **only the project folder structure** — no business logic, AI integration, or API implementation has been added yet.

## Overview

PolicySentinel is designed to help financial institutions detect:
- **Conflicts** between policies (contradictory rules across documents/departments)
- **Redundancies** (duplicate or overlapping policy language)
- **Staleness** (policies referencing outdated regulations, dates, or terminology)

using a combination of a Neo4j knowledge graph, Graph RAG, the Claude API, and the Z3 formal solver for provable logical conflict detection.

## Architecture

The system follows **Clean Architecture**, with strict inward dependency direction:

```
Presentation Layer   (backend/api, backend/middleware, frontend/)
        ↓
Application Layer    (backend/services, backend/schemas)
        ↓
Domain Layer         (backend/domain)  ← the core, zero external dependencies
        ↑
Infrastructure Layer (backend/database, backend/models, backend/repositories,
                       backend/ai, backend/graph, backend/reasoning, backend/auth)
```

Infrastructure implements the interfaces (`backend/domain/interfaces/`) that the Domain and Application layers depend on — never the reverse.

## Tech Stack

| Concern | Technology |
|---|---|
| Frontend | React |
| Backend | FastAPI (Python) |
| Relational DB | PostgreSQL |
| Knowledge Graph | Neo4j |
| AI Reasoning | Claude API + Graph RAG |
| Formal Verification | Z3 Solver |
| Auth | JWT |
| Containerization | Docker / docker-compose |

## Repository Layout

```
PolicySentinel/
├── backend/        FastAPI service (Clean Architecture layers)
├── frontend/       React application
├── docker/         Per-service Dockerfiles
├── docs/           Architecture docs, API docs, setup guides
├── scripts/        Setup, migration, and deployment scripts
├── tests/          Backend and frontend automated tests
├── docker-compose.yml
├── .env.example
└── .gitignore
```

See the `README.md` inside each top-level and key subfolder for what belongs there and why.

## Status

📐 **Scaffolding stage.** Folder structure only — see `docs/architecture/` for design notes as they are added.
