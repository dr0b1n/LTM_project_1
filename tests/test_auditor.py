import json
import pytest
from app.models.policy import Policy
from app.models.retrieval import RetrievedEvidence
from app.services import auditor

def policy():
    return Policy(policy_id="POL-001",title="Encryption",category="Security",requirement="Encrypt stored data with AES-256.",severity="HIGH",expected_commitment="AES-256",remediation_guidance="Add AES-256 wording.",policy_version="v1")

def evidence():
    return [RetrievedEvidence(policy_id="POL-001",chunk_id="c1",document_id="d1",source="contract.pdf",page_number=2,text="Stored data uses AES-256.",distance=0.1)]

def model_payload(chunk_id="c1"):
    return {"policy_id":"wrong","policy_version":"wrong","policy_requirement":"wrong","status":"COMPLIANT","severity":"LOW","confidence":0.9,"explanation":"The clause requires AES-256.","retrieved_clause":"model wording","contract_page":99,"chunk_id":chunk_id,"retrieval_distance":9.9,"recommended_remediation":"No change required.","requires_human_review":False,"embedding_model":"wrong","inference_model":"wrong","prompt_version":"wrong"}

def test_auditor_uses_authoritative_metadata(monkeypatch, tmp_path):
    prompt=tmp_path/"prompt.txt"; prompt.write_text("Return JSON.",encoding="utf-8")
    monkeypatch.setattr(auditor.ollama,"chat",lambda **kwargs:{"message":{"content":json.dumps(model_payload())}})
    result=auditor.audit_policy(policy(),evidence(),prompt,model="test-model")
    assert result.policy_id == "POL-001"
    assert result.contract_page == 2
    assert result.retrieved_clause == "Stored data uses AES-256."
    assert result.inference_model == "test-model"

def test_auditor_rejects_unknown_chunk(monkeypatch, tmp_path):
    prompt=tmp_path/"prompt.txt"; prompt.write_text("Return JSON.",encoding="utf-8")
    monkeypatch.setattr(auditor.ollama,"chat",lambda **kwargs:{"message":{"content":json.dumps(model_payload("invented"))}})
    with pytest.raises(
        auditor.AuditGenerationError,
        match="not included in the retrieved evidence",
    ):        
        auditor.audit_policy(policy(),evidence(),prompt)

def test_auditor_rejects_invalid_json(monkeypatch, tmp_path):
    prompt=tmp_path/"prompt.txt"; prompt.write_text("Return JSON.",encoding="utf-8")
    monkeypatch.setattr(auditor.ollama,"chat",lambda **kwargs:{"message":{"content":"not-json"}})
    with pytest.raises(auditor.AuditGenerationError, match="invalid structured"):
        auditor.audit_policy(policy(),evidence(),prompt)
