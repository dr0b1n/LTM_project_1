from pathlib import Path

from app.models.finding import AuditFinding
from app.models.policy import Policy, PolicySet
from app.services import audit_runner


def make_policy(policy_id: str) -> Policy:
    return Policy(
        policy_id=policy_id,
        title=policy_id,
        category="Security",
        requirement="Requirement",
        severity="HIGH",
        expected_commitment="Commitment",
        remediation_guidance="Remediate",
        policy_version="v1",
    )


def make_finding(policy_id: str) -> AuditFinding:
    return AuditFinding(
        policy_id=policy_id,
        policy_version="v1",
        policy_requirement="Requirement",
        status="COMPLIANT",
        severity="HIGH",
        confidence=0.9,
        explanation="Supported.",
        retrieved_clause="Evidence",
        contract_page=1,
        chunk_id="c1",
        retrieval_distance=0.1,
        recommended_remediation="None.",
        requires_human_review=False,
        embedding_model="embed",
        inference_model="llm",
        prompt_version="v1",
    )


def test_runner_converts_model_failure_to_review_fallback(
    monkeypatch,
    tmp_path: Path,
):
    policy_set = PolicySet(
        policy_set_id="set-v1",
        policies=[make_policy("P1"), make_policy("P2")],
    )
    evidence = type(
        "Evidence",
        (),
        {
            "text": "Retrieved clause",
            "page_number": 2,
            "chunk_id": "c1",
            "distance": 0.2,
        },
    )()
    monkeypatch.setattr(
        audit_runner,
        "retrieve_for_policy",
        lambda *args, **kwargs: [evidence],
    )

    def fake_audit(policy, *args, **kwargs):
        if policy.policy_id == "P1":
            raise RuntimeError("controlled model failure")
        return make_finding(policy.policy_id)

    monkeypatch.setattr(audit_runner, "audit_policy", fake_audit)
    result = audit_runner.run_complete_audit(
        object(),
        policy_set,
        "doc",
        "doc.pdf",
        tmp_path / "prompt.txt",
    )

    assert result.total_policies == 2
    assert result.successful_findings == 2
    assert result.failed_findings == 0
    fallback = next(item for item in result.findings if item.policy_id == "P1")
    assert fallback.status.value == "REVIEW_REQUIRED"
    assert fallback.requires_human_review is True
    assert fallback.chunk_id == "c1"
    assert fallback.contract_page == 2
    assert fallback.confidence == 0.0
