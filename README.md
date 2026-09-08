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

## System Architecture & Execution Flow

PolicySentinel runs an automated, fault-tolerant compliance intelligence pipeline powered by **FastAPI**, **React**, **Google Gemini**, **Z3 Theorem Prover**, and **Neo4j**:

```mermaid
flowchart LR
    A["📄 Policy Upload\n(PDF, Word, TXT)"] --> B["✂️ Clause Parser\n(Hierarchy Tree)"]
    B --> C["🤖 AI Extraction\n(Gemini 2.5 Flash)"]
    
    subgraph Resilience["🛡️ AI Circuit Breaker"]
        C -.->|Quota 429 / Offline| CB["⚡ Local Fallback Engine\n(Regex & Heuristics)"]
    end
    
    C --> D["⚖️ Dual Conflict Engine\n(Semantic AI + Z3 SMT Solver)"]
    CB --> D
    
    D --> E[("🌐 Neo4j Graph &\nPostgreSQL")]
    D --> F["📜 Regulatory Cross-Walk\n(GDPR • ISO 27001 • SEBI • RBI)"]
    
    E --> G["📊 Executive Dashboard\n& AI Redlines"]
    F --> G

    style A fill:#F1F5F9,stroke:#64748B,color:#0F172A
    style B fill:#F5F3FF,stroke:#8B5CF6,color:#4C1D95
    style C fill:#EDE9FE,stroke:#7C3AED,color:#2E1065
    style Resilience fill:#FFFBEB,stroke:#F59E0B,color:#92400E
    style CB fill:#FEF3C7,stroke:#D97706,color:#92400E
    style D fill:#E0E7FF,stroke:#4F46E5,color:#1E1B4B
    style E fill:#ECFDF5,stroke:#10B981,color:#064E3B
    style F fill:#DBEAFE,stroke:#2563EB,color:#172554
    style G fill:#F0FDF4,stroke:#16A34A,color:#14532D
```

| Stage | Process & Capability | Key Technologies & Resilience |
| :--- | :--- | :--- |
| **1. Ingest & Parse** | Ingests corporate documents, strips formatting, and builds hierarchical numbered clause trees. | PyMuPDF, python-docx |
| **2. Obligation Extraction** | Decomposes legalese into normalized quadruples: `[Subject, Modality, Action, Object]`. | **Google Gemini 2.5 Flash** with **AI Circuit Breaker** (instantly fails over to local regex/heuristics on 429 quota limits — zero downtime). |
| **3. Conflict Detection** | Detects direct contradictions, modality erosion (`MUST` → `SHOULD`), and retention mismatches. | **Dual Engine**: Semantic AI + **Z3 SMT Theorem Prover** for formal mathematical proofs. |
| **4. Regulatory Mapping** | Maps obligations directly against statutory controls and calculates policy health grades (A/B/C). | **GDPR**, **ISO 27001**, **SEBI CSCRF**, **RBI Master Direction** |
| **5. Graph & Resolution** | Interactively traverses policy impact subgraphs, drafts AI redlines (Accept/Reject), and exports signed audit PDFs. | **Neo4j 5**, PostgreSQL 16, Interactive React Graph, PDF Engine |


---

## Core Modules & Platform Features

| Module | Route / Page | Capabilities |
| :--- | :--- | :--- |
| **Executive Dashboard** | `/` or `/executive-dashboard` | Executive Compliance Score dial (0–100), active/resolved conflict counts, pending recommendations, risk distribution matrix, and audit trail. |
| **Policy Library** | `/policies` | Centralized corporate policy repository with real-time text search, department categorization, version tracking, and direct clause drilling. |
| **Policy Ingestion** | `/upload` | Ingestion of PDF, DOCX, TXT documents with custom Company and Uploader names, live progress tracking, and multi-tenant user provisioning. |
| **Clause Viewer** | `/clauses` | Clause hierarchy navigation, clause numbering, text preview, confidence scoring, and policy filtering. |
| **Obligation Viewer** | `/obligations` | Modality filtering (`MUST`, `SHALL`, `SHOULD`, `MAY`), structured Subject-Action-Object triples, and source clause links. |
| **Conflict Dashboard** | `/conflicts` | Side-by-side clause comparison, conflict taxonomy (Direct Contradiction, Modality Erosion, Temporal Mismatch, Scope Overlap, Threshold Discrepancy). |
| **AI Redlines & Approvals** | `/recommendations` | AI-generated redlines and suggested actions with one-click **Accept / Reject** human-in-the-loop audit logging. |
| **Obligation Relationships** | `/relationships` | Cross-policy obligation categorizations: `CONFLICT`, `REDUNDANT`, `COMPLEMENTARY`, `UNRELATED`. |
| **Advanced Findings** | `/findings` | In-depth cross-policy findings matrix with severity breakdowns. |
| **Regulatory Knowledge Base** | `/regulatory-dashboard` | Real-time mapping against **GDPR**, **ISO 27001**, **SEBI Cybersecurity Framework**, and **RBI Master Direction**, plus per-policy Health Scores (A/B/C grades). |
| **Neo4j Knowledge Graph** | `/knowledge-graph` | Interactive visual node-edge graph, policy impact analysis traversals, and semantic entity search. |
| **Guided Demo Mode** | `/demo-mode` | Interactive step-by-step walkthrough simulating policy upload, conflict detection, knowledge graph traversal, and redline resolution. |
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
cd ..
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

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

*Built with precision for robust, audit-ready compliance.❤️*

</div>
