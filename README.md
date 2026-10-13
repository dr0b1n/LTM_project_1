# RAG-Powered Vendor Compliance Auditor

A local-first demonstration application that reviews synthetic vendor contracts against version-controlled security, privacy, and operational policies. The application uses Retrieval-Augmented Generation (RAG) to retrieve relevant contract evidence and a local Ollama instruction model to produce structured, evidence-backed findings.

> **Important:** This repository is a synthetic, non-production demonstration. It does not provide legal advice or make legally authoritative compliance decisions. Generated findings, especially missing, ambiguous, conflicting, low-confidence, or fallback findings, require qualified human review.

## Contents

- [Project Overview](#project-overview)
- [Problem Statement](#problem-statement)
- [Current Implemented State](#current-implemented-state)
- [End-to-End Workflow](#end-to-end-workflow)
- [Architecture](#architecture)
- [Policy Set](#policy-set)
- [Synthetic Dataset](#synthetic-dataset)
- [Finding Statuses](#finding-statuses)
- [Privacy and PII Redaction](#privacy-and-pii-redaction)
- [Embeddings, ChromaDB, and Retrieval](#embeddings-chromadb-and-retrieval)
- [Structured Local Model Analysis](#structured-local-model-analysis)
- [Complete Audit, Evaluation, and Export](#complete-audit-evaluation-and-export)
- [Repository Structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Demonstration Guide](#demonstration-guide)
- [Testing](#testing)
- [Runtime Data and Git](#runtime-data-and-git)
- [Known Limitations](#known-limitations)
- [Troubleshooting](#troubleshooting)
- [Future Enhancements](#future-enhancements)
- [Responsible Use](#responsible-use)

## Project Overview

The project demonstrates a complete local RAG workflow for vendor-contract review:

- Upload a text-based vendor-contract PDF.
- Extract text while preserving page numbers.
- Detect and replace selected PII before AI processing.
- Split sanitized text into page-aware chunks.
- Generate local embeddings with Ollama.
- Store sanitized chunks and metadata in ChromaDB.
- Retrieve the top three chunks relevant to a selected policy.
- Generate a structured finding with a local instruction model.
- Validate model output with Pydantic.
- Preserve authoritative evidence text, page number, chunk ID, and retrieval distance.
- Run all policies as a complete audit.
- Compare generated findings with synthetic ground truth where available.
- Download complete audit results as JSON and a summary as CSV.

The application is intentionally local-first. Contract processing, embeddings, retrieval, and model inference are designed to run on the same machine.

## Problem Statement

Vendor agreements may contain important commitments relating to encryption, access control, incident notification, audit rights, retention, deletion, subprocessors, logging, vulnerability remediation, and service continuity. Manual review can be repetitive and may miss clauses, exceptions, conflicts, or absent commitments.

The application is designed as a review assistant rather than an autonomous decision-maker. For each policy, it aims to show:

1. the explicit policy requirement;
2. the most relevant sanitized contract evidence;
3. the source page and chunk identifier;
4. a structured compliance status;
5. an explanation and remediation recommendation; and
6. whether human review is required.

## Current Implemented State

The current application includes the following working capabilities.

### Document processing

- Streamlit PDF upload
- Text-based PDF validation and extraction with `pypdf`
- Page count, source filename, and character count
- Page-by-page extracted-text preview
- Controlled rejection of empty, invalid, encrypted, or textless PDFs

### Privacy processing

- Microsoft Presidio analysis
- spaCy `en_core_web_lg` NLP model
- Allow-listed PII entities:
  - `PERSON`
  - `EMAIL_ADDRESS`
  - `PHONE_NUMBER`
  - `IP_ADDRESS`
- Custom recognition for synthetic `.test` email addresses
- Typed placeholders such as `<PERSON>` and `<EMAIL_ADDRESS>`
- Sanitized-page preview and PII detection counts
- Sanitized-only downstream boundary

### Chunking and retrieval

- Paragraph-based chunking with long-text splitting
- Unique chunk identifiers
- Preserved page number, source filename, and document ID
- Local embeddings through Ollama
- ChromaDB persistent vector storage
- Top-three semantic retrieval per policy
- Retrieval display with rank, page, chunk ID, text, and vector distance
- Replacement indexing to avoid duplicating the same document ID

### Structured findings

- Local Ollama instruction-model analysis
- Strict structured-output schema
- Pydantic validation
- Model-selected chunk validation
- Authoritative evidence metadata supplied by the application
- Rejection of invented chunk IDs
- Human-review enforcement for material or uncertain statuses
- Conservative `REVIEW_REQUIRED` fallback in the complete-audit workflow when a smaller model returns invalid output

### Complete audit and reporting

- Single-policy evidence review and finding generation
- Complete audit across the full policy set
- Per-policy progress display
- Partial-failure isolation
- Consolidated audit summary
- Status breakdown and detailed finding inspection
- Synthetic ground-truth comparison when the matching expected-findings file exists
- Status-match and page-match metrics
- Audit JSON download
- Findings CSV download

### Interface

The Streamlit interface uses a review-oriented visual design with:

- warm white surfaces;
- plum and burgundy headers;
- muted gold accents;
- workflow-stage indicators;
- policy, evidence, and finding sections;
- executive audit metrics;
- readable rounded text areas; and
- clear synthetic-data and responsible-use notices.

## End-to-End Workflow

```text
Synthetic contract PDF
        |
        v
PDF validation and page-level extraction
        |
        v
Presidio and spaCy PII detection
        |
        v
Typed placeholder replacement
        |
        v
Sanitized page-aware chunks
        |
        v
Ollama granite-embedding:30m
        |
        v
ChromaDB vector collection
        |
        v
Policy requirement embedding
        |
        v
Top-three sanitized evidence chunks
        |
        v
Local Ollama policy/evidence comparison
        |
        v
Pydantic validation and evidence integrity checks
        |
        v
Single finding or complete policy-set audit
        |
        v
Evaluation, JSON export, CSV export, and human review
```

## Architecture

```text
Streamlit UI
    |
    +-- Document extractor (pypdf)
    |
    +-- PII redactor (Presidio + spaCy)
    |
    +-- Chunker (sanitized text only)
    |
    +-- Ollama embedder (granite-embedding:30m)
    |
    +-- ChromaDB vector store
    |
    +-- Policy retriever (top 3 chunks)
    |
    +-- Ollama auditor (local instruction model)
    |
    +-- Pydantic finding validation
    |
    +-- Batch audit runner
    |
    +-- Synthetic evaluator
    |
    +-- JSON and CSV report exporters
```

The demonstration uses direct local Python calls rather than a separate API layer. Authentication, multi-user services, background workers, and enterprise deployment are outside the current scope.

## Policy Set

Policies are stored in:

```text
policies/sample_policies.json
```

The active policy baseline contains 12 controls:

1. `POL-001` — Encryption at Rest
2. `POL-002` — Encryption in Transit
3. `POL-003` — Identity and Access Management
4. `POL-004` — Privileged Access Security
5. `POL-005` — Security Logging and Monitoring
6. `POL-006` — Vulnerability Remediation
7. `POL-007` — Security Incident Notification
8. `POL-008` — Audit and Assurance Rights
9. `POL-009` — Data Retention
10. `POL-010` — Secure Data Return and Deletion
11. `POL-011` — Subprocessor Management
12. `POL-012` — Service Continuity and Recovery

Each policy includes:

- stable policy ID;
- title and category;
- explicit requirement;
- severity;
- expected contractual commitment;
- remediation guidance; and
- policy version.

Policies are stored as JSON because they are reviewable business rules rather than executable application logic.

## Synthetic Dataset

The active synthetic dataset is stored under:

```text
synthetic_data/
```

The repository contains multiple synthetic contracts so the application can demonstrate varied contract quality, different clause styles, missing obligations, measurable commitments, and selected conflicts without using confidential agreements.

### 1. Cloud Analytics Services Agreement

Files:

```text
synthetic_data/cloud_analytics_agreement.pdf
synthetic_data/cloud_analytics_agreement.txt
synthetic_data/cloud_analytics_agreement_expected_findings.json
```

Characteristics:

- 12-page primary review contract
- explicit encryption, access, and logging clauses
- measurable continuity commitments
- deliberately weaker incident-notification and vulnerability-remediation terms
- ambiguous retention language
- controlled subprocessor-notification conflict
- suitable for demonstrating `COMPLIANT`, `NON_COMPLIANT`, `AMBIGUOUS`, and `REVIEW_REQUIRED` outcomes

### 2. Managed IT Support Agreement

Files:

```text
synthetic_data/managed_it_support_agreement.pdf
synthetic_data/managed_it_support_agreement.txt
synthetic_data/managed_it_support_agreement_expected_findings.json
```

Characteristics:

- 10-page weaker vendor agreement
- several vague or absent security commitments
- useful for testing `MISSING` and `AMBIGUOUS` findings
- includes weaker shared-access, logging, incident, deletion, and continuity language
- helps verify that nearest-neighbor retrieval is not automatically treated as proof of compliance

### 3. Customer Support SaaS Agreement

Files:

```text
synthetic_data/customer_support_saas_agreement.pdf
synthetic_data/customer_support_saas_agreement.txt
synthetic_data/customer_support_saas_agreement_expected_findings.json
```

Characteristics:

- 14-page stronger contract
- explicit encryption, access, logging, incident, subprocessor, and recovery commitments
- selected exceptions and international-support considerations
- useful for testing a mostly compliant agreement with a smaller number of review points
- includes contract text that must remain untrusted evidence rather than model instructions

### 4. Synthetic Vendor Contract v2

Files:

```text
synthetic_data/synthetic_vendor_contract_v2.pdf
synthetic_data/synthetic_vendor_contract_v2.txt
synthetic_data/synthetic_vendor_contract_v2_expected_findings.json
```

Characteristics:

- earlier expanded synthetic agreement retained as an additional test document
- contains clear security, incident, retention, subprocessor, and continuity clauses
- supports regression and comparison with the newer multi-contract dataset

### 5. Seven-Page Vendor Services Agreement

File:

```text
synthetic_data/synthetic_vendor_services_agreement_7_pages.pdf
```

Characteristics:

- seven-page text-heavy synthetic agreement
- designed for more reliable retrieval and classification with a smaller local instruction model
- uses explicit headings, direct obligations, concrete deadlines, and fewer vague clauses
- includes clear commitments for encryption, TLS, MFA, access reviews, log retention, vulnerability remediation, incident notification, backups, recovery objectives, availability, subprocessors, deletion, audit rights, and AI-use restrictions

The current repository inventory does not include a matching text source or expected-findings JSON for this seven-page PDF. The PDF can be used for extraction, redaction, indexing, retrieval, and live finding generation. Ground-truth evaluation requires a matching file named:

```text
synthetic_data/synthetic_vendor_services_agreement_7_pages_expected_findings.json
```

### Dataset documentation

The active dataset also includes:

```text
synthetic_data/README_DATASET.md
```

### Archived data

Previous dataset and policy versions are kept locally under:

```text
synthetic_data/archive/
policies/archive/
```

These archive directories are ignored by Git. Active synthetic files listed above are tracked.

### Why synthetic data is used

- **Confidentiality:** Real vendor contracts may contain sensitive commercial, technical, personal, and legal information.
- **Known ground truth:** Expected statuses and expected pages can be defined in advance.
- **Repeatability:** The same input can be reused for extraction, privacy, retrieval, and model testing.
- **Coverage:** The dataset deliberately includes compliant, non-compliant, ambiguous, missing, and conflicting scenarios.
- **Safe PII testing:** Fictional or reserved values can be used to demonstrate redaction.
- **Debugging:** Expected evidence helps isolate extraction, chunking, retrieval, or generation failures.
- **Responsible review:** The prototype can be demonstrated without implying readiness for real confidential contracts.

### Ground-truth separation

Expected-findings JSON files are used only after model generation for evaluation. They must not be embedded, stored in ChromaDB, passed to retrieval, or included in the Ollama prompt.

## Finding Statuses

The structured finding model supports:

- `COMPLIANT` — retrieved evidence clearly satisfies the policy requirement.
- `NON_COMPLIANT` — relevant evidence conflicts with or falls below the policy requirement.
- `AMBIGUOUS` — relevant language exists but is vague, incomplete, or non-measurable.
- `MISSING` — no retrieved evidence establishes the required commitment.
- `REVIEW_REQUIRED` — evidence or model output is conflicting, weak, malformed, or otherwise unsafe to classify conclusively.

Non-compliant, ambiguous, missing, and review-required findings are forced to human review.

## Privacy and PII Redaction

Redaction occurs before chunking, embedding, ChromaDB storage, retrieval, and model analysis.

```text
Original extracted text
        |
        v
Presidio Analyzer
        |
        v
Selected entity detections
        |
        v
Presidio Anonymizer
        |
        v
Typed placeholders
        |
        v
Sanitized chunks only
```

Typed placeholders preserve sentence structure while removing selected values:

```text
Before: Contact Alex Morgan at alex.morgan@example.test.
After:  Contact <PERSON> at <EMAIL_ADDRESS>.
```

Automated PII detection can produce false positives and false negatives. A production system would require organization-specific recognizers, evaluation, privacy review, and secure retention controls.

## Embeddings, ChromaDB, and Retrieval

### Embedding model

```text
granite-embedding:30m
```

Expected dimension:

```text
384
```

The application validates embedding count, numeric values, finite values, and vector dimensions.

### ChromaDB storage

ChromaDB stores only sanitized chunks and retrieval metadata:

- chunk ID;
- sanitized text;
- embedding;
- document ID;
- source filename;
- page number; and
- sanitized flag.

Runtime ChromaDB data is written to:

```text
data/chroma/
```

This directory is generated locally and excluded from Git. The source repository retains `data/.gitkeep` only when the runtime directory structure needs to be represented.

### Retrieval behavior

For a selected policy, the application retrieves the top three sanitized chunks. Retrieval rank and distance are displayed for transparency. A top-ranked result is only a candidate evidence passage and does not prove compliance.

## Structured Local Model Analysis

The application uses a configurable local Ollama instruction model. The current project supports changing the generation model through:

```text
OLLAMA_MODEL
```

The embedding model is configured through:

```text
OLLAMA_EMBEDDING_MODEL
```

The shared Ollama client reads:

```text
OLLAMA_HOST
```

Native execution normally uses the local Ollama endpoint. Container deployment can provide a different host address without changing the auditor or embedder code.

### Model responsibilities

The model generates only a constrained finding draft:

- status;
- confidence;
- explanation;
- selected chunk ID;
- recommended remediation; and
- human-review flag.

The application supplies authoritative values for:

- policy ID and version;
- policy requirement;
- severity;
- evidence text;
- page number;
- chunk ID validation;
- retrieval distance;
- embedding model;
- inference model; and
- prompt version.

If the model cites a chunk that was not retrieved, the finding is rejected.

### Smaller-model resilience

The complete-audit runner can convert recoverable model-validation errors into conservative `REVIEW_REQUIRED` fallback findings. A fallback finding:

- uses confidence `0.0`;
- requires human review;
- preserves the highest-ranked retrieved chunk for inspection; and
- does not claim that the chunk proves compliance.

This behavior improves batch completion while keeping the limitation visible.

## Complete Audit, Evaluation, and Export

After sanitized chunks are indexed, the application supports two workflows.

### Single-policy evidence review

1. Select a policy.
2. Retrieve the top three evidence chunks.
3. Inspect ranks, pages, chunk IDs, text, and distances.
4. Generate a structured finding for that policy.

### Complete contract audit

1. Attempt every policy in the active 12-policy baseline.
2. Retrieve evidence independently for each policy.
3. Generate and validate one finding per policy.
4. Isolate policy-level failures so one failure does not discard the full run.
5. Display consolidated status metrics and findings.
6. Compare generated results with matching synthetic ground truth where available.
7. Export full JSON and summary CSV reports.

### Evaluation

When the uploaded PDF stem matches an expected-findings file, the evaluator compares:

- generated status against expected status; and
- generated evidence page against expected pages.

The UI reports status-match and page-match percentages. These metrics are a small synthetic benchmark, not a production accuracy claim.

## Repository Structure

```text
LTM_project_1/
|-- app/
|   |-- .streamlit/
|   |   `-- config.toml
|   |-- data/
|   |   |-- mock_findings.py
|   |   `-- sample_policies.py
|   |-- models/
|   |   |-- audit_run.py
|   |   |-- chunk.py
|   |   |-- document.py
|   |   |-- evaluation.py
|   |   |-- finding.py
|   |   |-- policy.py
|   |   `-- retrieval.py
|   |-- services/
|   |   |-- audit_runner.py
|   |   |-- auditor.py
|   |   |-- chunker.py
|   |   |-- document_extractor.py
|   |   |-- embedder.py
|   |   |-- evaluator.py
|   |   |-- ollama_client.py
|   |   |-- pii_redactor.py
|   |   |-- policy_loader.py
|   |   |-- report_exporter.py
|   |   |-- retriever.py
|   |   `-- vector_store.py
|   `-- ui/
|       `-- main.py
|-- data/
|   `-- .gitkeep              # Optional tracked placeholder
|-- policies/
|   `-- sample_policies.json
|-- prompts/
|   `-- compliance_audit_v1.txt
|-- synthetic_data/
|   |-- README_DATASET.md
|   |-- cloud_analytics_agreement.pdf
|   |-- cloud_analytics_agreement.txt
|   |-- cloud_analytics_agreement_expected_findings.json
|   |-- customer_support_saas_agreement.pdf
|   |-- customer_support_saas_agreement.txt
|   |-- customer_support_saas_agreement_expected_findings.json
|   |-- managed_it_support_agreement.pdf
|   |-- managed_it_support_agreement.txt
|   |-- managed_it_support_agreement_expected_findings.json
|   |-- synthetic_vendor_contract_v2.pdf
|   |-- synthetic_vendor_contract_v2.txt
|   |-- synthetic_vendor_contract_v2_expected_findings.json
|   `-- synthetic_vendor_services_agreement_7_pages.pdf
|-- tests/
|   |-- test_audit_runner.py
|   |-- test_auditor.py
|   |-- test_chunker.py
|   |-- test_document_extractor.py
|   |-- test_embedder.py
|   |-- test_evaluator.py
|   |-- test_finding.py
|   |-- test_pii_redactor.py
|   |-- test_policy_loader.py
|   |-- test_report_exporter.py
|   `-- test_vector_store.py
|-- .env.example
|-- .gitattributes
|-- .gitignore
|-- pytest.ini
|-- rag_project_master_context_revised.txt
|-- README.md
|-- requirements.txt
`-- T9925_VITV_DANIELROBIN.pptx
```

Generated caches, ChromaDB files, archived datasets, archived policies, and development backup files are intentionally excluded from Git.

### Key active implementation files

```text
app/models/audit_run.py
app/models/evaluation.py
app/services/audit_runner.py
app/services/auditor.py
app/services/embedder.py
app/services/evaluator.py
app/services/ollama_client.py
app/services/report_exporter.py
app/ui/main.py
policies/sample_policies.json
prompts/compliance_audit_v1.txt
```

## Prerequisites

- Python 3.12
- Git
- Ollama
- `granite-embedding:30m`
- An installed local instruction model configured through `OLLAMA_MODEL`
- spaCy `en_core_web_lg`

## Installation

### 1. Clone the repository

```powershell
git clone https://github.com/dr0b1n/LTM_project_1.git
cd LTM_project_1
```

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip check
```

### 4. Verify the spaCy model

```powershell
python -c "import spacy; spacy.load('en_core_web_lg'); print('spaCy model ready')"
```

If the model is unavailable and downloads are permitted:

```powershell
python -m spacy download en_core_web_lg
```

### 5. Verify Ollama and models

```powershell
ollama --version
ollama list
```

Pull the embedding model when permitted:

```powershell
ollama pull granite-embedding:30m
```

Pull the exact instruction-model tag selected for the environment. The application model can be changed without modifying source code by setting `OLLAMA_MODEL`.

## Configuration

The main runtime variables are:

```text
OLLAMA_HOST
OLLAMA_MODEL
OLLAMA_EMBEDDING_MODEL
```

Example native PowerShell configuration:

```powershell
Remove-Item Env:OLLAMA_HOST -ErrorAction SilentlyContinue
$env:OLLAMA_MODEL = "granite4:3b"
$env:OLLAMA_EMBEDDING_MODEL = "granite-embedding:30m"
```

The default shared Ollama client uses the local Ollama API when `OLLAMA_HOST` is not set.

Keep real secrets or machine-specific values outside Git. `.env.example` may document safe configuration names, but `.env` is ignored.

## Running the Application

```powershell
python -m streamlit run app\ui\main.py
```

Streamlit prints the local application address in the terminal.

## Demonstration Guide

For a broad policy demonstration, use:

```text
synthetic_data/cloud_analytics_agreement.pdf
```

Recommended single-policy examples:

- `POL-001` — explicit compliant encryption commitment
- `POL-006` — measurable vulnerability-remediation comparison
- `POL-007` — incident-notification threshold comparison
- `POL-009` — ambiguous retention wording
- `POL-011` — conflicting subprocessor language

For a faster and clearer smaller-model demonstration, use:

```text
synthetic_data/synthetic_vendor_services_agreement_7_pages.pdf
```

### Suggested live flow

1. Upload a synthetic PDF.
2. Extract text and show page metadata.
3. Run PII redaction and create sanitized chunks.
4. Show the sanitized preview and chunk metadata.
5. Index sanitized chunks.
6. Select one policy and retrieve the top three chunks.
7. Generate one structured finding.
8. Run the complete audit.
9. Show consolidated results, evaluation where available, and exports.
10. Explain human-review requirements and known limitations.

## Testing

Run all tests:

```powershell
python -m pytest -v
```

Compile the application and tests:

```powershell
python -m compileall app tests -q
```

Check installed dependencies:

```powershell
python -m pip check
```

The active test suite covers:

- PDF validation and extraction;
- PII redaction;
- chunk construction and metadata;
- policy JSON loading;
- embedding validation;
- ChromaDB storage behavior;
- structured finding validation;
- authoritative evidence metadata;
- invalid JSON and invented chunk handling;
- complete-audit partial-failure isolation;
- synthetic evaluation; and
- JSON and CSV report export.

## Runtime Data and Git

The following are generated locally and ignored:

```text
data/chroma/
data/uploads/
data/sanitized/
data/audit/
data/output/
```

They can contain generated indexes, uploaded content, sanitized content, or audit output and should not be committed.

The repository may track:

```text
data/.gitkeep
```

so the runtime data parent directory exists after cloning.

The following are also ignored:

- Python virtual environments;
- Python and pytest caches;
- `.env`;
- credentials and certificates;
- archived policies and datasets;
- backup source copies; and
- local model files.

## Known Limitations

- Synthetic-data demonstration rather than production software
- Text-based PDFs only
- No OCR for scanned contracts
- No robust table or complex-layout extraction
- Paragraph-based chunking without reranking
- Local-model output can vary
- Smaller models may produce more validation fallbacks
- Synthetic evaluation is not a production accuracy benchmark
- Presidio can miss sensitive data or produce false positives
- No authentication, authorization, or multi-user isolation
- No malware scanning or upload quarantine
- No secure production document-retention workflow
- No production relational database
- No formal legal, privacy, compliance, or security approval
- No enterprise observability, high availability, or scaling layer

## Troubleshooting

### `ModuleNotFoundError: No module named 'app'`

Run Streamlit from the repository root:

```powershell
python -m streamlit run app\ui\main.py
```

### spaCy model unavailable

```powershell
python -c "import spacy; spacy.load('en_core_web_lg'); print('ready')"
```

### Ollama unreachable

```powershell
ollama list
Invoke-RestMethod -Uri "http://localhost:11434/api/tags"
```

Confirm that `OLLAMA_HOST` is correct for the current environment.

### Embedding model unavailable

```powershell
ollama list
ollama pull granite-embedding:30m
```

### Wrong embedding dimension

```powershell
python -c "from app.services.embedder import embed_texts; v=embed_texts(['test']); print(len(v), len(v[0]))"
```

Expected:

```text
1 384
```

### Stale vector data

Stop the application and remove only the generated ChromaDB directory:

```powershell
Remove-Item data\chroma -Recurse -Force
```

Then restart the application and index the contract again.

### Pytest import mismatch from archived test copies

The repository uses `pytest.ini` to restrict normal collection to the active `tests/` directory. Remove generated caches if necessary:

```powershell
Remove-Item .pytest_cache -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Directory -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force
```

## Future Enhancements

Potential production improvements include:

- authentication, SSO, and role-based access control;
- multi-user and tenant isolation;
- malware scanning and upload quarantine;
- OCR and layout-aware extraction;
- organization-specific PII recognizers;
- secure document storage and retention;
- relational audit history and policy lifecycle management;
- reviewer feedback and finding disposition;
- retrieval reranking and larger evaluation datasets;
- formal prompt and model governance;
- structured logging without raw contract text;
- deployment health checks and monitoring;
- container packaging and CI/CD security gates; and
- formal legal, privacy, compliance, and security review.

## Responsible Use

The application is a review aid. Users remain responsible for:

- verifying retrieved evidence;
- reading the surrounding contract context;
- checking policy applicability and policy version;
- resolving conflicting or incomplete clauses;
- assessing legal meaning;
- reviewing fallback findings;
- approving remediation language; and
- making the final compliance decision.

A generated explanation must not replace direct contract evidence. A nearest-neighbor retrieval result must not be treated as proof of compliance, and absence of a retrieved clause must not be considered conclusive without human review.

## License and Distribution

This repository is an educational, synthetic, non-production demonstration. Review applicable licenses and organizational approvals for Python packages, local models, and external runtimes before broader distribution or use.
