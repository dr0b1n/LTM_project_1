# RAG-Powered Vendor Compliance Auditor

A privacy-focused, local-first demonstration application that reviews a synthetic vendor agreement against a small set of security, privacy, and operational-governance policies. The project uses Retrieval-Augmented Generation (RAG) to retrieve relevant contract evidence and a local language model to produce structured, evidence-backed findings.

> **Important:** This repository is a synthetic, non-production demonstration. It does not provide legal advice, does not make legally authoritative compliance decisions, and must not be used as a substitute for qualified legal, privacy, security, procurement, or compliance review. Material, ambiguous, missing, conflicting, and low-confidence findings require human review.

## Contents

- [Purpose](#purpose)
- [Problem Statement](#problem-statement)
- [Objectives](#objectives)
- [Features](#features)
- [End-to-End Workflow](#end-to-end-workflow)
- [Architecture](#architecture)
- [How RAG Is Used](#how-rag-is-used)
- [Policy Model](#policy-model)
- [Finding Statuses](#finding-statuses)
- [Synthetic Dataset](#synthetic-dataset)
- [Privacy and PII Redaction](#privacy-and-pii-redaction)
- [Embeddings and ChromaDB](#embeddings-and-chromadb)
- [Structured Local LLM Analysis](#structured-local-llm-analysis)
- [Data Storage](#data-storage)
- [Repository Structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Demonstration Guide](#demonstration-guide)
- [Testing](#testing)
- [Expected Demonstration Outcomes](#expected-demonstration-outcomes)
- [Security Boundaries](#security-boundaries)
- [Known Limitations](#known-limitations)
- [Troubleshooting](#troubleshooting)
- [Future Production Enhancements](#future-production-enhancements)
- [Responsible Use](#responsible-use)

## Purpose

The purpose of this project is to demonstrate that the following technologies can be connected into a clear, repeatable, local RAG workflow:

- Streamlit user interface
- Text-based PDF extraction
- Microsoft Presidio and spaCy PII redaction
- Paragraph-based contract chunking
- Local Ollama embeddings
- ChromaDB vector storage and retrieval
- Policy-driven evidence comparison
- Local Ollama language-model analysis
- Pydantic-validated structured findings
- Evidence and page citations in the user interface

The primary success criterion is a stable, understandable end-to-end demonstration using a small synthetic dataset. Production scalability, exhaustive policy coverage, formal legal accuracy, enterprise deployment, and large-scale RAG evaluation are outside the demonstration scope.

## Problem Statement

Vendor agreements can contain important commitments relating to encryption, incident notification, audit rights, data retention, deletion, subprocessors, availability, disaster recovery, and other controls. Manual review can be slow, repetitive, inconsistent, and vulnerable to missed clauses.

A useful review assistant should not simply declare that a contract is compliant. The application should:

1. identify the policy being evaluated;
2. retrieve the most relevant contract evidence;
3. preserve the source page and chunk identifier;
4. compare the evidence with an explicit policy requirement;
5. return a structured status, explanation, and recommendation; and
6. require human review when the evidence is missing, ambiguous, conflicting, or uncertain.

## Objectives

The demonstration is designed to:

1. accept a text-based PDF through a Streamlit interface;
2. extract text while preserving page metadata;
3. detect and replace selected PII before downstream AI processing;
4. split sanitized text into readable chunks;
5. generate 384-dimensional embeddings locally with Ollama;
6. store and query sanitized chunks in ChromaDB;
7. load explicit policies from version-controlled JSON;
8. retrieve the top contract evidence for each policy;
9. compare policy requirements with retrieved evidence using a local instruction model;
10. validate generated findings with Pydantic;
11. display status, severity, evidence, page, explanation, recommendation, and human-review requirements; and
12. use synthetic data so no real confidential contract is required.

## Features

### Document processing

- PDF upload through Streamlit
- Text-based PDF extraction with `pypdf`
- Page count, filename, and character-count display
- Page-by-page extraction preview
- Controlled rejection of invalid, encrypted, empty, or textless PDFs
- No OCR or scanned-document support in the demonstration

### Privacy processing

- Selected PII detection with Microsoft Presidio
- spaCy `en_core_web_lg` NLP model
- Typed replacement placeholders such as `<PERSON>` and `<EMAIL_ADDRESS>`
- Approved demonstration entity allow-list:
  - `PERSON`
  - `EMAIL_ADDRESS`
  - `PHONE_NUMBER`
  - `IP_ADDRESS`
- Custom recognizer support for the reserved `.test` synthetic email domain
- Redaction counts and sanitized-page preview
- Sanitized-only downstream processing boundary

### Chunking

- Simple paragraph-based chunking
- Long-text splitting when a paragraph exceeds the configured size
- Unique chunk IDs
- Preserved document ID, source filename, and page number
- Explicit `sanitized` metadata flag

### Embeddings and retrieval

- Local embedding generation through Ollama
- Embedding model: `granite-embedding:30m`
- Expected embedding dimension: 384
- Persistent ChromaDB collection
- Sanitized document text and metadata storage
- Top-three semantic evidence retrieval per policy
- Retrieval display with rank, page, chunk ID, and vector distance
- Replacement indexing to avoid duplicating the same document

### Policy-driven audit

- Version-controlled JSON policy set
- Explicit policy requirements and thresholds
- Policy severity and version tracking
- Local LLM comparison against retrieved evidence
- Structured JSON output
- Pydantic validation
- Human-review flag
- Evidence-backed explanations and remediation recommendations
- Rejection or controlled handling of malformed model output

### Interface

- Review-oriented Streamlit dashboard
- Upload and processing workflow
- Document extraction preview
- Sanitized-text and chunk preview
- Policy viewer
- Vector-indexing controls
- Evidence-retrieval controls
- Finding metrics and status display
- Evidence, page, explanation, and recommendation viewer
- Clear synthetic-data and non-production disclaimers

## End-to-End Workflow

```text
Synthetic vendor contract PDF
            |
            v
File and PDF validation
            |
            v
Page-level text extraction
            |
            v
Presidio + spaCy PII detection
            |
            v
Typed placeholder replacement
            |
            v
Sanitized paragraph chunks
            |
            v
Ollama granite-embedding:30m
            |
            v
ChromaDB persistent collection
            |
            v
Policy requirement embedding
            |
            v
Top-k sanitized evidence retrieval
            |
            v
Local Ollama policy/evidence comparison
            |
            v
Pydantic structured-output validation
            |
            v
Streamlit finding and evidence display
            |
            v
Human review
```

## Architecture

The demonstration uses direct local Python function calls rather than a separate API tier. This is intentional: the smallest architecture is easier to run, inspect, explain, and complete within the project time limit.

```text
+-----------------------+
| Streamlit Interface   |
+-----------+-----------+
            |
            v
+-----------------------+
| Document Extractor    |
| pypdf                 |
+-----------+-----------+
            |
            v
+-----------------------+
| PII Redactor          |
| Presidio + spaCy      |
+-----------+-----------+
            |
            v
+-----------------------+
| Chunker               |
| Sanitized text only   |
+-----------+-----------+
            |
            v
+-----------------------+
| Local Embedder        |
| Ollama / Granite      |
+-----------+-----------+
            |
            v
+-----------------------+
| ChromaDB              |
| Vectors + metadata    |
+-----------+-----------+
            |
            v
+-----------------------+
| Retriever             |
| Top-k evidence        |
+-----------+-----------+
            |
            v
+-----------------------+
| Local Auditor         |
| Ollama + Pydantic     |
+-----------+-----------+
            |
            v
+-----------------------+
| Evidence-backed       |
| Streamlit Finding     |
+-----------------------+
```

### Why there is no FastAPI layer

A production system might separate the UI and backend using FastAPI. This demonstration uses direct calls because authentication, multi-user support, remote deployment, background workers, and service scaling are out of scope. Avoiding an unnecessary API keeps the review focused on the RAG and privacy workflow.

## How RAG Is Used

RAG stands for Retrieval-Augmented Generation. In this project, retrieval and generation have separate responsibilities.

### Retrieval

The system converts a policy requirement into an embedding and asks ChromaDB for the closest sanitized contract chunks. Retrieval returns possible evidence, not a compliance decision.

```text
Policy requirement
        |
        v
384-dimensional query embedding
        |
        v
ChromaDB similarity search
        |
        v
Top-three sanitized contract chunks
```

The returned evidence includes:

- sanitized clause text;
- document ID;
- source filename;
- page number;
- chunk ID; and
- vector distance.

### Generation

The local instruction model receives:

- the explicit policy requirement;
- severity and expected commitment;
- the retrieved evidence;
- page and chunk metadata; and
- strict output instructions.

The language model compares the evidence with the policy. The model must not invent policy thresholds or unsupported contract evidence.

### Important retrieval boundary

Vector retrieval always returns the nearest available content. A rank-one result does not prove compliance. If no relevant commitment exists, the final analysis should produce `MISSING` or `REVIEW_REQUIRED`, rather than treating an unrelated nearest-neighbor result as evidence.

## Policy Model

Policies are business rules defining what the organization expects from a vendor agreement. Policies are not contract clauses and are not generated by the language model.

Policies are stored at:

```text
policies/sample_policies.json
```

A policy record contains fields similar to:

```json
{
  "policy_id": "POL-002",
  "title": "Breach Notification",
  "category": "Incident Management",
  "requirement": "Vendor must notify the customer of a confirmed security incident within 72 hours.",
  "severity": "HIGH",
  "expected_commitment": "A notification deadline no longer than 72 hours after confirmation.",
  "remediation_guidance": "Amend the notification deadline to 72 hours or less after confirmation.",
  "policy_version": "v1"
}
```

### Why policies are stored as JSON

- Policies are data, not executable Python logic.
- Reviewers can inspect requirements without reading application code.
- Policy changes can be version-controlled.
- Stable IDs can be preserved across revisions.
- A policy version can be recorded with every finding.
- JSON can later be migrated into a relational policy-management system.

### Demonstration policies

The active policy set contains five requirements:

1. `POL-001` - Encryption at Rest
2. `POL-002` - Breach Notification
3. `POL-003` - Audit Rights
4. `POL-004` - Data Retention
5. `POL-005` - Subprocessor Notification

The project deliberately limits the number of policies so the entire workflow remains easy to test and explain.

## Finding Statuses

The structured finding model supports:

### `COMPLIANT`

Relevant contract evidence exists and satisfies the explicit policy requirement.

### `NON_COMPLIANT`

Relevant evidence exists, but the contractual commitment conflicts with or falls below the policy requirement.

### `AMBIGUOUS`

Potentially relevant language exists, but the wording is vague, incomplete, non-measurable, or open to interpretation.

### `MISSING`

No relevant contractual commitment was found. Missing evidence must not be presented as positive proof.

### `REVIEW_REQUIRED`

The system cannot safely produce another status because evidence is weak, conflicting, low-relevance, malformed, or otherwise uncertain.

## Synthetic Dataset

The active demonstration dataset is stored in:

```text
synthetic_data/
|-- synthetic_vendor_contract.pdf
|-- synthetic_vendor_contract.txt
`-- expected_findings.json
```

### Why synthetic data is required

Synthetic data is central to the project, not merely a convenience.

1. **Confidentiality:** Real vendor contracts may include commercial terms, customer information, infrastructure details, and legal obligations.
2. **Known ground truth:** The expected result for each policy is intentionally designed and recorded.
3. **Repeatability:** The same contract can be used for extraction, redaction, chunking, retrieval, and classification tests.
4. **Coverage:** One small agreement demonstrates compliant, non-compliant, ambiguous, missing, and conflicting scenarios.
5. **Safe PII testing:** Reserved and fictional values can be used to demonstrate redaction without exposing a real person.
6. **Debugging:** Expected pages and evidence make it easier to identify whether a failure occurs in extraction, redaction, chunking, retrieval, or generation.
7. **Responsible review:** The demonstration does not imply that a small prototype is ready to process real organizational contracts.

### Dataset design

The six-page synthetic agreement contains:

- Page 1: parties, services, confidentiality, and synthetic PII
- Page 2: security program, AES-256 encryption, TLS, access control, and vulnerability management
- Page 3: incident handling and a thirty-calendar-day notification commitment
- Page 4: data return, deletion, and an undefined “reasonable period” retention clause
- Page 5: prior subprocessor notice and an urgent no-prior-notice exception
- Page 6: availability, continuity, recovery objectives, termination, and general terms

Ground truth is stored separately in `expected_findings.json`. Expected labels are not embedded in the contract, preventing answer leakage into retrieval or model analysis.

### Synthetic PII values

The contract includes reserved demonstration values such as:

```text
Person: Alex Morgan
Email: alex.morgan@example.test
Phone: +1 202-555-0147
IP address: 192.0.2.25
```

These values are synthetic and exist only to test the redaction pipeline.

## Privacy and PII Redaction

Presidio analysis occurs before chunking, embedding, ChromaDB storage, retrieval, and LLM processing.

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
Typed replacement placeholders
```

Example:

```text
Before:
Contact Alex Morgan at alex.morgan@example.test.

After:
Contact <PERSON> at <EMAIL_ADDRESS>.
```

Typed placeholders preserve sentence structure and meaning better than deleting the values entirely.

### Allow-list approach

Only selected entity types are requested during the demonstration:

```text
PERSON
EMAIL_ADDRESS
PHONE_NUMBER
IP_ADDRESS
```

Enabling every available recognizer would add noise and complexity. A custom recognizer supports the reserved `.test` email suffix used by the synthetic dataset.

### Presidio limitation

Automated PII detection can produce false positives and false negatives. A production solution would require organization-specific recognizers, testing, privacy review, retention controls, and additional safeguards. Presidio is one layer in a privacy architecture, not a complete privacy guarantee.

## Embeddings and ChromaDB

### Embedding model

The project uses the local Ollama embedding model:

```text
granite-embedding:30m
```

Expected vector dimension:

```text
384
```

The same model must be used for document chunks and policy queries.

### Why ChromaDB

ChromaDB is used because the demonstration primarily needs local semantic retrieval over a small collection of sanitized contract chunks. It provides a compact interface for storing and querying:

- IDs;
- documents;
- embeddings; and
- metadata.

PostgreSQL with `pgvector` would be a reasonable production option when the system needs multi-user relational data, complex joins, transactional workflows, central administration, backup, and point-in-time recovery. For this small local project, PostgreSQL would add infrastructure without improving the core demonstration.

### ChromaDB record

A stored chunk is conceptually similar to:

```json
{
  "id": "synthetic_vendor_contract-chunk-006",
  "document": "The Vendor shall encrypt all Customer Data...",
  "embedding": "384-dimensional vector",
  "metadata": {
    "document_id": "synthetic_vendor_contract",
    "source": "synthetic_vendor_contract.pdf",
    "page_number": 2,
    "sanitized": true
  }
}
```

Only sanitized chunks are accepted by the vector-store service.

### Persistence

Runtime ChromaDB data is written to:

```text
data/chroma/
```

This directory is generated locally and excluded from Git.

## Structured Local LLM Analysis

The inference stage uses an approved local Ollama instruction model. A practical configuration may use:

```text
granite4.1:8b
```

A smaller fallback may be configured when system resources require it:

```text
granite4.1:3b
```

The exact approved model can be configured through environment variables.

### Model input

The model receives only:

- explicit policy data;
- sanitized retrieved evidence;
- page and chunk references;
- allowed status values; and
- strict instructions to return JSON.

Contract text is treated as untrusted evidence, not as application instructions. Text inside a contract must not override the system’s analysis rules.

### Structured finding

A finding is expected to contain fields such as:

```json
{
  "policy_id": "POL-002",
  "policy_version": "v1",
  "policy_requirement": "Vendor must notify within 72 hours.",
  "status": "NON_COMPLIANT",
  "severity": "HIGH",
  "confidence": 0.91,
  "explanation": "The contract allows a thirty-day notification period.",
  "retrieved_clause": "The Vendor shall notify the Customer...",
  "contract_page": 3,
  "chunk_id": "synthetic_vendor_contract-chunk-009",
  "retrieval_distance": 0.22,
  "recommended_remediation": "Require notification within 72 hours or less.",
  "requires_human_review": true,
  "embedding_model": "granite-embedding:30m",
  "inference_model": "configured local model",
  "prompt_version": "v1"
}
```

Values above are illustrative. Actual model output must be validated.

### Validation rules

- Only allowed statuses are accepted.
- Malformed JSON is rejected or returned as `REVIEW_REQUIRED` through controlled handling.
- A result cannot be marked compliant without supporting evidence.
- Missing evidence cannot be presented as proof.
- Conflicting evidence requires human review.
- Low-confidence or weakly retrieved evidence requires human review.
- Policy thresholds come from the policy file, not from model memory.

## Data Storage

The demonstration uses separate storage for separate responsibilities.

### Policy JSON

Stores explicit business requirements and policy versions:

```text
policies/sample_policies.json
```

### ChromaDB

Stores sanitized chunks, embeddings, and retrieval metadata:

```text
data/chroma/
```

### Expected-findings JSON

Stores synthetic ground truth for manual and automated verification:

```text
synthetic_data/expected_findings.json
```

### Optional audit-result JSON

If enabled, generated results may be saved locally under:

```text
data/audit/
```

This directory is excluded from Git. A production system might use PostgreSQL for audit runs, findings, policy versions, model versions, reviewer feedback, and workflow state.

## Repository Structure

```text
LTM_project_1/
|-- app/
|   |-- data/
|   |   `-- mock_findings.py
|   |-- models/
|   |   |-- chunk.py
|   |   |-- document.py
|   |   |-- finding.py
|   |   |-- policy.py
|   |   `-- retrieval.py
|   |-- services/
|   |   |-- auditor.py
|   |   |-- chunker.py
|   |   |-- document_extractor.py
|   |   |-- embedder.py
|   |   |-- pii_redactor.py
|   |   |-- policy_loader.py
|   |   |-- retriever.py
|   |   `-- vector_store.py
|   `-- ui/
|       `-- main.py
|-- data/
|   |-- audit/              # Generated locally, ignored by Git
|   |-- chroma/             # Generated locally, ignored by Git
|   |-- sanitized/          # Generated locally, ignored by Git
|   `-- uploads/            # Generated locally, ignored by Git
|-- policies/
|   `-- sample_policies.json
|-- prompts/
|   `-- compliance_audit_v1.txt
|-- synthetic_data/
|   |-- expected_findings.json
|   |-- synthetic_vendor_contract.pdf
|   `-- synthetic_vendor_contract.txt
|-- tests/
|   |-- test_auditor.py
|   |-- test_chunker.py
|   |-- test_document_extractor.py
|   |-- test_embedder.py
|   |-- test_pii_redactor.py
|   |-- test_policy_loader.py
|   |-- test_schema.py
|   `-- test_vector_store.py
|-- .env.example
|-- .gitattributes
|-- .gitignore
|-- README.md
`-- requirements.txt
```

Some final-stage files may be added as the local structured-audit integration is completed. Runtime folders and archived development copies are intentionally excluded from source control.

## Prerequisites

- Windows VM or compatible local environment
- CPython 3.12, 64-bit
- Git
- Visual Studio Code or another Python editor
- Ollama runtime
- Ollama embedding model `granite-embedding:30m`
- An approved Ollama instruction model
- spaCy model `en_core_web_lg`
- Approximately 16 GB RAM recommended for the larger local instruction model

## Installation

### 1. Clone the repository

```powershell
git clone https://github.com/dr0b1n/LTM_project_1.git
cd LTM_project_1
```

### 2. Create a virtual environment

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

### 4. Verify spaCy

```powershell
python -c "import spacy; spacy.load('en_core_web_lg'); print('spaCy model ready')"
```

If the model is unavailable and external downloads are approved:

```powershell
python -m spacy download en_core_web_lg
```

### 5. Verify Ollama

```powershell
ollama --version
ollama list
```

If downloads are approved and the embedding model is missing:

```powershell
ollama pull granite-embedding:30m
```

Pull the approved instruction model if required:

```powershell
ollama pull granite4.1:8b
```

A smaller approved option may be used on constrained systems:

```powershell
ollama pull granite4.1:3b
```

### Corporate certificate note

Corporate HTTPS inspection may cause certificate-verification errors during package or model downloads. Do not disable TLS verification and do not use `verify=False` as a workaround. Obtain the approved corporate root/intermediate CA bundle and configure the approved certificate and proxy environment variables.

## Configuration

Create a local `.env` from `.env.example`. Never commit `.env`.

Example configuration:

```dotenv
APP_ENV=development
LOG_LEVEL=INFO
UPLOAD_DIR=./data/uploads
SANITIZED_DIR=./data/sanitized
CHROMA_PATH=./data/chroma
AUDIT_OUTPUT_DIR=./data/audit
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=granite4.1:8b
EMBEDDING_MODEL=granite-embedding:30m
EMBEDDING_DIMENSION=384
SPACY_MODEL=en_core_web_lg
MAX_UPLOAD_MB=25
RETRIEVAL_TOP_K=3
LLM_TEMPERATURE=0
PROMPT_VERSION=v1
POLICY_VERSION=v1
```

Corporate certificate variables must be configured outside the repository:

```powershell
$env:SSL_CERT_FILE = "C:\CompanyCertificates\company-ca-bundle.pem"
$env:REQUESTS_CA_BUNDLE = "C:\CompanyCertificates\company-ca-bundle.pem"
```

Configure proxy variables only with approved values supplied by the organization.

## Running the Application

Activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Start Streamlit:

```powershell
python -m streamlit run app\ui\main.py
```

Open the local URL displayed by Streamlit, commonly:

```text
http://localhost:8501
```

## Demonstration Guide

Use the bundled synthetic PDF:

```text
synthetic_data/synthetic_vendor_contract.pdf
```

### Demonstration sequence

1. Start Ollama and Streamlit.
2. Upload the synthetic PDF.
3. Select **Extract PDF Text**.
4. Show the six-page count and page-level extracted text.
5. Select **Redact PII and Create Chunks**.
6. Show Page 1 before and after redaction.
7. Show detection counts and sanitized chunk metadata.
8. Select **Index Sanitized Chunks**.
9. Confirm that embeddings are 384-dimensional and chunks are stored.
10. Select each policy and retrieve the top three evidence chunks.
11. Show page numbers, chunk IDs, and vector distances.
12. Run the structured audit when the local auditor is enabled.
13. Show status, explanation, evidence, page, remediation, and human-review requirement.
14. State that the output is illustrative and requires qualified review.

### Suggested 5-to-7-minute narrative

- **Minute 1:** Explain the problem, local-first design, and synthetic dataset.
- **Minute 2:** Upload and extract the PDF with page metadata.
- **Minute 3:** Demonstrate Presidio redaction and explain the privacy boundary.
- **Minute 4:** Create sanitized chunks, embeddings, and the ChromaDB index.
- **Minute 5:** Retrieve evidence for two or three policies.
- **Minute 6:** Show structured findings and compare them with expected ground truth.
- **Minute 7:** Explain limitations, human review, and future production controls.

## Testing

Run all tests:

```powershell
python -m pytest -v
```

Run coverage if desired:

```powershell
python -m pytest --cov=app --cov-report=term-missing
```

Syntax-check the main UI:

```powershell
python -m py_compile app\ui\main.py
```

Verify dependency consistency:

```powershell
python -m pip check
```

Optional quality checks:

```powershell
ruff check .
mypy app
bandit -r app
pip-audit
```

The small demonstration prioritizes focused functional tests over extensive coverage.

### Tested behavior

Focused tests should verify:

- empty PDF rejection;
- invalid PDF rejection;
- textless PDF rejection;
- page-level extraction;
- expected PII replacement;
- empty redaction input;
- chunk splitting;
- page and source metadata preservation;
- policy JSON validation;
- 384-dimensional embedding validation;
- sanitized-only ChromaDB storage;
- finding-schema validation;
- malformed model-output handling; and
- evidence requirements for compliant findings.

## Expected Demonstration Outcomes

Ground truth is stored in:

```text
synthetic_data/expected_findings.json
```

Typical expected outcomes are:

### `POL-001` - Encryption at Rest

- Expected status: `COMPLIANT`
- Expected page: 2
- Reason: AES-256 or equivalent encryption is explicitly committed.

### `POL-002` - Breach Notification

- Expected status: `NON_COMPLIANT`
- Expected page: 3
- Reason: the contract allows thirty calendar days after investigation, while the policy requires notification within 72 hours.

### `POL-003` - Audit Rights

- Expected status: `MISSING`
- Expected page: none
- Reason: no operative audit or inspection right exists.

### `POL-004` - Data Retention

- Expected status: `AMBIGUOUS`
- Expected page: 4
- Reason: “reasonable period” is not a measurable retention period or objective deletion trigger.

### `POL-005` - Subprocessor Notification

- Expected status: `REVIEW_REQUIRED`
- Expected page: 5
- Reason: one clause promises advance notice, while another allows an urgent appointment without prior notice.

Retrieval order may vary slightly. The demonstration does not require the correct clause to rank first if the relevant evidence is present in the top three.

## Security Boundaries

### Enforced demonstration boundaries

- Use synthetic data only.
- Keep inference and embeddings local through Ollama.
- Redact selected PII before embeddings and model processing.
- Store only sanitized chunks in ChromaDB.
- Preserve evidence separately from generated explanation.
- Require a page or explicit missing-evidence state.
- Treat contract text as untrusted data.
- Keep material findings subject to human review.
- Keep credentials, certificates, model caches, vector data, uploaded files, and generated reports out of Git.

### Files that must not be committed

- Real vendor contracts
- Real PII
- `.env`
- Credentials or API keys
- Private keys and certificates
- `data/chroma/`
- Uploaded and sanitized runtime files
- Audit databases and generated reports
- Local Ollama model data
- Python virtual environments
- Archived development copies

Review staged files before every push:

```powershell
git --no-pager diff --cached --name-only
```

## Known Limitations

- Demonstration rather than production software
- Synthetic data only
- PDF input only
- Text-based PDFs only
- No OCR for scanned or image-only PDFs
- No complex table extraction
- Basic paragraph or fixed-size chunking
- Five sample policies
- One primary synthetic contract
- No retrieval reranker
- No formal confidence calibration
- No large RAG evaluation framework
- Local-model output may vary
- Presidio can miss sensitive information
- No authentication or authorization
- No multi-user isolation
- No malware scanning
- No secure production retention or deletion workflow
- No production database
- No high-availability or scaling design
- No production observability platform
- No formal legal, privacy, compliance, or security approval

## Troubleshooting

### `ModuleNotFoundError: No module named 'app'`

Run Streamlit from the repository root:

```powershell
python -m streamlit run app\ui\main.py
```

Confirm that `app/__init__.py` exists.

### spaCy model unavailable

```powershell
python -c "import spacy; spacy.load('en_core_web_lg'); print('ready')"
```

Install the model only through an approved route.

### Ollama is unreachable

```powershell
ollama --version
ollama list
Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags"
```

Restart Ollama or the development terminal if necessary.

### Embedding model missing

```powershell
ollama list
ollama pull granite-embedding:30m
```

The pull command requires approved network access.

### Wrong embedding dimension

```powershell
python -c "import ollama; r=ollama.embed(model='granite-embedding:30m', input=['test']); print(len(r['embeddings'][0]))"
```

Expected:

```text
384
```

Use the same embedding model for indexing and queries.

### ChromaDB contains stale data

The application replaces chunks for the same document ID when re-indexing. For a clean demonstration reset, stop the application and remove the generated local vector directory:

```powershell
Remove-Item data\chroma -Recurse -Force
```

Then restart the application and index the sanitized chunks again. Never run the command against a directory containing required data.

### Corporate certificate error

Do not disable SSL verification. Obtain the approved CA bundle, approved proxy configuration, or internally mirrored package/model artifact.

### Git opens a screen containing `(END)`

Git is using a pager. Press:

```text
q
```

To avoid the pager:

```powershell
git --no-pager diff --cached --stat
```

## Future Production Enhancements

The following are intentionally excluded from the small demonstration but would be relevant to a production design:

- Enterprise authentication, SSO, and role-based access control
- Multi-user and tenant isolation
- Malware scanning and upload quarantine
- File-signature and MIME validation
- OCR and more robust document-layout processing
- Organization-specific PII recognizers
- Secure original-document storage and retention
- PostgreSQL with `pgvector`
- Policy approval and version-lifecycle workflows
- Reviewer feedback and finding disposition
- Full audit history
- Prompt and model governance
- Model digest and artifact tracking
- Retrieval evaluation and regression datasets
- Prompt-injection testing
- Structured logging without raw PII
- Health checks and metrics
- Container deployment
- CI/CD quality and security gates
- Dependency, model, and container scanning
- Backup, restoration, deletion, and disaster-recovery procedures
- Formal legal, privacy, compliance, and security review

These items should be considered future work rather than additions to the demonstration unless explicitly required.

## Responsible Use

The application is a review aid. Users remain responsible for:

- verifying retrieved evidence;
- reading the surrounding contract context;
- resolving conflicting clauses;
- checking policy applicability and version;
- assessing legal meaning;
- approving remediation language; and
- making the final compliance decision.

A generated explanation must never replace the direct contract evidence. A missing retrieval result must never be treated as conclusive proof without human review.

## License and Distribution

This repository is an educational, synthetic, non-production demonstration. Review the licenses and organizational approvals for all Python packages, local models, and external runtimes before broader distribution or use.
