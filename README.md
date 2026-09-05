<div align="center">

# PolicySentinel
### Autonomous Policy Conflict Detection, Regulatory Mapping & Compliance Intelligence Platform

Automate enterprise policy cross-referencing. Detect hidden contradictions, modality erosions, and temporal mismatches across corporate documents with AI-drafted redline resolutions, interactive Neo4j knowledge graphs, and multi-framework regulatory mapping.

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI_0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React_18.3-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/Relational_DB-PostgreSQL_16-4169E1.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Neo4j](https://img.shields.io/badge/Graph_DB-Neo4j_5-008CC1.svg?logo=neo4j&logoColor=white)](https://neo4j.com)
[![Gemini](https://img.shields.io/badge/AI_Engine-Google_Gemini-8E75B2.svg?logo=google-gemini&logoColor=white)](https://ai.google.dev)

</div>

---

## The Problem
Modern enterprise organizations face severe compliance risks and operational overhead caused by fragmented, siloed policies:
* **Silent Policy Contradictions**: Disjointed departments publish conflicting mandates (e.g., Information Security mandating 90-day log deletion, while Legal retains logs for 7 years).
* **Modality Erosion**: Crucial mandates (*"Employees MUST encrypt portable media"*) get diluted over revisions into discretionary guidance (*"Employees SHOULD encrypt portable media"*).
* **M&A and Departmental Overlaps**: Merging corporate policies during acquisitions creates duplicate, contradictory operational rules.
* **Regulatory Compliance Blindspots**: Organizations struggle to map internal obligations directly against external frameworks like GDPR, ISO 27001, SEBI, and RBI.
* **Manual Audit Fatigue**: Compliance teams spend hundreds of hours manually comparing document pages ahead of external regulatory audits.

---

## The Proposed Solution & Pipeline
PolicySentinel transforms dense document reviews into an automated, AI-driven compliance workflow:

```
[Uploaded Document (.pdf, .docx, .txt)]
       │
       ▼
[Clause Segmentation] ────────► Hierarchical section outlines & numbered clause trees
       │
       ▼
[AI Obligation Parser] ───────► Normalized JSON (Subject, Modality, Action, Object)
       │
       ▼
[Conflict & Staleness Engine] ─► Flags direct contradictions, modality shifts, temporal rot
       │
       ▼
[Regulatory Knowledge Base] ──► Auto-maps obligations to GDPR, ISO 27001, SEBI, RBI
       │
       ▼
[Actionable Redlines & Graph] ─► AI redline proposals, Neo4j graph traversal, Executive PDF report
```

---

## System Architecture & Execution Flow

```mermaid
flowchart TD
    subgraph Step1["Step 1: Ingestion & Text Extraction"]
        A["Uploaded Policy Files\n(.pdf, .docx, .txt, .md)"] --> B["PyMuPDF & python-docx\nDocument Extractor"]
        B --> Out1["Clean Raw Text, Sections & Metadata"]
    end

    subgraph Step2["Step 2: Hierarchy & AI Obligation Extraction"]
        Out1 --> C["Clause Segmentation Engine"]
        C --> Out2["Structured Clause Tree Outline\n(Numbered Clauses & Paragraphs)"]
        Out2 --> D["Google Gemini AI Obligation Extractor"]
        D --> Out3["Structured Obligation Triples\n(Subject, Modality, Action, Object)"]
    end

    subgraph Step3["Step 3: Multi-Dimensional Conflict Analysis"]
        Out3 --> E["Semantic Comparison & Formal Logic Engine"]
        E --> Out4["Flagged Conflict Matrix\n(Contradictions, Modality Shifts, Temporal Rotations)"]
        Out3 --> RegMap["AI Regulatory Mapping Engine"]
        RegMap --> RegOut["Regulatory Mappings\n(GDPR, ISO 27001, SEBI, RBI)"]
    end

    subgraph Step4["Step 4: Knowledge Graph, Actionable Redlines & Reports"]
        Out4 --> F["AI Redline Recommendation Engine"]
        Out4 --> G["PostgreSQL 16 & Neo4j 5 Knowledge Graph"]
        F --> Out5["Drafted Redline Text & Accept/Reject Audit Trail"]
        G --> Out6["Interactive Knowledge Graph & Downloadable Executive PDF Report"]
    end

    style Step1 fill:#F5F3FF,stroke:#7C3AED,color:#4C1D95
    style Step2 fill:#FFFFFF,stroke:#8B5CF6,color:#4C1D95
    style Step3 fill:#F5F3FF,stroke:#7C3AED,color:#4C1D95
    style Step4 fill:#FFFFFF,stroke:#6D28D9,color:#4C1D95
```

---

## Core Modules & Platform Features

| Module | Route / Page | Capabilities |
| :--- | :--- | :--- |
| **Executive Dashboard** | `/dashboard` | Executive Compliance Score dial (0–100), active/resolved conflict counts, pending recommendations, risk distribution matrix, and audit trail. |
| **Policy Ingestion** | `/upload` | Ingestion of PDF, DOCX, TXT documents with custom Company and Uploader names, progress tracking, and multi-tenant user provisioning. |
| **Clause Viewer** | `/clauses` | Clause hierarchy navigation, clause numbering, text preview, confidence scoring, and policy filtering. |
| **Obligation Viewer** | `/obligations` | Modality filtering (`MUST`, `SHALL`, `SHOULD`, `MAY`), structured Subject-Action-Object triples, and source clause links. |
| **Conflict Dashboard** | `/conflicts` | Side-by-side clause comparison, conflict taxonomy (Direct Contradiction, Modality Erosion, Temporal Mismatch, Scope Overlap, Threshold Discrepancy). |
| **AI Redlines & Approvals** | `/recommendations` | AI-generated redlines and suggested actions with one-click **Accept / Reject** human-in-the-loop audit logging. |
| **Obligation Relationships** | `/relationships` | Cross-policy obligation categorizations: `CONFLICT`, `REDUNDANT`, `COMPLEMENTARY`, `UNRELATED`. |
| **Advanced Findings** | `/findings` | In-depth cross-policy findings matrix with severity breakdowns. |
| **Regulatory Knowledge Base** | `/regulatory` | Real-time mapping against **GDPR**, **ISO 27001**, **SEBI Cybersecurity Framework**, and **RBI Master Direction**, plus per-policy Health Scores (A/B/C grades). |
| **Neo4j Knowledge Graph** | `/graph` | Interactive visual node-edge graph, policy impact analysis traversals, and semantic entity search. |
| **Audit Logs & PDF Reports** | `/reports` | Immutable activity trail with exportable, signed executive compliance PDF reports (`/api/v1/compliance-dashboard/download`). |
| **Multi-Company Directory** | *Topbar* | Dynamic tenant switcher separating multiple corporate entities with accurate, isolated policy counts. |

---

## Technology Stack

| Layer | Technology | Version | Purpose & Rationale |
| :--- | :--- | :--- | :--- |
| **Frontend UI** | React, TypeScript, Tailwind CSS, Vite | React 18.3, TS 5.7 | High-performance reactive UI with responsive data tables, dials, and dark/light mode. |
| **Backend REST API** | FastAPI, Python | Python 3.11+, FastAPI 0.115+ | High-throughput asynchronous backend with auto-generated OpenAPI documentation. |
| **Relational Database** | PostgreSQL, SQLAlchemy, Alembic | PostgreSQL 16 | ACID-compliant transactional storage for companies, users, policies, clauses, conflicts, and audit trails. |
| **Knowledge Graph** | Neo4j, Bolt Driver | Neo4j 5 Community | High-performance graph database storing policy hierarchies, obligation relationships, and impact analysis paths. |
| **AI & LLM Services** | Google Gemini AI | `google-genai` SDK | Clause extraction, obligation decomposition, regulatory mapping, and redline drafting with schema-enforced JSON. |
| **Document Parsers** | PyMuPDF, python-docx | Latest | Fast, robust local extraction of text, tables, and metadata from PDF and Word documents. |
| **Formal Reasoning** | Z3 Theorem Prover | `z3-solver` | Mathematical validation of deontic logic and modality contradictions. |

---

## Installation & Execution Guide

### Option A: Docker Compose (Recommended)

Runs the entire stack in orchestrated, health-checked containers:

```bash
# 1. Clone repository
git clone https://github.com/Sangamithraa077/PolicySentinel.git
cd PolicySentinel

# 2. Configure environment
cp .env.example .env
# Edit .env and supply your GEMINI_API_KEY if testing live AI generation

# 3. Build & start all 4 services
docker compose up -d --build

# 4. Run database migrations & seed demo dataset
docker exec -w /app/backend policysentinel-backend alembic upgrade head
docker exec -w /app policysentinel-backend python -m scripts.setup.seed_demo_data
```

#### Service URLs & Default Credentials

| Service | URL | Credentials / Notes |
| :--- | :--- | :--- |
| **Frontend Web Application** | [http://localhost:3000](http://localhost:3000) | Hot-reloading React dashboard |
| **Backend REST API** | [http://localhost:8000](http://localhost:8000) | Root API endpoint |
| **Interactive Swagger Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Complete interactive endpoint testing |
| **PostgreSQL Database** | `localhost:5433` (container port `5432`) | User: `policysentinel`, Password: `changeme`, DB: `policysentinel` |
| **Neo4j Graph Browser** | [http://localhost:7474](http://localhost:7474) | User: `neo4j`, Password: `changeme`, Bolt: `bolt://localhost:7687` |

---

### Option B: Native Local Execution

Run services natively on host machines:

```bash
# 1. Start Postgres & Neo4j database containers
docker compose up -d postgres neo4j

# 2. Start Backend API (Terminal 1)
cd backend
python -m venv venv
# Windows: .\venv\Scripts\activate | macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 3. Start Frontend App (Terminal 2)
cd frontend
npm install
npm run dev
```

---

## Future Implementation Roadmap

* **Interactive RAG Policy Chatbot**: Knowledge Graph-augmented natural language interface allowing auditors to ask questions (*"What is our maximum retention period for customer PII across all subsidiaries?"*) and receive citation-backed answers.
* **Agentic Multi-Party Reconciler**: Autonomous multi-agent negotiations proposing consensus policy text across cross-departmental stakeholders.
* **Continuous Cloud Webhook Ingestion**: Webhooks for SharePoint, Google Drive, and OneDrive for automated real-time compliance diffing on document updates.

<div align="center">

PolicySentinel delivers enterprise compliance assurance through automated policy cross-referencing, formal logic validation, and AI-powered redlines.

*Built with precision for robust, audit-ready compliance.*

</div>
