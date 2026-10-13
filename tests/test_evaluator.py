from datetime import datetime, timezone

from app.models.audit_run import AuditRun
from app.models.finding import AuditFinding
from app.services.evaluator import evaluate_audit_run


def finding(policy_id, status, page):
    kwargs = dict(policy_id=policy_id, policy_version="v1", policy_requirement="R",
        status=status, severity="HIGH", confidence=0.8, explanation="E",
        recommended_remediation="R", requires_human_review=status != "COMPLIANT",
        embedding_model="e", inference_model="i", prompt_version="v1")
    if status == "MISSING":
        return AuditFinding(**kwargs)
    return AuditFinding(**kwargs, retrieved_clause="clause", contract_page=page, chunk_id="c1", retrieval_distance=0.1)


def test_evaluation_counts_status_and_page_matches():
    now=datetime.now(timezone.utc)
    run=AuditRun(audit_run_id="A1", document_id="doc", source_filename="doc.pdf",
        started_at=now, completed_at=now, policy_set_id="set", embedding_model="e",
        inference_model="i", prompt_version="v1", total_policies=2,
        findings=[finding("P1","COMPLIANT",2), finding("P2","MISSING",None)])
    expected={"document_id":"doc","expected_findings":[
        {"policy_id":"P1","expected_status":"COMPLIANT","expected_pages":[2]},
        {"policy_id":"P2","expected_status":"MISSING","expected_pages":[]}]}
    result=evaluate_audit_run(run,expected)
    assert result.status_accuracy == 1.0
    assert result.page_accuracy == 1.0
