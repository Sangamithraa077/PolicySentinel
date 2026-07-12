# PolicySentinel Interactive Compliance Demo Guide

This guide details how to verify and demonstrate all core features of **PolicySentinel** using the pre-generated custom policy PDF files inside the `demo-data/` directory.

---

## Seeded Testing Credentials
To upload policies or query company scores, use these seeded administrative parameters:
- **Company Name**: `Acme Global Corporation`
- **Company ID**: `6e671c26-dfd8-4ebe-832f-f5277432f865`
- **Administrator Email**: `admin@acmeglobal.com`
- **Administrator User ID**: `f23c1df1-cb4f-4729-beb5-0b27315c9f2b`
- **Administrator Password**: `DemoPassword123!`

---

## Step 1: Upload Information Security Policy v1

### Ingestion Action
1. Go to the **Upload** page (`/upload`).
2. Input the following details:
   - **Company**: `Acme Global Corporation`
   - **Policy Title**: `Information Security Policy v1`
   - **User ID**: `f23c1df1-cb4f-4729-beb5-0b27315c9f2b`
   - **Version Number**: `1`
3. Drag & drop the file `demo-data/Information_Security_Policy_v1.pdf` and click **Upload**.

### Expected System Behaviour
1. **File Hashing & Storage**: The system hashes the file and stores it locally under `uploads/companies/6e671c26-dfd8-4ebe-832f-f5277432f865/policies/`.
2. **Text Extraction**: PyMuPDF automatically extracts the text content page-by-page.
3. **Clause Segmentation**: Splits the text into structured nodes (e.g., Section 1, Section 2, Section 3, and individual clauses like 1.1, 1.2, 2.1, 2.2).
4. **Obligation Extraction**: Gemini identifies legal compliance metrics, mapping subjects (e.g., "Corporate assets"), actions ("be accessed"), objects ("company-managed laptops"), modalities ("must"), and compliance categories ("Security").
5. **Regulatory Mapping**: Links:
   - Clause 2.1 (passwords every 90 days) to **ISO 27001** password parameters.
   - Clause 3.1 (data classification) to **GDPR Article 5** data protection guidelines.

---

## Step 2: Upload Remote Work Policy v2

### Ingestion Action
1. Go to the **Upload** page (`/upload`).
2. Input the following details:
   - **Company**: `Acme Global Corporation`
   - **Policy Title**: `Remote Work Policy v2`
   - **User ID**: `f23c1df1-cb4f-4729-beb5-0b27315c9f2b`
   - **Version Number**: `1`
3. Drag & drop the file `demo-data/Remote_Work_Policy_v2.pdf` and click **Upload**.

### Expected System Behaviour
Upon uploading, PolicySentinel automatically triggers a **Cross-Policy Semantic Ingestion Comparison**.

---

## Expected Analysis Findings

### 1. Exact Matches & Redundancies
- **Exact Match**: `Clause 3.1: Data Classification` is identical in both files. The system classifies it as an exact match and flags no conflicts.
- **Redundancy**: `Clause 3.2: Log Purging` (Document 1) and `Clause 3.2: Event Archiving` (Document 2) refer to archiving server logs monthly. The semantic model marks them as **Redundant**.

### 2. Direct & Temporal Conflicts
- **Device Usage Conflict**:
  - *Policy 1 (1.1)*: `company-managed laptops only`.
  - *Policy 2 (1.1)*: `Personal laptops allowed`.
  - *Outcome*: Flags a **High Severity Modality Contradiction**.
- **Password Renewal Temporal Conflict**:
  - *Policy 1 (2.1)*: passwords change every **90 days**.
  - *Policy 2 (2.1)*: passwords change every **180 days**.
  - *Outcome*: Flags a **Temporal Frequency Conflict** (90-day vs. 180-day cycle discrepancy).
- **Endpoint Storage Conflict**:
  - *Policy 1 (1.2)*: `Local storage is prohibited`.
  - *Policy 2 (1.2)*: `Local storage is allowed if encrypted`.
  - *Outcome*: Flags an **Operational Control Anomaly**.

### 3. Strength Conflicts (Modality Shifts)
- **VPN Protection**:
  - *Policy 1 (2.2)*: `VPN must always be used` (Modality: **Must**).
  - *Policy 2 (2.2)*: `VPN is recommended` (Modality: **Should**).
  - *Outcome*: Flags a **Modality Strength Shift Conflict** (Mandate weakened to recommendation).

### 4. Complementary Links
- `Clause 3.3 (Policy 1) account disabling` and `Clause 3.3 (Policy 2) physical offboarding key return` are flagged as **Complementary** offboarding workflows.

### 5. Regulatory Coverage Mappings
- **GDPR**: Linked to Document 1 (data labeling/classification).
- **ISO 27001**: Linked to Document 1 (90-day password mandates).
- **RBI**: Linked to Document 2 (remote connection access rules).
- **SEBI**: Linked to Document 2 (event log archiving controls).

### 6. AI Recommendation Resolutions
- The AI formulates resolution redlines suggesting a unified policy stance:
  - e.g. Standardize log retention, enforce corporate laptop restrictions, and align remote connections.

---

## Dashboard and Graph Representation
- **Policy Health Score**: Shows deductions from 100 based on active conflicts, grading the tenant (e.g. Grade B/C).
- **Knowledge Graph**: Navigating to `/knowledge-graph` reveals an interactive SVG mapping:
  - Policy nodes connected to their respective Clauses.
  - Clauses connected to their obligations.
  - Obligations connected to each other via red `CONFLICTS_WITH` lines and green `MAPS_TO` regulation lines.
