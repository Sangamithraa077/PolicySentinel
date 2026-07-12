# 🛡️ PolicySentinel

### *AI-Powered Enterprise Policy Intelligence & Governance Platform*

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Neo4j](https://img.shields.io/badge/Neo4j-5-018bff?style=for-the-badge&logo=neo4j&logoColor=white)](https://neo4j.com)
[![Gemini](https://img.shields.io/badge/Gemini_AI-1.5-1A73E8?style=for-the-badge&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

---

## 🌐 GitHub Repository

**Repository:**  
[https://github.com/Sangamithraa077/PolicySentinel.git](https://github.com/Sangamithraa077/PolicySentinel.git)

This repository contains the complete implementation of **PolicySentinel**, including the frontend, backend, AI pipeline, database integration, knowledge graph, and project documentation.

---

## 📖 Overview

PolicySentinel is an **AI-powered policy intelligence and compliance governance platform**. 

As organizations scale, internal corporate policies grow, overlap, and frequently drift into direct contradiction with one another. Compliance teams struggle to track overlaps, outdated mandates, and mismatches against external legal standards (GDPR, ISO 27001, RBI, SEBI). 

**PolicySentinel is NOT a document management system.** It is an automated governance platform that parses natural language policy documents into structured semantic elements, matches them vectorially, flags regulatory compliance risks, and suggests automated AI corrective actions.

### The Business Impact

| Area | Challenge | PolicySentinel Impact |
| :--- | :--- | :--- |
| **Audit Prep Time** | Weeks of manual comparison across hundreds of folders. | Reduced to **minutes** via automated cross-policy alignment mapping. |
| **Friction & Risk** | Conflicting guidelines (e.g., "delete logs in 24 hours" vs. "retain logs for 7 years") trigger compliance fines. | Automated anomaly and temporal constraint detection flags inconsistencies before execution. |
| **M&A Integrations** | Aligning acquired corporate compliance frameworks takes months of legal counsel. | Instantly charts overlap mappings, redundant policies, and structural gaps. |

---

## 🎨 Interactive Dashboards (UI Preview)

<details>
<summary><b>📷 Click to expand Markdown UI Placeholders</b></summary>
<br>

#### 📊 1. Executive Dashboard (`/`)
```
+-----------------------------------------------------------------------------+
| [🛡️ PolicySentinel] Acme Global Corporation            [Active Tenant: Admin] |
|                                                                             |
|  +--------------------+  +--------------------+  +-----------------------+  |
|  | Policy Health Score|  | Active Violations  |  | Regulatory Alignment  |  |
|  |       [ 84 / 100 ] |  |       [ 12 ]       |  |       [ 91% ]         |  |
|  |       Grade: B+    |  |  (3 High Severity) |  |   (GDPR, ISO 27001)   |  |
|  +--------------------+  +--------------------+  +-----------------------+  |
|                                                                             |
|  [ Live Audit Trail Log ]                                                   |
|  - 22:45 UTC: Text extraction completed successfully for IT_Security_v1.pdf |
|  - 22:46 UTC: High Severity Conflict detected: "Managed Device Access only" |
+-----------------------------------------------------------------------------+
```

#### 📂 2. Document Registry (`/policies`)
```
+-----------------------------------------------------------------------------+
| [ Policies Registry ]                                      [+ Upload Policy] |
|                                                                             |
|  Document Title                Version    Uploaded Date    Actions          |
|  -------------------------------------------------------------------------  |
|  IT Security Policy v1         v1.0       July 12, 2026    [👁️] [🛡️] [⚠️] [📥] |
|  Remote Work Guidelines        v2.3       July 12, 2026    [👁️] [🛡️] [⚠️] [📥] |
+-----------------------------------------------------------------------------+
```

#### ⚠️ 3. Anomaly & Conflict Detection (`/conflicts`)
```
+-----------------------------------------------------------------------------+
| [ Conflicts & Contradictions ]                                               |
|                                                                             |
|  [!! HIGH SEVERITY] Modality Mismatch detected in Device Security:          |
|  - Source: IT Security Policy v1 (Clause 1.2): "Must use managed laptops."  |
|  - Target: Remote Work Guidelines (Clause 1.1): "Personal devices allowed."  |
|                                                                             |
|  [⚖️ AI Recommendation] Standardize remote connection policies by enforcing  |
|  BYOD MDM profiles or provisioning secure enterprise workspaces. [Accept / Reject] |
+-----------------------------------------------------------------------------+
```

#### 🌐 4. Interactive Knowledge Graph (`/knowledge-graph`)
```
+-----------------------------------------------------------------------------+
| [ Interactive Knowledge Graph ]                                  [Reset Zoom] |
|                                                                             |
|              (Policy 1) ----[:HAS_CLAUSE]----> (Clause 1.1)                 |
|                                                     |                       |
|                                             [:HAS_OBLIGATION]               |
|                                                     v                       |
|   (ISO 27001) <--[:MAPS_TO]-- (Obligation A) --[:CONFLICTS_WITH]-- (Ob B)   |
+-----------------------------------------------------------------------------+
```
</details>

---

## ⚡ Key Features

* **🛡️ Structural Outline Parsing**: Auto-segments policy text files into nested hierarchical Clause Trees using outline-aware regex parsing.
* **🧠 AI Obligation Extraction**: Uses Google Gemini to extract compliance obligations (Subject, Modality, Action, Object, and Category) into structured JSON.
* **🎭 Semantic Modality Analyzer**: Classifies modal strengths (Must, Shall vs. Should, May) to spot subtle policy alignment gaps.
* **⏱️ Temporal Constraint Detection**: Flags conflicting retention cycles, reporting deadlines, and operational frequencies (e.g., 90-day vs. 180-day rotations).
* **⚖️ AI Redlining & Recommendations**: Proposes merge strategies and redline edits for compliance officers to Accept/Reject with automated audit trails.
* **🌐 Hybrid Knowledge Graph**: Synchronizes PostgreSQL data to a Neo4j graph database to map structural links, overlaps, and external framework matches.

---

## 🏗️ System Architecture

```mermaid
graph TD
    classDef client fill:#3178C6,stroke:#1A5F8A,color:#fff;
    classDef server fill:#009688,stroke:#00796B,color:#fff;
    classDef db fill:#4169E1,stroke:#3B5998,color:#fff;
    classDef external fill:#D16A00,stroke:#B05500,color:#fff;

    subgraph Client_Tier["Client Tier (React & TypeScript)"]
        UI["React SPA (Vite)"]:::client
        Query["React Query (Client Caching)"]:::client
        Graph["SVG Graph Visualizer (D3-like)"]:::client
    end

    subgraph Backend_Services["Backend Services (FastAPI)"]
        API["FastAPI Routing Engine"]:::server
        Extract["PDF Text Parser (PyMuPDF)"]:::server
        Segment["Clause Segmenter (Regex Scanner)"]:::server
        Compare["Semantic Comparison (Vector Embeddings)"]:::server
        Conflict["Conflict Detection Engine"]:::server
    end

    subgraph Persistent_Storage["Persistent Storage"]
        PG["PostgreSQL (Relational Metadata & Audit Logs)"]:::db
        Neo4j["Neo4j Graph Database (Entity Mapping Linkages)"]:::db
        Disk["Local Storage (Source Policy PDFs)"]:::db
    end

    subgraph External_Services["AI Services"]
        Gemini["Google Gemini API (Vertex AI SDK)"]:::external
    end

    UI -->|JSON API Requests| API
    API -->|1. Parse file| Extract
    API -->|2. Build Outline| Segment
    API -->|3. Get Embeddings| Compare
    Compare -->|text-embedding-004| Gemini
    API -->|4. Structure Obligations| Gemini
    API -->|5. Match Relations| Conflict
    
    API -->|Read/Write Metadata| PG
    API -->|Sync Nodes/Relationships| Neo4j
    API -->|Store Raw Files| Disk
    
    Query --> UI
    Graph --> UI
```

---

## ⚙️ AI Processing Ingestion Pipeline

```mermaid
flowchart TD
    classDef proc fill:#8e44ad,stroke:#7d3c98,color:#fff;
    classDef data fill:#27ae60,stroke:#1e8449,color:#fff;

    A([User Uploads PDF]) --> B[Text Extraction & Page Cleaning]:::proc
    B --> C[Hierarchical Clause Tree Segmentation]:::proc
    C --> D[Pydantic Schema Extraction via Gemini]:::proc
    
    D --> E[(Store in PostgreSQL)]:::data
    E --> F[Generate Vector Embeddings via Gemini]:::proc
    F --> G[Calculate Cosine Similarity Matches]:::proc
    
    G --> H{Conflict Engine}:::proc
    H -->|Modality Variance| I[Modality Shift Conflict]:::proc
    H -->|Frequency Incompatibility| J[Temporal Range Conflict]:::proc
    H -->|Missing Links| K[Regulatory Gap Flag]:::proc
    
    I & J & K --> L[Generate Resolution Recommendations]:::proc
    L --> M[(Sync to Neo4j Knowledge Graph)]:::data
    M --> N([Update Executive Dashboard & Audit Trail])
```

---

## 🌐 Graph Database Schema Representation

```mermaid
graph TD
    classDef node fill:#1abc9c,stroke:#16a085,color:#fff;
    classDef rel stroke:#2c3e50,stroke-width:2px;

    Policy["Policy Node"]:::node
    Clause["Clause Node"]:::node
    Obligation["Obligation Node"]:::node
    Regulation["Regulation Node"]:::node
    Finding["Finding Node"]:::node
    Recommendation["Recommendation Node"]:::node

    Policy -- "[:HAS_CLAUSE]" --> Clause
    Clause -- "[:HAS_OBLIGATION]" --> Obligation
    Obligation -- "[:MAPS_TO]" --> Regulation
    Obligation -- "[:CONFLICTS_WITH (Temporal / Modality)]" --> Obligation
    Obligation -- "[:REDUNDANT_WITH]" --> Obligation
    Obligation -- "[:COMPLEMENTS]" --> Obligation
    Obligation -- "[:HAS_FINDING]" --> Finding
    Finding -- "[:HAS_RECOMMENDATION]" --> Recommendation
```

---

## 🛠️ Technology Stack

| Layer | Technology | Usage |
| :--- | :--- | :--- |
| **Frontend** | React, TypeScript, Tailwind CSS, TanStack Query, React Router | Dashboard interfaces, Graph visualization render, upload panels. |
| **Backend** | FastAPI, Python 3.12, Uvicorn, SQLAlchemy | REST API server orchestration, asynchronous ingestion worker tasks. |
| **Relational DB**| PostgreSQL 16 | Policy metadata, user credentials, clauses, audit trails. |
| **Graph DB** | Neo4j 5 | Graph nodes, maps-to, complement, and conflicts-with relationships. |
| **AI LLM** | Google Gemini Pro (`gemini-1.5-flash`) | Structured legal extraction, resolution recommendations. |
| **Embeddings** | Google Embeddings (`text-embedding-004`) | Context representations for similarity scoring. |
| **File Parsing** | PyMuPDF (`fitz`), Python-docx, PyPDF | PDF/Word text stream layout extraction. |
| **Auth** | JWT, Passlib (Bcrypt) | Secure route authorization. |

---

## 📂 Folder Structure

```
PolicySentinel/
├── backend/
│   ├── ai/                    # Gemini API & Vertex AI custom integration layer
│   ├── alembic/               # Alembic database migrations and version scripts
│   ├── api/                   # REST routing definitions (FastAPI endpoints)
│   ├── auth/                  # JWT security and password hashing utilities
│   ├── database/              # PostgreSQL connections and SQLAlchemy sessions
│   ├── domain/                # Shared exception schemas and entities
│   ├── graph/                 # Neo4j client connection and graph syncer scripts
│   ├── models/                # Database models (Policy, Clause, Obligation, etc.)
│   ├── schemas/               # Pydantic serialization definitions
│   ├── services/              # Core business services (Ingestion, Conflict engine)
│   ├── utils/                 # General logging helpers and retry wrappers
│   ├── main.py                # FastAPI app bootstrap setup
│   └── requirements.txt       # Python backend dependencies
├── frontend/
│   ├── public/                # Static public assets
│   ├── src/
│   │   ├── components/        # Shared components (Sidebar, Layouts, Metrics)
│   │   ├── hooks/             # TanStack Query React custom hooks
│   │   ├── pages/             # Route views (Dashboard, Upload, Graph, Registry)
│   │   ├── services/          # Axios HTTP network connection services
│   │   ├── types/             # TypeScript models mirroring backend schemas
│   │   ├── App.tsx            # React router definitions
│   │   └── main.tsx           # React bootstrap entry point
│   ├── package.json           # Frontend package scripts
│   └── vite.config.ts         # Vite server proxy mappings
├── demo-data/                 # Pre-generated compliance policies for testing
├── scripts/
│   └── setup/                 # Database seed and reset utility scripts
└── docker-compose.yml         # Container configuration file
```

---

## 🚀 Installation Guide

### Prerequisites
- **Python 3.12+**
- **Node.js 18+**
- **PostgreSQL 16**
- **Neo4j Desktop or Aura Instance**
- **Gemini API Key** (Google AI Studio)

---

### Step 1: Configure Environment Variables
Create a file named `.env` in the root directory:

```env
# --- Server Environment ---
ENV=development
SECRET_KEY=yoursecretjwtkeyhere
ACCESS_TOKEN_EXPIRE_MINUTES=60

# --- PostgreSQL Connection ---
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/policysentinel

# --- Neo4j Graph DB Connection ---
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=yourneo4jpassword

# --- Google Gemini AI API ---
GEMINI_API_KEY=AIzaSyYourGeminiApiKeyHere
```

---

### Step 2: Set Up Backend

1. Navigate to the backend folder and create a virtual environment:
   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\activate   # On Linux: source venv/bin/activate
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run Alembic migrations to apply DB schemas:
   ```bash
   alembic upgrade head
   ```

---

### Step 3: Set Up Frontend

1. Navigate to the frontend folder:
   ```bash
   cd ../frontend
   ```
2. Install Node packages:
   ```bash
   npm install
   ```

---

### Step 4: Seed Clean Demo Workspace
Reset historical databases and seed a clean company context mapping (Company ID: `6e671c26-dfd8-4ebe-832f-f5277432f865`) and pre-generate testing files:
```bash
cd ..
python scripts/setup/reset_db_clean.py
python scripts/setup/generate_demo_pdfs.py
```

---

## 🏃 Running the Project

### Running Backend API
```bash
cd backend
venv\Scripts\activate
uvicorn backend.main:app --reload
```
*API will run at: `http://localhost:8000` (API Docs: `http://localhost:8000/docs`)*

### Running Frontend Client
```bash
cd frontend
npm run dev
```
*Vite dev server will run at: `http://localhost:3000`*

---

## 🔌 API Overview

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| **POST** | `/api/v1/auth/login` | Login to retrieve JWT Bearer token | No |
| **POST** | `/api/v1/uploads/policies` | Upload policy PDF & trigger automatic compliance parsing | Yes |
| **GET** | `/api/v1/policies` | List all uploaded organization policies | Yes |
| **GET** | `/api/v1/clauses` | Retrieve hierarchical clause trees for a policy | Yes |
| **GET** | `/api/v1/obligations` | List all extracted compliance obligations | Yes |
| **GET** | `/api/v1/conflicts` | List semantic anomalies and modality conflicts | Yes |
| **GET** | `/api/v1/regulatory-dashboard/summary` | Get external framework (GDPR/ISO) alignment stats | Yes |
| **GET** | `/api/v1/graph` | Retrieve nodes/edges matching search for Graph rendering | Yes |

---

## 🌟 Future Enhancements

- [ ] **🤖 Real-time Legal Regulation Scraping**: Auto-update framework knowledge bases using real-time scraping of federal registry databases (RBI, GDPR updates).
- [ ] **🔐 Active Directory / SSO Integration**: Implement corporate LDAP / SAML single sign-on flows.
- [ ] **🔄 Multi-Version Diffing Interface**: Side-by-side interactive redlines highlighting semantic differences directly between Policy Version draft iterations.
- [ ] **📈 Advanced Compliance Prediction**: Machine learning models predicting downstream audit failures based on compliance history patterns.

---

## 📄 License
Distributed under the **MIT License**. See `LICENSE` for more information.

---

## 🤝 Acknowledgements
- [Google AI Studio (Gemini SDK)](https://ai.google.dev/)
- [FastAPI Framework](https://fastapi.tiangolo.com)
- [Neo4j Graph Database](https://neo4j.com)
- [PyMuPDF Parser](https://pymupdf.readthedocs.io/)
