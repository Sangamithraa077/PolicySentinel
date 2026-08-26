<div align="center">

# PolicySentinel

### Policy Conflict Detection & Compliance Intelligence Platform

<p align="center">
  <b>Automate policy cross-referencing. Detect hidden contradictions, modality shifts, and temporal mismatches across corporate documents with AI-drafted redline resolutions.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-8B5CF6?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.141-7C3AED?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/React-19-6D28D9?style=for-the-badge&logo=react&logoColor=white" />
  <img src="https://img.shields.io/badge/TypeScript-5.7-8B5CF6?style=for-the-badge&logo=typescript&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-16-7C3AED?style=for-the-badge&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/Neo4j-5-6D28D9?style=for-the-badge&logo=neo4j&logoColor=white" />
  <img src="https://img.shields.io/badge/Gemini_AI-Google-8B5CF6?style=for-the-badge&logo=google&logoColor=white" />
  <img src="https://img.shields.io/badge/Docker-Compose-7C3AED?style=for-the-badge&logo=docker&logoColor=white" />
</p>

<p align="center">
  <a href="https://policysentinel-frontend.onrender.com"><b>Live Application</b></a> &bull; 
  <a href="https://policysentinel-backend.onrender.com/docs"><b>API Documentation</b></a> &bull; 
  <a href="https://policysentinel-frontend.onrender.com/demo"><b>Interactive Demo Mode</b></a>
</p>

</div>

---

## Executive Overview

As organizations grow, corporate policies accumulate across different departments, creating hidden compliance risks and operational friction:

* **Silent Policy Contradictions**: Information Security mandates deleting access logs after 90 days, while Data Retention requires retaining logs for 7 years.
* **Manual Audit Bottlenecks**: Compliance teams spend weeks manually cross-referencing hundreds of document pages before regulatory audits.
* **Modality Erosion**: Critical mandates (*Must encrypt mobile devices*) get quietly diluted to discretionary suggestions (*Should encrypt mobile devices*) in newer policy versions.
* **M&A Policy Friction**: Merging corporate policies during corporate acquisitions creates overlapping, conflicting operational rules.

---

## Solution Architecture

PolicySentinel replaces manual document reviews with an automated end-to-end compliance intelligence workflow:

1. **Native Multi-Format Parsing**: Automatically extracts text from `.pdf`, `.docx`, `.txt`, and `.md` files without manual document preparation.
2. **AI-Driven Obligation Structuring**: Converts unstructured prose into structured directives (Subject, Modality, Action, Object, Time Constraints) using Google Gemini AI.
3. **Multi-Dimensional Conflict Analysis**: Compares obligations across all policies to detect semantic contradictions, modality weakenings, and temporal mismatches.
4. **Actionable AI Redlines**: Drafts inline policy text revisions with an interactive Accept/Reject audit workflow.
5. **Graph & Executive Intelligence**: Connects policy relationships in Neo4j and exports audit-ready PDF compliance reports.

---

## System Execution Flow & Pipeline Outputs

The diagram below shows how PolicySentinel processes uploaded documents step-by-step and highlights the **exact outputs** generated at each stage:

```mermaid
flowchart TD
    subgraph Step1["Step 1: Document Upload & Parsing"]
        A["Uploaded Policy Files\n(.pdf, .docx, .txt, .md)"] --> B["PyMuPDF & python-docx\nText Extractor"]
        B --> Out1["Output 1: Clean Raw Document Text & Metadata"]
    end

    subgraph Step2["Step 2: Structure & AI Obligation Extraction"]
        Out1 --> C["Clause Segmentation Engine"]
        C --> Out2["Output 2: Structured Clause Tree Hierarchy\n(Section & Sub-clause Outline)"]
        Out2 --> D["Google Gemini AI Obligation Extractor"]
        D --> Out3["Output 3: Normalized Obligation JSON\n(Subject, Action, Modality, Time Constraint)"]
    end

    subgraph Step3["Step 3: Multi-Dimensional Conflict Analysis"]
        Out3 --> E["Semantic Vector Similarity & Rules Engine"]
        E --> Out4["Output 4: Flagged Conflicts Matrix\n(Contradictions, Modality Shifts, Temporal Rotations)"]
    end

    subgraph Step4["Step 4: AI Resolution, Knowledge Graph & PDF Reports"]
        Out4 --> F["AI Redline Recommendation Engine"]
        Out4 --> G["PostgreSQL 16 & Neo4j 5 Knowledge Graph"]
        F --> Out5["Output 5: AI-Drafted Text Redlines & Accept/Reject Audit Trail"]
        G --> Out6["Output 6: Visual Knowledge Graph & Downloadable Executive PDF Report"]
    end

    style Step1 fill:#F5F3FF,stroke:#7C3AED,color:#4C1D95
    style Step2 fill:#FFFFFF,stroke:#8B5CF6,color:#4C1D95
    style Step3 fill:#F5F3FF,stroke:#7C3AED,color:#4C1D95
    style Step4 fill:#FFFFFF,stroke:#6D28D9,color:#4C1D95
```

---

## Pipeline Stage Outputs Summary

<table width="100%">
<tr>
<th align="left">Pipeline Stage</th>
<th align="left">Generated Output</th>
<th align="left">What You See in the App</th>
</tr>
<tr>
<td><b>1. Document Parsing</b></td>
<td>Clean Raw Text & Metadata</td>
<td>File upload status, document metadata, byte storage.</td>
</tr>
<tr>
<td><b>2. Clause Segmentation</b></td>
<td>Hierarchical Section Tree</td>
<td>Structured Clause Tree outline view under <code>/clauses</code>.</td>
</tr>
<tr>
<td><b>3. AI Extraction</b></td>
<td>Normalized Obligation JSON</td>
<td>Structured obligations with confidence scores under <code>/obligations</code>.</td>
</tr>
<tr>
<td><b>4. Conflict Detection</b></td>
<td>Flagged Conflicts Matrix</td>
<td>High / Medium / Low conflict cards under <code>/conflicts</code>.</td>
</tr>
<tr>
<td><b>5. AI Redlining</b></td>
<td>AI-Drafted Text Revisions</td>
<td>Interactive Accept / Reject redline cards under <code>/recommendations</code>.</td>
</tr>
<tr>
<td><b>6. Graph & Reporting</b></td>
<td>Neo4j Nodes & PDF Report</td>
<td>Interactive node graph under <code>/knowledge-graph</code> & PDF report download.</td>
</tr>
</table>

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

<p align="center">
  <b>Engineered for Enterprise Compliance & Risk Management Teams.</b><br>
  <i>So policy contradictions get caught before the auditor does.</i> ❤️
</p>

</div>
