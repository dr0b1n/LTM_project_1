import json
import os
from pathlib import Path
from typing import Any

import ollama
from pydantic import BaseModel, Field, ValidationError

from app.models.finding import AuditFinding, FindingStatus
from app.models.policy import Policy
from app.models.retrieval import RetrievedEvidence
from app.services.embedder import EMBEDDING_MODEL


DEFAULT_INFERENCE_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "granite4.1:8b",
)
PROMPT_VERSION = "v1"


class AuditGenerationError(RuntimeError):
    """Raised when the local model cannot produce a valid finding."""


class ModelFindingDraft(BaseModel):
    """
    Fields that the local model is allowed to generate.

    Policy metadata, evidence text, page numbers, retrieval distance,
    and model provenance are supplied by the application.
    """

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
        return response.get("message", {}).get("content", "")

    message = getattr(response, "message", None)

    if message is None:
        return ""

    return getattr(message, "content", "") or ""


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
        print("Structured finding validation error:")
        print(exc)
        print("Raw local model response:")
        print(cleaned_content)

        raise AuditGenerationError(
            "The local model returned an invalid structured finding. "
            "Validation details were written to the Streamlit terminal."
        ) from exc


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

    if not prompt_file.exists():
        raise AuditGenerationError(
            f"Audit prompt file was not found: {prompt_file}"
        )

    prompt = prompt_file.read_text(encoding="utf-8")

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

    try:
        response = ollama.chat(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        user_payload,
                        indent=2,
                    ),
                },
            ],
            format=ModelFindingDraft.model_json_schema(),
            options={
                "temperature": 0,
            },
        )
    except Exception as exc:
        print(f"Ollama audit error: {exc}")

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

    evidence_by_id = {
        item.chunk_id: item
        for item in evidence
    }

    selected_evidence = None

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