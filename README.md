# PolicySentinel

**AI-Powered Policy Conflict, Redundancy, Staleness & Regulatory Alignment Platform for Financial Institutions**

PolicySentinel is an enterprise-grade platform designed to automatically ingest regulatory documents and corporate policies, parse them into hierarchical clauses, extract compliance obligations using Gemini AI, map them to international standard regulatory frameworks (GDPR, ISO 27001, RBI, SEBI), and visualize the resulting structural mappings and semantic conflicts using an interactive Neo4j Knowledge Graph.

---

## Architecture

The system follows the **Clean Architecture** pattern, enforcing a strict inward dependency direction:

```
    Presentation Layer    (backend/api, backend/middleware, React Frontend)
            ↓
    Application Layer     (backend/services, backend/schemas)
            ↓
    Domain Layer          (backend/domain)  ← Zero external dependencies
            ↑
    Infrastructure Layer  (backend/database, backend/models, backend/repositories,
                           backend/ai, backend/graph, backend/reasoning)
```

- **Domain Layer**: Contains fundamental domain exceptions, entities (Policy, Clause, Obligation), and interface definitions.
- **Application Layer**: Contains business services orchestrating the upload pipeline, semantic comparison, conflict detection, and dashboard metrics.
- **Infrastructure Layer**: Connects to PostgreSQL using SQLAlchemy, interacts with Neo4j using the Bolt driver client, and calls Google GenAI (Gemini) with retry handlers.
- **Presentation Layer**: Exposes FastAPI endpoints (with Pydantic schemas) and serves a modern responsive React web dashboard.

---

## Key Features

1. **Upload Pipeline & Text Extraction**: Accepts PDF, DOCX, TXT, and MD files, hashes files to prevent duplicate uploads, and automatically extracts layout-aware text.
2. **Clause Segmentation**: Splits policy documents into ordered sections and subheadings using hierarchical outline scanners.
3. **Obligation Extraction**: Employs Gemini to extract compliance subjects, actions, objects, modalities (Must, Shall, Should, May), and categories.
4. **Semantic Comparison & Conflict Detection**: Identifies cross-document conflicts:
   - **Temporal Conflicts**: Flags contradictory timing requirements (e.g., daily logs vs. 7-year archives).
   - **Strength Conflicts**: Identifies modality weaknesses (e.g., MUST retain logs vs. MAY purge logs).
   - **Staleness Detection**: Automatically marks outdated policies based on effective dates, review cycles, and supersession states.
5. **AI Regulatory Mapping**: Maps obligations directly to GDPR, ISO 27001, SEBI, and RBI frameworks.
6. **Policy Health Scoring**: Configurable engine computing score (0–100) and grade (A–F) based on severity penalties, missing mappings, and approved recommendations.
7. **Neo4j Knowledge Graph**: Synchronizes SQL data to graph nodes (`Policy`, `Clause`, `Obligation`, `Regulation`, `Finding`, `Recommendation`) and traverses relationships (`MAPS_TO`, `CONFLICTS_WITH`, etc.).
8. **Interactive SVG visualization**: React visualizer featuring node dragging, scroll zooming, drag panning, node property details drawer, and traversal impact analysis stats.
9. **Guided Demo Mode**: Walkthrough step dashboard designed for presentations and offline testing.

---

## Technology Stack

- **Frontend**: React (Vite, TypeScript, TailwindCSS v4, Lucide Icons, TanStack Query)
- **Backend**: FastAPI (Python 3.12, Uvicorn, Pydantic v2, Alembic migrations)
- **Database**: PostgreSQL (SQLAlchemy ORM)
- **Knowledge Graph**: Neo4j (Bolt driver connectivity, Cypher queries)
- **AI Integration**: Google GenAI SDK (Gemini-2.0-flash / Gemini-1.5-flash)

---

## Repository Layout

```
PolicySentinel/
├── backend/
│   ├── api/             # FastAPI controller endpoints & dependency injections
│   ├── config/          # Environment configuration settings (settings.py)
│   ├── core/            # Lifespan handlers, security, and unhandled exception middleware
│   ├── database/        # Session generators, migrations setup, and seed scripts
│   ├── domain/          # Entities and domain constraints (zero-dependency core)
│   ├── graph/           # Neo4j client driver and Graph population services
│   ├── models/          # SQLAlchemy relational model definitions
│   ├── schemas/         # Pydantic schema validation structures
│   ├── services/        # Business workflow logic (extraction, comparison, scoring)
│   └── utils/           # Helper scripts (logging configurations, retry decorators)
├── frontend/
│   ├── public/          # Static app assets
│   ├── src/
│   │   ├── components/  # Layout sidebars, topbars, dropzones, and common UI elements
│   │   ├── hooks/       # React Query queries & theme state hooks
│   │   ├── pages/       # Dashboard, Knowledge Graph, Advanced Findings, and Demo Mode
│   │   ├── styles/      # Global Tailwind configuration imports
│   │   └── App.tsx      # Routing router registration
└── tests/               # Pytest unit, integration, and E2E suites
```

---

## Environment Variables

Create a `.env` file in the root folder with the following configuration:

```env
# Backend Server Configuration
ENV=production
DEBUG=false
SECRET_KEY=super-secret-production-token-change-me

# PostgreSQL Connection Settings
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secure-password
POSTGRES_DB=policysentinel
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATABASE_URL=postgresql://postgres:secure-password@localhost:5432/policysentinel

# Neo4j Connection Settings
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=secure-neo4j-password

# Gemini AI API Configuration
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-1.5-flash
```

---

## Running the Project Locally

1. **Start the database servers**:
   ```bash
   # Run the development db setup scripts
   python scripts/setup/run_dev_db.py
   ```
2. **Apply migrations & seed data**:
   ```bash
   # Relational migration
   cd backend
   venv/Scripts/alembic upgrade head
   
   # Seed enterprise demo dataset
   python scripts/setup/seed_demo_data.py
   ```
3. **Run the FastAPI backend server**:
   ```bash
   venv/Scripts/uvicorn backend.main:app --reload --port 8000
   ```
4. **Run the React frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

## Production Deployment Guide

### 1. Database & Neo4j Hosting
- **PostgreSQL**: Deploy using AWS RDS, GCP Cloud SQL, or a managed PostgreSQL instance with Connection Pooling enabled (e.g. PgBouncer) to sustain parallel query spikes. Ensure `max_connections` is configured to accommodate the pool size.
- **Neo4j**: Deploy via Neo4j AuraDB or a self-hosted instance. In production, configure authentication, enable Bolt encryption, and disable guest access.

### 2. Backend API (FastAPI) Configuration
- Set `ENV=production` and `DEBUG=false` to disable detailed error stack traces in API response payloads.
- Run FastAPI using Gunicorn with Uvicorn workers:
  ```bash
  gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
  ```
- **Logging**: Log events are routed to JSON formatted outputs, suitable for Datadog, AWS CloudWatch, or Google Cloud Logging.

### 3. Frontend Production Build
- Compile the static bundle:
  ```bash
  cd frontend
  npm run build
  ```
- Serves the generated `dist/` static files through Nginx or a CDN (Cloudflare / AWS CloudFront) for global latency reduction and cache control.

---

## API Documentation

Once the backend is running, standard Swagger API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Future Enhancements

- **Formal Logic Verification**: Incorporating the Z3 Solver to evaluate provable modality contradictions.
- **Agentic Multi-Step RAG**: Adding semantic Vector Search to improve retrieval context for mappings.
- **Department/Role Hierarchy Enforcement**: Scoping findings to matching compliance department heads.
