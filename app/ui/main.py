from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from app.data.mock_findings import MOCK_FINDINGS
from app.services.chunker import chunk_document
from app.services.document_extractor import (
    DocumentExtractionError,
    extract_pdf,
)
from app.services.embedder import EmbeddingError, embed_texts
from app.services.pii_redactor import redact_document
from app.services.policy_loader import load_policy_set
from app.services.retriever import retrieve_for_policy
from app.services.vector_store import get_collection, replace_document_chunks

POLICY_PATH = ROOT / "policies" / "sample_policies.json"
CHROMA_PATH = ROOT / "data" / "chroma"
TOP_K = 3

st.set_page_config(page_title="Vendor Compliance Auditor", layout="wide")


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
    st.session_state.audit_completed = False


initialize_state()

try:
    policy_set = load_policy_set(POLICY_PATH)
except (FileNotFoundError, ValueError) as exc:
    st.error(f"Policy configuration could not be loaded: {exc}")
    st.info("Expected file: policies/sample_policies.json")
    st.stop()

st.sidebar.title("Demo Information")
st.sidebar.info(
    "This review version uses a synthetic contract and deterministic "
    "audit findings. PDF extraction, PII redaction, chunking, embeddings, "
    "ChromaDB indexing, and policy retrieval are real. Local LLM "
    "classification will be connected in Session 6."
)

st.sidebar.subheader("Synthetic Dataset")
st.sidebar.write(
    "The bundled contract contains synthetic PII, a compliant encryption "
    "clause, a non-compliant notification clause, ambiguous retention "
    "wording, conflicting subprocessor clauses, and missing audit rights."
)

st.title("RAG-Powered Vendor Compliance Auditor")
st.markdown("**Demonstration Version**")
st.warning(
    "Illustrative demonstration only. Findings use synthetic data and are "
    "not legal or compliance advice."
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

    st.subheader("Extraction Preview")
    e1, e2, e3 = st.columns(3)
    e1.metric("Pages Extracted", document.page_count)
    e2.metric("Characters Extracted", f"{document.character_count:,}")
    e3.metric("Source File", document.filename)

    selected_page_number = st.selectbox(
        "Preview extracted page",
        options=[page.page_number for page in document.pages],
        format_func=lambda value: f"Page {value}",
    )
    selected_page = next(
        page for page in document.pages
        if page.page_number == selected_page_number
    )
    st.text_area(
        "Extracted text",
        value=selected_page.text or "No text extracted from this page.",
        height=260,
        disabled=True,
    )

    st.divider()
    st.subheader("Privacy Processing")

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
            "Only the sanitized text below may be embedded or stored in ChromaDB."
        )

        preview_page_number = st.selectbox(
            "Preview sanitized page",
            options=[
                page.page_number for page in summary.sanitized_document.pages
            ],
            format_func=lambda value: f"Page {value}",
            key="sanitized_page_selector",
        )
        sanitized_page = next(
            page for page in summary.sanitized_document.pages
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
                st.markdown(f"**{chunk.chunk_id} | Page {chunk.page_number}**")
                st.code(chunk.text)

if st.session_state.contract_chunks:
    st.divider()
    st.subheader("Vector Index and Policy Retrieval")
    st.caption(
        "Embeddings are generated locally with granite-embedding:30m. "
        "Only sanitized chunks are stored in ChromaDB."
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
            st.success(f"Indexed {stored} sanitized chunks.")
        except EmbeddingError as exc:
            st.error(str(exc))
        except Exception as exc:
            print(f"Vector indexing error: {exc}")
            st.error("Vector indexing could not be completed.")

    if st.session_state.indexed_chunk_count:
        v1, v2 = st.columns(2)
        v1.metric(
            "Indexed Sanitized Chunks",
            st.session_state.indexed_chunk_count,
        )
        v2.metric("Embedding Dimension", 384)

        selected_retrieval_policy = st.selectbox(
            "Select a policy retrieval query",
            policy_set.policies,
            format_func=lambda policy: f"{policy.policy_id}: {policy.title}",
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

st.divider()
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Sample Policies")
    for policy in policy_set.policies:
        with st.expander(f"{policy.policy_id}: {policy.title}"):
            st.write(policy.requirement)
            st.caption(
                f"Severity: {policy.severity} | "
                f"Version: {policy.policy_version}"
            )

with col2:
    st.subheader("Audit Findings")

    if st.button("Run Mock Audit"):
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

        st.subheader("Audit Findings Table")
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.subheader("Finding Summary")
        for finding in MOCK_FINDINGS:
            message = f"{finding['policy']} : {finding['status']}"
            if finding["status"] == "COMPLIANT":
                st.success(message)
            elif finding["status"] == "NON_COMPLIANT":
                st.error(message)
            elif finding["status"] in {"MISSING", "REVIEW_REQUIRED"}:
                st.warning(message)
            else:
                st.info(message)

        st.subheader("Evidence Details")
        selected_policy = st.selectbox(
            "Select Policy",
            [item["policy"] for item in MOCK_FINDINGS],
            key="mock_finding_policy_selector",
        )
        selected_finding = next(
            item for item in MOCK_FINDINGS
            if item["policy"] == selected_policy
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
            "PDF extraction, PII redaction, chunking, embeddings, and "
            "retrieval are real. Audit findings remain deterministic until "
            "local LLM classification is connected in Session 6."
        )
