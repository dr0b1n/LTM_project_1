from collections.abc import Callable
from pathlib import Path
from uuid import uuid4

from app.models.audit_run import AuditFailure, AuditRun, utc_now
from app.models.finding import AuditFinding, FindingStatus
from app.models.policy import Policy, PolicySet
from app.models.retrieval import RetrievedEvidence
from app.services.auditor import (
    DEFAULT_INFERENCE_MODEL,
    PROMPT_VERSION,
    audit_policy,
)
from app.services.embedder import EMBEDDING_MODEL
from app.services.retriever import retrieve_for_policy

ProgressCallback = Callable[[int, int, str], None]


def _fallback_finding(
    policy: Policy,
    evidence: list[RetrievedEvidence],
    model: str,
    error: Exception,
) -> AuditFinding:
    """Create a safe usable finding when a small model fails validation."""
    error_name = type(error).__name__

    if not evidence:
        return AuditFinding(
            policy_id=policy.policy_id,
            policy_version=policy.policy_version,
            policy_requirement=policy.requirement,
            status=FindingStatus.MISSING,
            severity=policy.severity,
            confidence=0.0,
            explanation=(
                "No retrieved contract evidence was available. The local "
                f"model result could not be validated ({error_name}), so "
                "this fallback requires human review."
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

    selected = evidence[0]
    return AuditFinding(
        policy_id=policy.policy_id,
        policy_version=policy.policy_version,
        policy_requirement=policy.requirement,
        status=FindingStatus.REVIEW_REQUIRED,
        severity=policy.severity,
        confidence=0.0,
        explanation=(
            "The local model response could not be validated "
            f"({error_name}). The highest-ranked retrieved clause is shown "
            "for human review; retrieval rank alone does not establish "
            "compliance."
        ),
        retrieved_clause=selected.text,
        contract_page=selected.page_number,
        chunk_id=selected.chunk_id,
        retrieval_distance=selected.distance,
        recommended_remediation=policy.remediation_guidance,
        requires_human_review=True,
        embedding_model=EMBEDDING_MODEL,
        inference_model=model,
        prompt_version=PROMPT_VERSION,
    )


def run_complete_audit(
    collection,
    policy_set: PolicySet,
    document_id: str,
    source_filename: str,
    prompt_path: str | Path,
    *,
    top_k: int = 3,
    model: str = DEFAULT_INFERENCE_MODEL,
    progress_callback: ProgressCallback | None = None,
) -> AuditRun:
    started_at = utc_now()
    findings: list[AuditFinding] = []
    failures: list[AuditFailure] = []
    total = len(policy_set.policies)

    for index, policy in enumerate(policy_set.policies, start=1):
        if progress_callback is not None:
            progress_callback(index - 1, total, policy.policy_id)

        evidence: list[RetrievedEvidence] = []
        try:
            evidence = retrieve_for_policy(
                collection,
                policy,
                document_id=document_id,
                top_k=top_k,
            )
            finding = audit_policy(
                policy,
                evidence,
                prompt_path,
                model=model,
            )
            findings.append(finding)
        except Exception as exc:
            # Keep the batch usable with smaller local models. A validation
            # failure becomes an explicit human-review fallback rather than
            # a lost policy result.
            try:
                findings.append(
                    _fallback_finding(policy, evidence, model, exc)
                )
            except Exception as fallback_exc:
                failures.append(
                    AuditFailure(
                        policy_id=policy.policy_id,
                        policy_title=policy.title,
                        error=(
                            f"{type(fallback_exc).__name__}: "
                            f"{fallback_exc}"
                        ),
                    )
                )

        if progress_callback is not None:
            progress_callback(index, total, policy.policy_id)

    return AuditRun(
        audit_run_id=f"AUD-{uuid4().hex[:12].upper()}",
        document_id=document_id,
        source_filename=source_filename,
        started_at=started_at,
        completed_at=utc_now(),
        policy_set_id=policy_set.policy_set_id,
        embedding_model=EMBEDDING_MODEL,
        inference_model=model,
        prompt_version=PROMPT_VERSION,
        total_policies=total,
        findings=findings,
        failures=failures,
    )
