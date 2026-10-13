from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

st.markdown(
    """
    <style>
    .stTextArea textarea,
    .stTextInput input,
    .stNumberInput input {
        background-color: #F8ECEF !important;
        color: #1E293B !important;
        -webkit-text-fill-color: #1E293B !important;
        border: none !important;
        border-radius: 10px !important;
        box-shadow: none !important;
        opacity: 1 !important;
    }

    /* Keep the outer Streamlit containers consistent */
    .stTextArea [data-baseweb="base-input"],
    .stTextInput [data-baseweb="base-input"],
    .stNumberInput [data-baseweb="base-input"] {
        background-color: #F8ECEF !important;
        border: none !important;
        border-radius: 10px !important;
        box-shadow: none !important;
    }

    /* Placeholder text */
    .stTextArea textarea::placeholder,
    .stTextInput input::placeholder {
        color: #64748B !important;
        -webkit-text-fill-color: #64748B !important;
        opacity: 1 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

from app.data.mock_findings import MOCK_FINDINGS
from app.services.audit_runner import run_complete_audit
from app.services.auditor import AuditGenerationError, audit_policy
from app.services.chunker import chunk_document
from app.services.document_extractor import (
    DocumentExtractionError,
    extract_pdf,
)
from app.services.embedder import EmbeddingError, embed_texts
from app.services.evaluator import evaluate_audit_run, load_expected_findings
from app.services.pii_redactor import redact_document
from app.services.policy_loader import load_policy_set
from app.services.report_exporter import audit_run_to_csv, audit_run_to_json
from app.services.retriever import retrieve_for_policy
from app.services.vector_store import get_collection, replace_document_chunks

POLICY_PATH = ROOT / "policies" / "sample_policies.json"
CHROMA_PATH = ROOT / "data" / "chroma"
AUDIT_PROMPT_PATH = ROOT / "prompts" / "compliance_audit_v1.txt"
TOP_K = 3
EXPECTED_SUFFIX = "_expected_findings.json"

st.set_page_config(
    page_title="Vendor Compliance Auditor",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Presentation layer only. Workflow logic remains below.
st.markdown(
    """
    <style>
    :root {
        --ink: #2B2528;
        --muted: #6F6469;
        --plum: #5B2449;
        --plum-dark: #3F1934;
        --burgundy: #7A2948;
        --gold: #B58A3C;
        --gold-soft: #F4EBD8;
        --paper: #FFFDFC;
        --canvas: #F8F4F2;
        --line: #E6DCD8;
        --green: #2E6B57;
        --red: #A63D4C;
        --amber: #A86F18;
        --violet: #70507A;
    }

    .stApp {
        background:
            radial-gradient(circle at 96% 0%, rgba(181, 138, 60, 0.10), transparent 22rem),
            linear-gradient(180deg, #FFFDFC 0%, #F8F4F2 100%);
        color: var(--ink);
    }

    .block-container {
        max-width: 1380px;
        padding-top: 1.4rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3 {
        color: var(--plum-dark);
        letter-spacing: -0.025em;
    }

    h2 {
        margin-top: 1.25rem !important;
        padding-bottom: 0.35rem;
        border-bottom: 1px solid var(--line);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #4A1F3E 0%, #35162D 100%);
        border-right: 1px solid rgba(255,255,255,0.10);
    }

    [data-testid="stSidebar"] * {
        color: #FFF9F5;
    }

    [data-testid="stSidebar"] [data-testid="stAlert"] {
        background: rgba(255,255,255,0.09);
        border: 1px solid rgba(255,255,255,0.14);
    }

    .hero-shell {
        position: relative;
        overflow: hidden;
        padding: 2.1rem 2.2rem 1.85rem;
        margin: 0 0 1rem;
        border: 1px solid #DED0D0;
        border-radius: 22px;
        background: linear-gradient(125deg, #4B1F3E 0%, #6D294D 64%, #8A4A55 100%);
        box-shadow: 0 18px 45px rgba(74, 31, 62, 0.16);
    }

    .hero-shell::after {
        content: "";
        position: absolute;
        width: 17rem;
        height: 17rem;
        right: -5rem;
        top: -8rem;
        border-radius: 50%;
        border: 1px solid rgba(244, 235, 216, 0.34);
        box-shadow: 0 0 0 2.7rem rgba(244, 235, 216, 0.05),
                    0 0 0 5.4rem rgba(244, 235, 216, 0.04);
    }

    .hero-kicker {
        color: #E8D39B;
        font-size: 0.75rem;
        font-weight: 800;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        margin-bottom: 0.55rem;
    }

    .hero-title {
        position: relative;
        z-index: 2;
        color: #FFFFFF;
        font-size: clamp(2rem, 4vw, 3.45rem);
        font-weight: 760;
        line-height: 1.02;
        letter-spacing: -0.045em;
        margin: 0;
        max-width: 880px;
    }

    .hero-subtitle {
        position: relative;
        z-index: 2;
        color: #F4EDEF;
        font-size: 1.05rem;
        line-height: 1.65;
        max-width: 790px;
        margin: 0.85rem 0 1.1rem;
    }

    .hero-badges {
        position: relative;
        z-index: 2;
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem;
    }

    .hero-badge {
        padding: 0.38rem 0.72rem;
        border-radius: 999px;
        color: #FFFDFC;
        background: rgba(255,255,255,0.11);
        border: 1px solid rgba(255,255,255,0.20);
        font-size: 0.78rem;
        font-weight: 650;
    }

    .workflow-strip {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.7rem;
        margin: 1rem 0 1.35rem;
    }

    .workflow-step {
        min-height: 86px;
        padding: 0.85rem 0.95rem;
        border-radius: 14px;
        border: 1px solid var(--line);
        background: rgba(255,255,255,0.72);
        box-shadow: 0 7px 22px rgba(67, 35, 48, 0.05);
    }

    .workflow-step.complete {
        border-color: rgba(46,107,87,0.35);
        background: #F0F6F2;
    }

    .workflow-step.active {
        border-color: rgba(181,138,60,0.72);
        background: #FFF9EB;
        box-shadow: 0 7px 22px rgba(181,138,60,0.10);
    }

    .workflow-number {
        display: inline-grid;
        place-items: center;
        width: 1.55rem;
        height: 1.55rem;
        border-radius: 50%;
        margin-right: 0.35rem;
        background: var(--plum);
        color: white;
        font-size: 0.72rem;
        font-weight: 800;
    }

    .workflow-name {
        color: var(--plum-dark);
        font-size: 0.88rem;
        font-weight: 750;
    }

    .workflow-copy {
        margin-top: 0.38rem;
        color: var(--muted);
        font-size: 0.75rem;
        line-height: 1.35;
    }

    [data-testid="stMetric"] {
        background: rgba(255,255,255,0.82);
        border: 1px solid var(--line);
        border-top: 3px solid var(--gold);
        border-radius: 14px;
        padding: 0.85rem 1rem;
        box-shadow: 0 7px 22px rgba(67,35,48,0.055);
    }

    [data-testid="stMetricLabel"] {
        color: var(--muted);
        font-weight: 700;
    }

    [data-testid="stMetricValue"] {
        color: var(--plum-dark);
        font-weight: 780;
    }

    [data-testid="stFileUploader"] {
        padding: 0.8rem;
        border: 1px dashed #BEAAA9;
        border-radius: 16px;
        background: rgba(255,255,255,0.74);
    }

    [data-testid="stExpander"] {
        border: 1px solid var(--line);
        border-radius: 14px;
        background: rgba(255,255,255,0.74);
        box-shadow: 0 5px 18px rgba(67,35,48,0.04);
        overflow: hidden;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid var(--line);
        border-radius: 14px;
        overflow: hidden;
        box-shadow: 0 7px 24px rgba(67,35,48,0.05);
    }

    .stButton > button,
    .stDownloadButton > button {
        min-height: 2.75rem;
        border-radius: 10px;
        border: 1px solid #6C2B50;
        font-weight: 730;
        letter-spacing: 0.005em;
        transition: transform 120ms ease, box-shadow 120ms ease;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 18px rgba(91,36,73,0.14);
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(115deg, #5B2449, #7A2948);
        border-color: #5B2449;
        color: white;
    }

    [data-testid="stAlert"] {
        border-radius: 12px;
    }

    code, pre, [data-testid="stCodeBlock"] {
        border-radius: 12px !important;
    }

    .review-note {
        padding: 0.82rem 1rem;
        margin: 0.75rem 0 1.1rem;
        border-left: 4px solid var(--gold);
        border-radius: 0 12px 12px 0;
        background: var(--gold-soft);
        color: #4D3A25;
        font-size: 0.88rem;
        line-height: 1.5;
    }

    .sidebar-brand {
        margin: 0.25rem 0 1rem;
        padding: 0.2rem 0 0.8rem;
        border-bottom: 1px solid rgba(255,255,255,0.15);
    }

    .sidebar-brand-title {
        color: white;
        font-size: 1.15rem;
        font-weight: 780;
    }

    .sidebar-brand-copy {
        color: #E7D9E1;
        font-size: 0.78rem;
        margin-top: 0.28rem;
        line-height: 1.4;
    }

    @media (max-width: 900px) {
        .workflow-strip { grid-template-columns: 1fr 1fr; }
        .hero-shell { padding: 1.5rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_workflow_strip() -> None:
    extracted = st.session_state.extracted_document is not None
    sanitized = bool(st.session_state.contract_chunks)
    indexed = bool(st.session_state.indexed_chunk_count)
    audited = st.session_state.complete_audit_run is not None or bool(
        st.session_state.real_findings
    )
    complete = [extracted, sanitized, indexed, audited]
    labels = [
        ("Document", "Extract page-level contract text"),
        ("Privacy", "Redact selected PII and create chunks"),
        ("Evidence", "Index and retrieve sanitized clauses"),
        ("Audit", "Generate findings and export results"),
    ]
    if not extracted:
        active_index = 0
    elif not sanitized:
        active_index = 1
    elif not indexed:
        active_index = 2
    else:
        active_index = 3

    cards = []
    for index, ((name, copy), is_complete) in enumerate(zip(labels, complete)):
        state_class = "complete" if is_complete else "active" if index == active_index else ""
        cards.append(
            f'<div class="workflow-step {state_class}">'
            f'<span class="workflow-number">{index + 1}</span>'
            f'<span class="workflow-name">{name}</span>'
            f'<div class="workflow-copy">{copy}</div>'
            '</div>'
        )
    st.markdown(
        '<div class="workflow-strip">' + ''.join(cards) + '</div>',
        unsafe_allow_html=True,
    )


def initialize_state() -> None:
    defaults = {
        "audit_completed": False,
        "extracted_document": None,
        "uploaded_file_key": None,
        "redaction_summary": None,
        "contract_chunks": [],
        "retrieval_results": {},
        "indexed_chunk_count": 0,
        "indexed_document_id": None,
        "real_findings": {},
        "complete_audit_run": None,
        "audit_evaluation": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_downstream_state(*, clear_extraction: bool = False) -> None:
    if clear_extraction:
        st.session_state.extracted_document = None
    st.session_state.redaction_summary = None
    st.session_state.contract_chunks = []
    st.session_state.retrieval_results = {}
    st.session_state.indexed_chunk_count = 0
    st.session_state.indexed_document_id = None
    st.session_state.real_findings = {}
    st.session_state.complete_audit_run = None
    st.session_state.audit_evaluation = None
    st.session_state.audit_completed = False


initialize_state()

try:
    policy_set = load_policy_set(POLICY_PATH)
except (FileNotFoundError, ValueError) as exc:
    st.error(f"Policy configuration could not be loaded: {exc}")
    st.info("Expected file: policies/sample_policies.json")
    st.stop()

if not AUDIT_PROMPT_PATH.exists():
    st.error(
        "Audit prompt configuration could not be loaded. "
        "Expected file: prompts/compliance_audit_v1.txt"
    )
    st.stop()

st.sidebar.markdown(
    """
    <div class="sidebar-brand">
      <div class="sidebar-brand-title">Compliance Review</div>
      <div class="sidebar-brand-copy">Local evidence intelligence for synthetic vendor contracts</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.subheader("Processing boundary")
st.sidebar.info(
    "PDF extraction, selected PII redaction, local embeddings, ChromaDB "
    "retrieval, and structured local findings are connected."
)
st.sidebar.subheader("Synthetic dataset")
st.sidebar.write(
    "Three fictional vendor agreements and twelve policy controls cover "
    "compliant, non-compliant, ambiguous, missing, and review-required cases."
)
st.sidebar.caption(
    "Only sanitized chunks are embedded, indexed, retrieved, or sent to "
    "the local instruction model."
)

st.markdown(
    """
    <section class="hero-shell">
      <div class="hero-kicker">Third-party risk review</div>
      <div class="hero-title">Vendor Compliance Auditor</div>
      <div class="hero-subtitle">
        Privacy-preserving contract analysis with local RAG, traceable evidence,
        and structured findings designed for human review.
      </div>
      <div class="hero-badges">
        <span class="hero-badge">Local inference</span>
        <span class="hero-badge">Sanitized evidence</span>
        <span class="hero-badge">12 policy controls</span>
        <span class="hero-badge">Human-reviewed findings</span>
      </div>
    </section>
    """,
    unsafe_allow_html=True,
)
render_workflow_strip()
st.markdown(
    """
    <div class="review-note">
      <strong>Demonstration boundary:</strong> Generated findings may be
      inaccurate and are not legal or compliance advice. Material and uncertain
      results require qualified human review.
    </div>
    """,
    unsafe_allow_html=True,
)

uploaded_file = st.file_uploader("Upload Contract PDF", type=["pdf"])

if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    file_key = (uploaded_file.name, len(file_bytes))

    if file_key != st.session_state.uploaded_file_key:
        reset_downstream_state(clear_extraction=True)
        st.session_state.uploaded_file_key = file_key

    st.success(f"Selected file: {uploaded_file.name}")

    if st.button("Extract PDF Text", type="primary"):
        try:
            extracted_document = extract_pdf(file_bytes, uploaded_file.name)
            reset_downstream_state()
            st.session_state.extracted_document = extracted_document
        except DocumentExtractionError as exc:
            reset_downstream_state(clear_extraction=True)
            st.error(str(exc))

if st.session_state.extracted_document is not None:
    document = st.session_state.extracted_document

    st.subheader("Document Processing")
    e1, e2, e3 = st.columns(3)
    e1.metric("Pages Extracted", document.page_count)
    e2.metric("Characters Extracted", f"{document.character_count:,}")
    e3.metric("Source File", document.filename)

    selected_page_number = st.selectbox(
        "Preview extracted page",
        options=[page.page_number for page in document.pages],
        format_func=lambda value: f"Page {value}",
        key="extracted_page_selector",
    )
    selected_page = next(
        page
        for page in document.pages
        if page.page_number == selected_page_number
    )
    st.text_area(
        "Extracted text",
        value=selected_page.text or "No text extracted from this page.",
        height=260,
        disabled=True,
    )

    st.divider()
    st.subheader("Privacy Processing and Sanitization")

    if st.button("Redact PII and Create Chunks"):
        try:
            with st.spinner(
                "Detecting selected PII and creating sanitized chunks..."
            ):
                summary = redact_document(document)
                document_id = Path(document.filename).stem
                chunks = chunk_document(
                    summary.sanitized_document,
                    document_id=document_id,
                )

                st.session_state.redaction_summary = summary
                st.session_state.contract_chunks = chunks
                st.session_state.retrieval_results = {}
                st.session_state.indexed_chunk_count = 0
                st.session_state.indexed_document_id = None
                st.session_state.real_findings = {}
                st.session_state.complete_audit_run = None
                st.session_state.audit_evaluation = None
                st.session_state.audit_completed = False
        except Exception as exc:
            reset_downstream_state()
            print(f"Privacy processing error: {exc}")
            st.error(
                "Privacy processing could not be completed. Confirm that "
                "Presidio and the en_core_web_lg spaCy model are available."
            )

    if st.session_state.redaction_summary is not None:
        summary = st.session_state.redaction_summary
        chunks = st.session_state.contract_chunks

        r1, r2, r3 = st.columns(3)
        r1.metric("PII Detections", summary.total_detections)
        r2.metric("Sanitized Pages", summary.sanitized_document.page_count)
        r3.metric("Chunks Created", len(chunks))

        st.caption(
            "Only the sanitized text below may be embedded, stored, "
            "retrieved, or sent to the local instruction model."
        )

        preview_page_number = st.selectbox(
            "Preview sanitized page",
            options=[
                page.page_number
                for page in summary.sanitized_document.pages
            ],
            format_func=lambda value: f"Page {value}",
            key="sanitized_page_selector",
        )
        sanitized_page = next(
            page
            for page in summary.sanitized_document.pages
            if page.page_number == preview_page_number
        )
        st.text_area(
            "Sanitized text",
            value=sanitized_page.text,
            height=260,
            disabled=True,
        )

        with st.expander("PII detection counts"):
            st.json(summary.counts)

        with st.expander("Sanitized chunk preview"):
            for chunk in chunks:
                st.markdown(
                    f"**{chunk.chunk_id} | Page {chunk.page_number}**"
                )
                st.code(chunk.text)

if st.session_state.contract_chunks:
    st.divider()
    st.subheader("Evidence Index")
    st.caption(
        "Embeddings are generated locally with granite-embedding:30m. "
        "Only sanitized chunks are stored in ChromaDB or analyzed locally."
    )

    if st.button("Index Sanitized Chunks"):
        try:
            with st.spinner(
                "Generating local embeddings and updating ChromaDB..."
            ):
                chunks = st.session_state.contract_chunks
                vectors = embed_texts([chunk.text for chunk in chunks])
                collection = get_collection(CHROMA_PATH)
                stored = replace_document_chunks(collection, chunks, vectors)

                st.session_state.indexed_chunk_count = stored
                st.session_state.indexed_document_id = chunks[0].document_id
                st.session_state.retrieval_results = {}
                st.session_state.real_findings = {}
                st.session_state.complete_audit_run = None
                st.session_state.audit_evaluation = None
            st.success(f"Indexed {stored} sanitized chunks.")
        except EmbeddingError as exc:
            st.session_state.indexed_chunk_count = 0
            st.session_state.indexed_document_id = None
            st.session_state.retrieval_results = {}
            st.session_state.real_findings = {}
            st.session_state.complete_audit_run = None
            st.session_state.audit_evaluation = None
            st.error(str(exc))
        except Exception as exc:
            st.session_state.indexed_chunk_count = 0
            st.session_state.indexed_document_id = None
            st.session_state.retrieval_results = {}
            st.session_state.real_findings = {}
            st.session_state.complete_audit_run = None
            st.session_state.audit_evaluation = None
            print(f"Vector indexing error: {exc}")
            st.error("Vector indexing could not be completed.")

    if st.session_state.indexed_chunk_count:
        v1, v2 = st.columns(2)
        v1.metric(
            "Indexed Sanitized Chunks",
            st.session_state.indexed_chunk_count,
        )
        v2.metric("Embedding Dimension", 384)

        st.subheader("Policy → Evidence → Finding")
        st.caption(
            "Select one policy, inspect its top three retrieved chunks, "
            "and generate a structured finding before running the full "
            "contract audit below."
        )

        selected_retrieval_policy = st.selectbox(
            "Select a policy",
            policy_set.policies,
            format_func=lambda policy: (
                f"{policy.policy_id}: {policy.title}"
            ),
            key="retrieval_policy_selector",
        )

        if st.button("Retrieve Top 3 Evidence Chunks"):
            try:
                collection = get_collection(CHROMA_PATH)
                results = retrieve_for_policy(
                    collection,
                    selected_retrieval_policy,
                    document_id=st.session_state.indexed_document_id,
                    top_k=TOP_K,
                )
                st.session_state.retrieval_results[
                    selected_retrieval_policy.policy_id
                ] = results
                st.session_state.real_findings.pop(
                    selected_retrieval_policy.policy_id,
                    None,
                )
            except EmbeddingError as exc:
                st.error(str(exc))
            except Exception as exc:
                print(f"Retrieval error: {exc}")
                st.error("Evidence retrieval could not be completed.")

        current_results = st.session_state.retrieval_results.get(
            selected_retrieval_policy.policy_id,
            [],
        )

        if current_results:
            st.caption(
                "Vector distance is shown for demonstration purposes. "
                "Lower values indicate closer vectors, but retrieval rank "
                "does not prove compliance."
            )

        for rank, evidence in enumerate(current_results, start=1):
            with st.expander(
                f"Result {rank}: Page {evidence.page_number} | "
                f"{evidence.chunk_id}",
                expanded=(rank == 1),
            ):
                st.write(evidence.text)
                if evidence.distance is not None:
                    st.caption(
                        f"Vector distance: {evidence.distance:.4f} "
                        "(lower is closer)"
                    )

        if current_results:
            st.subheader("Local Structured Finding")

            if st.button("Generate Structured Finding"):
                try:
                    with st.spinner(
                        "Comparing the policy with retrieved evidence "
                        "using the local instruction model..."
                    ):
                        finding = audit_policy(
                            selected_retrieval_policy,
                            current_results,
                            AUDIT_PROMPT_PATH,
                        )
                        st.session_state.real_findings[
                            selected_retrieval_policy.policy_id
                        ] = finding
                except AuditGenerationError as exc:
                    st.session_state.real_findings.pop(
                        selected_retrieval_policy.policy_id,
                        None,
                    )
                    st.error(str(exc))

            current_finding = st.session_state.real_findings.get(
                selected_retrieval_policy.policy_id
            )

            if current_finding is not None:
                f1, f2, f3 = st.columns(3)
                f1.metric("Status", current_finding.status.value)
                f2.metric("Severity", current_finding.severity)
                f3.metric(
                    "Confidence",
                    f"{current_finding.confidence:.2f}",
                )

                st.write("### Explanation")
                st.write(current_finding.explanation)

                st.write("### Evidence")
                st.code(
                    current_finding.retrieved_clause
                    or "No supporting clause found."
                )

                d1, d2 = st.columns(2)
                d1.write(
                    "**Contract Page:** "
                    f"{current_finding.contract_page or 'No evidence page'}"
                )
                d2.write(
                    "**Chunk ID:** "
                    f"{current_finding.chunk_id or 'No evidence chunk'}"
                )

                if current_finding.retrieval_distance is not None:
                    st.caption(
                        "Authoritative retrieval distance: "
                        f"{current_finding.retrieval_distance:.4f}"
                    )

                st.write("### Recommendation")
                st.write(current_finding.recommended_remediation)

                if current_finding.requires_human_review:
                    st.warning("Human review is required for this finding.")
                else:
                    st.info(
                        "Automated result available. Human verification is "
                        "still recommended for this demonstration."
                    )

                with st.expander("Finding provenance"):
                    st.json(
                        {
                            "policy_id": current_finding.policy_id,
                            "policy_version": current_finding.policy_version,
                            "embedding_model": (
                                current_finding.embedding_model
                            ),
                            "inference_model": (
                                current_finding.inference_model
                            ),
                            "prompt_version": current_finding.prompt_version,
                        }
                    )

        st.divider()
        st.subheader("Complete Contract Audit and Export")
        st.caption(
            "Run retrieval and structured local analysis for every policy. "
            "Each policy is isolated so one failure does not discard the "
            "other findings."
        )

        if st.button("Run Complete Local Audit", type="primary"):
            progress = st.progress(0.0, text="Preparing complete audit...")

            def update_progress(
                done: int,
                total: int,
                policy_id: str,
            ) -> None:
                ratio = done / total if total else 1.0
                progress.progress(
                    min(max(ratio, 0.0), 1.0),
                    text=(
                        f"Processed {done} of {total} policies | "
                        f"{policy_id}"
                    ),
                )

            try:
                collection = get_collection(CHROMA_PATH)
                audit_run = run_complete_audit(
                    collection,
                    policy_set,
                    document_id=st.session_state.indexed_document_id,
                    source_filename=(
                        st.session_state.extracted_document.filename
                    ),
                    prompt_path=AUDIT_PROMPT_PATH,
                    top_k=TOP_K,
                    progress_callback=update_progress,
                )
                st.session_state.complete_audit_run = audit_run
                st.session_state.audit_evaluation = None

                expected_path = (
                    ROOT
                    / "synthetic_data"
                    / f"{audit_run.document_id}{EXPECTED_SUFFIX}"
                )
                try:
                    expected = load_expected_findings(expected_path)
                    st.session_state.audit_evaluation = evaluate_audit_run(
                        audit_run,
                        expected,
                    )
                except FileNotFoundError:
                    st.info(
                        "No matching synthetic expected-findings file was "
                        "found. The audit completed without evaluation."
                    )
                except ValueError as exc:
                    st.warning(f"Evaluation could not be completed: {exc}")

                progress.progress(1.0, text="Complete audit finished.")
            except Exception as exc:
                st.session_state.complete_audit_run = None
                st.session_state.audit_evaluation = None
                print(f"Complete audit error: {exc}")
                st.error(
                    "The complete audit could not be completed. Confirm "
                    "that Ollama is running and the configured model is "
                    "installed."
                )

        audit_run = st.session_state.complete_audit_run
        if audit_run is not None:
            st.subheader("Executive Audit Summary")
            status_counts = {}
            for item in audit_run.findings:
                status = item.status.value
                status_counts[status] = status_counts.get(status, 0) + 1

            a1, a2, a3, a4 = st.columns(4)
            a1.metric("Policies Attempted", audit_run.total_policies)
            a2.metric("Completed", audit_run.successful_findings)
            a3.metric("Failures", audit_run.failed_findings)
            a4.metric(
                "Human Review",
                sum(
                    item.requires_human_review
                    for item in audit_run.findings
                ),
            )

            status_columns = st.columns(5)
            for column, status in zip(
                status_columns,
                [
                    "COMPLIANT",
                    "NON_COMPLIANT",
                    "AMBIGUOUS",
                    "MISSING",
                    "REVIEW_REQUIRED",
                ],
            ):
                column.metric(
                    status.replace("_", " ").title(),
                    status_counts.get(status, 0),
                )

            findings_df = pd.DataFrame(
                [
                    {
                        "Policy ID": item.policy_id,
                        "Status": item.status.value,
                        "Severity": item.severity,
                        "Confidence": item.confidence,
                        "Page": item.contract_page,
                        "Chunk ID": item.chunk_id,
                        "Human Review": item.requires_human_review,
                    }
                    for item in audit_run.findings
                ]
            )
            if not findings_df.empty:
                st.dataframe(
                    findings_df,
                    use_container_width=True,
                    hide_index=True,
                )

                finding_ids = [
                    item.policy_id for item in audit_run.findings
                ]
                selected_batch_policy = st.selectbox(
                    "Inspect a complete-audit finding",
                    finding_ids,
                    key="complete_audit_finding_selector",
                )
                batch_finding = next(
                    item
                    for item in audit_run.findings
                    if item.policy_id == selected_batch_policy
                )
                with st.expander(
                    f"{batch_finding.policy_id} finding details",
                    expanded=False,
                ):
                    st.write(f"**Status:** {batch_finding.status.value}")
                    st.write(f"**Severity:** {batch_finding.severity}")
                    st.write(
                        f"**Confidence:** {batch_finding.confidence:.2f}"
                    )
                    st.write("**Explanation**")
                    st.write(batch_finding.explanation)
                    st.write("**Evidence**")
                    st.code(
                        batch_finding.retrieved_clause
                        or "No supporting clause found."
                    )
                    st.write(
                        "**Contract Page:** "
                        f"{batch_finding.contract_page or 'No evidence page'}"
                    )
                    st.write(
                        "**Chunk ID:** "
                        f"{batch_finding.chunk_id or 'No evidence chunk'}"
                    )
                    st.write("**Recommendation**")
                    st.write(batch_finding.recommended_remediation)

            if audit_run.failures:
                with st.expander("Policy processing failures"):
                    for failure in audit_run.failures:
                        st.warning(
                            f"{failure.policy_id} - "
                            f"{failure.policy_title}: {failure.error}"
                        )

            evaluation = st.session_state.audit_evaluation
            if evaluation is not None:
                st.subheader("Synthetic Evaluation")
                st.caption(
                    "Expected findings are loaded only after generation. "
                    "They are not sent to retrieval or the language model. "
                    "These metrics describe this synthetic demonstration, "
                    "not production accuracy."
                )
                e1, e2, e3 = st.columns(3)
                e1.metric(
                    "Evaluated Policies",
                    evaluation.evaluated_policies,
                )
                e2.metric(
                    "Status Match",
                    f"{evaluation.status_accuracy:.0%}",
                )
                e3.metric(
                    "Page Match",
                    f"{evaluation.page_accuracy:.0%}",
                )
                evaluation_df = pd.DataFrame(
                    [item.model_dump() for item in evaluation.results]
                )
                st.dataframe(
                    evaluation_df,
                    use_container_width=True,
                    hide_index=True,
                )

            report_json = audit_run_to_json(audit_run, evaluation)
            report_csv = audit_run_to_csv(audit_run)
            d1, d2 = st.columns(2)
            d1.download_button(
                "Download Audit JSON",
                data=report_json,
                file_name=f"{audit_run.audit_run_id}.json",
                mime="application/json",
            )
            d2.download_button(
                "Download Findings CSV",
                data=report_csv,
                file_name=f"{audit_run.audit_run_id}.csv",
                mime="text/csv",
            )

st.divider()
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Policy Library")
    for policy in policy_set.policies:
        with st.expander(f"{policy.policy_id}: {policy.title}"):
            st.write(policy.requirement)
            st.caption(
                f"Severity: {policy.severity} | "
                f"Version: {policy.policy_version}"
            )

with col2:
    st.subheader("Demonstration Fallback")
    st.caption(
        "This section is retained only as a fallback for demonstrations. "
        "It is separate from the real local retrieval and LLM workflow above."
    )

    if st.button("Run Deterministic Fallback Audit"):
        st.session_state.audit_completed = True

    if st.session_state.audit_completed:
        df = pd.DataFrame(MOCK_FINDINGS)
        total = len(df)
        compliant = len(df[df["status"] == "COMPLIANT"])
        issues = len(
            df[df["status"].isin(["NON_COMPLIANT", "MISSING"])]
        )
        review = len(
            df[df["status"].isin(["AMBIGUOUS", "REVIEW_REQUIRED"])]
        )

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Policies Checked", total)
        m2.metric("Compliant", compliant)
        m3.metric("Issues", issues)
        m4.metric("Review Needed", review)

        st.subheader("Fallback Findings Table")
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.subheader("Fallback Finding Summary")
        for fallback_finding in MOCK_FINDINGS:
            message = (
                f"{fallback_finding['policy']} : "
                f"{fallback_finding['status']}"
            )
            if fallback_finding["status"] == "COMPLIANT":
                st.success(message)
            elif fallback_finding["status"] == "NON_COMPLIANT":
                st.error(message)
            elif fallback_finding["status"] in {
                "MISSING",
                "REVIEW_REQUIRED",
            }:
                st.warning(message)
            else:
                st.info(message)

        st.subheader("Fallback Evidence Details")
        selected_fallback_policy = st.selectbox(
            "Select fallback policy",
            [item["policy"] for item in MOCK_FINDINGS],
            key="mock_finding_policy_selector",
        )
        selected_finding = next(
            item
            for item in MOCK_FINDINGS
            if item["policy"] == selected_fallback_policy
        )

        st.write("### Evidence")
        st.code(selected_finding["evidence"])
        st.write("### Explanation")
        st.write(selected_finding["explanation"])
        st.write("### Recommendation")
        st.write(selected_finding["recommendation"])

        page = selected_finding["page"]
        page_display = page if page is not None else "No evidence page"
        st.write(f"**Contract Page:** {page_display}")
        st.caption(
            "These fallback findings are deterministic and do not use the "
            "retrieved evidence or local instruction model."
        )
