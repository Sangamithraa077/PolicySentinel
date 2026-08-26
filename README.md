<div align="center">

# 🛡️ PolicySentinel

### Automated Policy Conflict Detection & Compliance Intelligence Platform

**Upload corporate policies. PolicySentinel extracts obligations, detects hidden contradictions across documents, and drafts AI-powered redlines.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Neo4j](https://img.shields.io/badge/Neo4j-5-018bff?style=for-the-badge&logo=neo4j&logoColor=white)](https://neo4j.com)
[![Gemini](https://img.shields.io/badge/Gemini-AI-1A73E8?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docs.docker.com/compose/)

[Live App →](https://policysentinel-frontend.onrender.com) &nbsp;·&nbsp; [API Docs →](https://policysentinel-backend.onrender.com/docs) &nbsp;·&nbsp; [Guided Demo Mode →](https://policysentinel-frontend.onrender.com/demo)

</div>

---

## 💡 Overview

As organizations grow, corporate policies proliferate across departments. Over time, subtle contradictions emerge between documents — one policy mandates *deleting audit logs after 90 days*, while another requires *retaining logs for 7 years*. 

**PolicySentinel** automates the manual cross-referencing process:

1. **Ingest Policies**: Upload multi-format documents (`.pdf`, `.docx`, `.txt`, `.md`).
2. **AI Clause Segmentation & Extraction**: Parses documents into structured section hierarchies and extracts normalized compliance obligations (Subject, Modality, Action, Object, Time Constraints).
3. **Multi-Dimensional Conflict Detection**: Identifies semantic contradictions, modality weakenings (`Must` → `Should`), and temporal rotation mismatches across company policies.
4. **AI-Drafted Redline Resolutions**: Generates actionable policy rewrites with an interactive Accept/Reject audit trail.
5. **Knowledge Graph & Executive Reporting**: Visualizes relationships in Neo4j and exports audit-ready PDF compliance reports.

---

## ✨ Key Features

* 📄 **Multi-Format Ingestion**: Supports `.pdf` (PyMuPDF), `.docx` (python-docx), `.txt`, and `.md` file formats.
* 🧩 **Hierarchical Clause Tree**: Rule-based outline matching combined with Gemini AI structural fallback.
* 🤖 **AI Obligation Extraction**: Leverages Google Gemini AI to extract structured obligations as JSON with automatic fallback resilience.
* ⚡ **Semantic & Temporal Conflict Detection**: Catches conflicting retention windows, weakened security controls, and duplicate requirements.
* ✏️ **Interactive AI Redlining**: Proposes inline text revisions with a full audit log.
* 🕸️ **Neo4j Knowledge Graph**: Graph nodes mapping **Company → Policies → Clauses → Obligations → Regulations (GDPR, ISO 27001, DPDP Act 2023)**.
* 📊 **Executive Compliance Dashboard**: Real-time compliance risk scoring (0–100) and downloadable PDF executive reports.

---

## 🏗️ System Architecture

```mermaid
graph TD
    classDef client fill:#3178C6,stroke:#1A5F8A,color:#fff;
    classDef server fill:#009688,stroke:#00796B,color:#fff;
    classDef db fill:#4169E1,stroke:#3B5998,color:#fff;
    classDef external fill:#D16A00,stroke:#B05500,color:#fff;

    Client["React 19 + Vite Frontend"]:::client
    API["FastAPI 0.141 Backend"]:::server
    PG[("PostgreSQL 16\n(Relational & Files)")]:::db
    Neo[("Neo4j 5\n(Knowledge Graph)")]:::db
    Gemini["Google Gemini AI API"]:::external

    Client -->|REST API / CORS| API
    API -->|SQLAlchemy ORM| PG
    API -->|Bolt Protocol| Neo
    API -->|GenAI Client| Gemini
```

---

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

Run the entire application stack (Frontend, Backend, PostgreSQL, and Neo4j) with Docker Compose:

```bash
# 1. Clone the repository
git clone https://github.com/Sangamithraa077/PolicySentinel.git
cd PolicySentinel

# 2. Configure environment variables (optional: add your Gemini API key)
cp .env.example .env

# 3. Build and launch all containers
docker compose up -d --build

# 4. Apply database migrations & seed sample demo data
docker exec -w /app/backend policysentinel-backend alembic upgrade head
docker cp scripts policysentinel-backend:/app/scripts
docker exec -w /app policysentinel-backend python -m scripts.setup.seed_demo_data
```

Access your services:
* 🌐 **Frontend Web App**: [http://localhost:3000](http://localhost:3000)
* ⚙️ **Backend REST API**: [http://localhost:8000](http://localhost:8000)
* 📚 **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
* 🕸️ **Neo4j Browser**: [http://localhost:7474](http://localhost:7474)

---

### Option 2: Native Local Execution

#### 1. Start Database Containers
```bash
docker compose up -d postgres neo4j
```

#### 2. Start Backend Server
```bash
cd backend
python -m venv venv
# On Windows: .\venv\Scripts\activate | On macOS/Linux: source venv/bin/activate
pip install -r requirements.txt

# Run migrations & start server on port 8001
python -m alembic upgrade head
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
```

#### 3. Start Frontend App
```bash
cd frontend
npm install
npm run dev
```
Open **[http://localhost:3000](http://localhost:3000)** in your browser.

---

## ⚙️ Configuration (`.env`)

| Variable | Description | Default |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://policysentinel:changeme@127.0.0.1:5433/policysentinel` |
| `NEO4J_URI` | Neo4j Bolt connection URI | `bolt://localhost:7687` |
| `NEO4J_USER` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | `changeme` |
| `GEMINI_API_KEY` | Google AI Studio API key | *(Optional — activates live Gemini extraction)* |
| `GEMINI_MODEL` | Gemini AI model version | `gemini-1.5-flash` |
| `CORS_ALLOWED_ORIGINS` | Permitted frontend origins | `http://localhost:3000,http://localhost:3001` |

---

## 📡 API Reference Overview

All REST API endpoints are scoped under `/api/v1`:

| Module | Core Endpoints | Description |
| :--- | :--- | :--- |
| **Uploads** | `POST /uploads/policies` | Uploads PDF/DOCX/TXT/MD & executes automated pipeline. |
| **Policies** | `GET /policies`, `GET /policies/{id}`, `DELETE /policies/{id}` | Policy metadata, version management & file download. |
| **Clauses** | `GET /clauses`, `POST /clauses/resegment` | Clause hierarchy list, keyword search & re-segmentation. |
| **Obligations** | `GET /obligations`, `GET /obligations/{id}` | Filterable obligation list by modality and compliance category. |
| **Conflicts** | `GET /conflicts`, `PATCH /conflicts/{id}/status` | List flagged conflicts and update resolution status. |
| **Recommendations** | `GET /recommendations`, `PATCH /recommendations/{id}/status` | Review AI redline proposals and accept/reject resolutions. |
| **Dashboard** | `GET /compliance-dashboard/summary`, `/download` | Overview metrics and exportable PDF audit report. |
| **Knowledge Graph** | `GET /graph/policy/{id}`, `GET /graph/impact` | Neo4j node traversals, impact analysis & search. |

Full interactive OpenAPI documentation is available live at `/docs`.

---

## 🧪 Testing

```bash
# Run full unit and integration test suite
pytest -v

# Run unit tests only
pytest tests/backend/unit/ -v
```

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more details.

---

<div align="center">

*Designed & Built for Financial & Enterprise Compliance Teams.*

</div>
