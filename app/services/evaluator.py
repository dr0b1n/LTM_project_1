import json
from pathlib import Path

from app.models.audit_run import AuditRun
from app.models.evaluation import AuditEvaluation, PolicyEvaluation


def load_expected_findings(path: str | Path) -> dict:
    expected_path = Path(path)
    if not expected_path.exists():
        raise FileNotFoundError(f"Expected-findings file not found: {expected_path}")
    with expected_path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if "document_id" not in payload or "expected_findings" not in payload:
        raise ValueError("Expected-findings JSON has an invalid structure.")
    return payload


def evaluate_audit_run(audit_run: AuditRun, expected_payload: dict) -> AuditEvaluation:
    expected_document = str(expected_payload["document_id"])
    if expected_document != audit_run.document_id:
        raise ValueError(
            f"Expected findings are for {expected_document}, not {audit_run.document_id}."
        )

    finding_by_policy = {item.policy_id: item for item in audit_run.findings}
    results = []

    for expected in expected_payload["expected_findings"]:
        policy_id = str(expected["policy_id"])
        expected_status = str(expected["expected_status"])
        expected_pages = [int(page) for page in expected.get("expected_pages", [])]
        finding = finding_by_policy.get(policy_id)

        if finding is None:
            results.append(PolicyEvaluation(
                policy_id=policy_id,
                expected_status=expected_status,
                generated_status=None,
                status_match=False,
                expected_pages=expected_pages,
                generated_page=None,
                page_match=False,
                note="No successful generated finding.",
            ))
            continue

        generated_status = finding.status.value
        if expected_pages:
            page_match = finding.contract_page in expected_pages
        else:
            page_match = finding.contract_page is None

        results.append(PolicyEvaluation(
            policy_id=policy_id,
            expected_status=expected_status,
            generated_status=generated_status,
            status_match=(generated_status == expected_status),
            expected_pages=expected_pages,
            generated_page=finding.contract_page,
            page_match=page_match,
        ))

    count = len(results)
    status_matches = sum(item.status_match for item in results)
    page_matches = sum(item.page_match for item in results)
    return AuditEvaluation(
        document_id=audit_run.document_id,
        evaluated_policies=count,
        status_matches=status_matches,
        page_matches=page_matches,
        status_accuracy=(status_matches / count if count else 0.0),
        page_accuracy=(page_matches / count if count else 0.0),
        results=results,
    )
