"""Generate structured, evidence-grounded compliance findings with Ollama."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from app.models.finding import AuditFinding, FindingStatus
from app.models.policy import Policy
from app.models.retrieval import RetrievedEvidence
from app.services.embedder import EMBEDDING_MODEL
from app.services.ollama_client import get_ollama_client


DEFAULT_INFERENCE_MODEL = (
    os.getenv(
        "OLLAMA_MODEL",
        "granite4.1:8b",
    ).strip()
    or "granite4.1:8b"
)
PROMPT_VERSION = "v1"


class AuditGenerationError(RuntimeError):
    """Raised when the local model cannot produce a valid finding."""


class ModelFindingDraft(BaseModel):
    """Fields that the local model is allowed to generate."""

    status: FindingStatus
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str = Field(min_length=1)
    chunk_id: str | None = None
    recommended_remediation: str = Field(min_length=1)
    requires_human_review: bool


def _evidence_payload(
    evidence: list[RetrievedEvidence],
) -> list[dict[str, Any]]:
    return [
        {
            "rank": rank,
            "chunk_id": item.chunk_id,
            "page": item.page_number,
            "distance": item.distance,
            "text": item.text,
        }
        for rank, item in enumerate(evidence, start=1)
    ]


def _response_content(response: Any) -> str:
    if isinstance(response, dict):
        message = response.get("message", {})
        if isinstance(message, dict):
            content = message.get("content", "")
            return content if isinstance(content, str) else ""
        return ""

    message = getattr(response, "message", None)
    if message is None:
        return ""

    content = getattr(message, "content", "")
    return content if isinstance(content, str) else ""


def _parse_model_response(content: str) -> ModelFindingDraft:
    cleaned_content = content.strip()

    if cleaned_content.startswith("```"):
        cleaned_content = cleaned_content.removeprefix("```json")
        cleaned_content = cleaned_content.removeprefix("```")
        cleaned_content = cleaned_content.removesuffix("```")
        cleaned_content = cleaned_content.strip()

    try:
        return ModelFindingDraft.model_validate_json(cleaned_content)
    except ValidationError as exc:
        raise AuditGenerationError(
            "The local model returned an invalid structured finding."
        ) from exc


def _build_citation_correction(
    draft: ModelFindingDraft,
    evidence: list[RetrievedEvidence],
) -> str:
    available_chunk_ids = [item.chunk_id for item in evidence]

    return json.dumps(
        {
            "validation_error": (
                "A non-MISSING finding must cite exactly one retrieved "
                "evidence chunk."
            ),
            "previous_response": draft.model_dump(mode="json"),
            "available_chunk_ids": available_chunk_ids,
            "correction_rules": [
                (
                    "If status is COMPLIANT, NON_COMPLIANT, AMBIGUOUS, "
                    "or REVIEW_REQUIRED, copy exactly one chunk_id from "
                    "available_chunk_ids."
                ),
                (
                    "If none of the retrieved chunks supports a finding, "
                    "change status to MISSING and set chunk_id to null."
                ),
                "Return only the corrected JSON object.",
            ],
        },
        indent=2,
    )


def audit_policy(
    policy: Policy,
    evidence: list[RetrievedEvidence],
    prompt_path: str | Path,
    model: str = DEFAULT_INFERENCE_MODEL,
) -> AuditFinding:
    if not evidence:
        return AuditFinding(
            policy_id=policy.policy_id,
            policy_version=policy.policy_version,
            policy_requirement=policy.requirement,
            status=FindingStatus.MISSING,
            severity=policy.severity,
            confidence=1.0,
            explanation=(
                "No retrieved contract evidence was available for this "
                "policy requirement."
            ),
            retrieved_clause=None,
            contract_page=None,
            chunk_id=None,
            retrieval_distance=None,
            recommended_remediation=policy.remediation_guidance,
            requires_human_review=True,
            embedding_model=EMBEDDING_MODEL,
            inference_model=model,
            prompt_version=PROMPT_VERSION,
        )

    prompt_file = Path(prompt_path)
    if not prompt_file.is_file():
        raise AuditGenerationError(
            f"Audit prompt file was not found: {prompt_file}"
        )

    prompt = prompt_file.read_text(encoding="utf-8").strip()
    if not prompt:
        raise AuditGenerationError(
            f"Audit prompt file was empty: {prompt_file}"
        )

    user_payload = {
        "policy": {
            "policy_id": policy.policy_id,
            "title": policy.title,
            "category": policy.category,
            "requirement": policy.requirement,
            "severity": policy.severity,
            "expected_commitment": policy.expected_commitment,
            "remediation_guidance": policy.remediation_guidance,
            "policy_version": policy.policy_version,
        },
        "retrieved_evidence": _evidence_payload(evidence),
    }

    messages = [
        {
            "role": "system",
            "content": prompt,
        },
        {
            "role": "user",
            "content": json.dumps(
                user_payload,
                ensure_ascii=False,
            ),
        },
    ]

    try:
        client = get_ollama_client()
        response = client.chat(
            model=model,
            messages=messages,
            format=ModelFindingDraft.model_json_schema(),
            options={"temperature": 0},
        )
    except Exception as exc:
        raise AuditGenerationError(
            f"Ollama could not generate a finding with model '{model}'. "
            "Confirm that Ollama is running and the model is installed."
        ) from exc

    content = _response_content(response)
    if not content:
        raise AuditGenerationError(
            "Ollama returned an empty audit response."
        )

    draft = _parse_model_response(content)
    evidence_by_id = {item.chunk_id: item for item in evidence}
    selected_evidence: RetrievedEvidence | None = None

    if draft.status != FindingStatus.MISSING:
        if not draft.chunk_id:
            raise AuditGenerationError(
                "The finding did not cite a retrieved evidence chunk."
            )

        selected_evidence = evidence_by_id.get(draft.chunk_id)
        if selected_evidence is None:
            raise AuditGenerationError(
                "The finding cited a chunk that was not included in the "
                "retrieved evidence."
            )

    requires_human_review = draft.requires_human_review
    if draft.status in {
        FindingStatus.NON_COMPLIANT,
        FindingStatus.AMBIGUOUS,
        FindingStatus.MISSING,
        FindingStatus.REVIEW_REQUIRED,
    }:
        requires_human_review = True

    if draft.status == FindingStatus.MISSING:
        retrieved_clause = None
        contract_page = None
        chunk_id = None
        retrieval_distance = None
    else:
        if selected_evidence is None:
            raise AuditGenerationError(
                "A non-MISSING finding has no validated evidence."
            )
        retrieved_clause = selected_evidence.text
        contract_page = selected_evidence.page_number
        chunk_id = selected_evidence.chunk_id
        retrieval_distance = selected_evidence.distance

    return AuditFinding(
        policy_id=policy.policy_id,
        policy_version=policy.policy_version,
        policy_requirement=policy.requirement,
        status=draft.status,
        severity=policy.severity,
        confidence=draft.confidence,
        explanation=draft.explanation,
        retrieved_clause=retrieved_clause,
        contract_page=contract_page,
        chunk_id=chunk_id,
        retrieval_distance=retrieval_distance,
        recommended_remediation=draft.recommended_remediation,
        requires_human_review=requires_human_review,
        embedding_model=EMBEDDING_MODEL,
        inference_model=model,
        prompt_version=PROMPT_VERSION,
    )
