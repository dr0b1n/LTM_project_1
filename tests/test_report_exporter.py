import csv
import io
import json
from datetime import datetime, timezone
from app.models.audit_run import AuditRun
from app.models.finding import AuditFinding
from app.services.report_exporter import audit_run_to_csv, audit_run_to_json

def run():
    now=datetime.now(timezone.utc)
    finding=AuditFinding(policy_id="P1",policy_version="v1",policy_requirement="R",
        status="COMPLIANT",severity="HIGH",confidence=0.9,explanation="E",
        retrieved_clause="C",contract_page=2,chunk_id="c1",retrieval_distance=0.1,
        recommended_remediation="None",requires_human_review=False,embedding_model="e",
        inference_model="i",prompt_version="v1")
    return AuditRun(audit_run_id="A1",document_id="doc",source_filename="doc.pdf",
        started_at=now,completed_at=now,policy_set_id="set",embedding_model="e",
        inference_model="i",prompt_version="v1",total_policies=1,findings=[finding])

def test_json_export_is_parseable():
    payload=json.loads(audit_run_to_json(run()))
    assert payload["audit_run"]["document_id"] == "doc"

def test_csv_export_has_one_finding_row():
    rows=list(csv.DictReader(io.StringIO(audit_run_to_csv(run()))))
    assert len(rows) == 1
    assert rows[0]["policy_id"] == "P1"
