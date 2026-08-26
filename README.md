<div align="center">

# PolicySentinel

### Policy Conflict Detection & Compliance Intelligence Platform

Automate policy cross-referencing. Detect hidden contradictions, modality shifts, and temporal mismatches across corporate documents with AI-drafted redline resolutions.

[![Python](https://img.shields.io/badge/Python-3.11+-8B5CF6?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141-7C3AED?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-6D28D9?style=flat-square&logo=react&logoColor=white)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-8B5CF6?style=flat-square&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-7C3AED?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Neo4j](https://img.shields.io/badge/Neo4j-5-6D28D9?style=flat-square&logo=neo4j&logoColor=white)](https://neo4j.com)
[![Gemini AI](https://img.shields.io/badge/Gemini-AI-8B5CF6?style=flat-square&logo=google&logoColor=white)](https://ai.google.dev/)
[![Docker](https://img.shields.io/badge/Docker-Compose-7C3AED?style=flat-square&logo=docker&logoColor=white)](https://docs.docker.com/compose/)

[Live Application](https://policysentinel-frontend.onrender.com) &nbsp;&bull;&nbsp; [API Documentation](https://policysentinel-backend.onrender.com/docs) &nbsp;&bull;&nbsp; [Interactive Demo Mode](https://policysentinel-frontend.onrender.com/demo)

</div>

---

## Executive Overview

As organizations scale, policy documents accumulate across departments, creating undetected compliance liabilities:

- **Silent Policy Contradictions**: Information Security mandates deleting access logs after 90 days, while Data Retention requires retaining logs for 7 years.
- **Manual Audit Bottlenecks**: Compliance teams spend weeks manually cross-referencing hundreds of pages before regulatory audits.
- **Modality Erosion**: Critical mandates (*Must encrypt mobile devices*) get quietly diluted to recommendations (*Should encrypt mobile devices*) in newer policy revisions.
- **M&A Policy Friction**: Merging corporate policies during acquisitions creates overlapping, conflicting operational directives.

---

## Solution Architecture

PolicySentinel replaces manual policy reviews with an automated compliance intelligence pipeline:

1. **Native Multi-Format Parsing**: Ingests `.pdf`, `.docx`, `.txt`, and `.md` files without pre-processing.
2. **AI-Driven Obligation Structuring**: Extracts normalized compliance directives (Subject, Modality, Action, Object, Time Constraints) using Google Gemini AI.
3. **Multi-Dimensional Conflict Analysis**: Compares obligations across all policies to detect semantic contradictions, modality shifts, and temporal mismatches.
4. **Actionable AI Redlines**: Generates inline text revisions with an interactive Accept/Reject audit workflow.
5. **Graph & Executive Intelligence**: Syncs policy relationships to Neo4j and exports audit-ready PDF compliance reports.

---

## System Architecture & Execution Flow

```mermaid
flowchart TD
    subgraph Step1["1. Document Ingestion"]
        A["Uploaded Policy Files\n(.pdf, .docx, .txt, .md)"] --> B["PyMuPDF & python-docx\nText Extractor"]
    end

    subgraph Step2["2. Structure & Extraction"]
        B --> C["Clause Segmentation Engine\n(Hierarchical Outline Tree)"]
        C --> D["Google Gemini AI\nObligation Extractor"]
    end

    subgraph Step3["3. Conflict Analysis Engine"]
        D --> E["Semantic Vector Search\n(Cosine Similarity)"]
        E --> F["Modality Shift & Temporal\nConflict Engine"]
    end

    subgraph Step4["4. Resolution & Intelligence"]
        F --> G["AI Redline Recommendation Service"]
        F --> H["PostgreSQL 16\nRelational Storage"]
        F --> I["Neo4j 5\nKnowledge Graph"]
        F --> J["Executive PDF Audit Report"]
    end

    style Step1 fill:#F5F3FF,stroke:#7C3AED,color:#4C1D95
    style Step2 fill:#FFFFFF,stroke:#8B5CF6,color:#4C1D95
    style Step3 fill:#F5F3FF,stroke:#7C3AED,color:#4C1D95
    style Step4 fill:#FFFFFF,stroke:#6D28D9,color:#4C1D95
```

---

## Core Platform Capabilities

| Capability | Technical Mechanism | Business Value |
| :--- | :--- | :--- |
| **Multi-Format Ingestion** | PyMuPDF, python-docx & raw text parsers | Zero document prep required; ingest existing enterprise PDFs and Word files natively. |
| **Clause Segmentation** | Heuristic outline matching + Gemini AI fallback | Preserves document hierarchy (Chapters, Sections, Sub-clauses) for targeted auditing. |
| **Obligation Extraction** | Gemini AI JSON Schema enforcement | Converts unstructured prose into structured rules: *Who*, *Must/Should*, *What*, *When*. |
| **Conflict Detection** | Semantic similarity & rule-based engine | Identifies duplicates, direct contradictions, modality shifts, and temporal mismatches. |
| **AI Redlining** | Gemini AI text synthesis | Provides instant, copy-pasteable revised text to resolve policy conflicts cleanly. |
| **Knowledge Graph** | Neo4j 5 Cypher queries | Visualizes policy dependencies and performs instant impact analysis across policies. |
| **Audit Reporting** | ReportLab PDF generator | Generates executive risk scores (0–100) and downloadable compliance audit trails. |

---

## Supported Formats & Extraction Specifications

| Extension | Parser Engine | Extraction Capabilities |
| :--- | :--- | :--- |
| `.pdf` | PyMuPDF (`fitz`) | Multi-page text extraction, heading detection, layout preservation. |
| `.docx` | `python-docx` | Structured paragraph parsing, table cell text extraction, heading levels. |
| `.txt` | UTF-8 Plain Text | Fast line-by-line parsing, section header discovery. |
| `.md` | Markdown Parser | AST header hierarchy extraction (`#`, `##`, `###`), list item parsing. |

---

## Quick Start Guide

### Option A: Docker Compose (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/Sangamithraa077/PolicySentinel.git
cd PolicySentinel

# 2. Configure environment
cp .env.example .env

# 3. Build & start containers
docker compose up -d --build

# 4. Migrate database & seed demo data
docker exec -w /app/backend policysentinel-backend alembic upgrade head
docker cp scripts policysentinel-backend:/app/scripts
docker exec -w /app policysentinel-backend python -m scripts.setup.seed_demo_data
```

| Service | Local URL |
| :--- | :--- |
| **Frontend Web App** | [http://localhost:3000](http://localhost:3000) |
| **Backend REST API** | [http://localhost:8000](http://localhost:8000) |
| **Swagger API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) |
| **Neo4j Browser** | [http://localhost:7474](http://localhost:7474) |

---

### Option B: Native Local Execution

```bash
# 1. Start Postgres & Neo4j containers
docker compose up -d postgres neo4j

# 2. Start Backend API (Terminal 1)
cd backend
python -m venv venv
# Windows: .\venv\Scripts\activate | macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python -m alembic upgrade head
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload

# 3. Start Frontend App (Terminal 2)
cd frontend
npm install
npm run dev
```

---

## API Reference Overview

All REST API endpoints are scoped under `/api/v1`:

| Module | Route | Method | Description |
| :--- | :--- | :--- | :--- |
| **Uploads** | `/uploads/policies` | `POST` | Ingests `.pdf`/`.docx`/`.txt`/`.md` & triggers automated AI pipeline. |
| **Policies** | `/policies` | `GET` / `DELETE` | List, inspect metadata, or remove company policies. |
| **Clauses** | `/clauses` | `GET` / `POST` | List clauses, search keywords, or trigger AI re-segmentation. |
| **Obligations** | `/obligations` | `GET` | Filter obligations by modality (`Must`, `Should`) and category. |
| **Conflicts** | `/conflicts` | `GET` / `PATCH` | List detected policy contradictions and update review status. |
| **Recommendations** | `/recommendations` | `GET` / `PATCH` | Review AI-drafted redline resolutions and accept/reject edits. |
| **Dashboard** | `/compliance-dashboard/summary` | `GET` | Fetch compliance risk score and download executive PDF report. |
| **Knowledge Graph** | `/graph/policy/{id}` | `GET` | Query Neo4j node relationships and perform audit impact analysis. |

---

## Environment Configuration

| Variable | Purpose | Default Value |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://policysentinel:changeme@127.0.0.1:5433/policysentinel` |
| `NEO4J_URI` | Neo4j Bolt connection URI | `bolt://localhost:7687` |
| `NEO4J_USER` | Neo4j database user | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j database password | `changeme` |
| `GEMINI_API_KEY` | Google AI Studio API key | *(Optional — activates live Gemini extraction)* |
| `GEMINI_MODEL` | Gemini AI model version | `gemini-1.5-flash` |
| `CORS_ALLOWED_ORIGINS` | Permitted frontend origins | `http://localhost:3000,http://localhost:3001` |

---

## License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

---

<div align="center">

*Engineered for Enterprise Compliance & Risk Management Teams.*

</div>
