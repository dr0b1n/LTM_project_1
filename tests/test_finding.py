import pytest
from pydantic import ValidationError
from app.models.finding import AuditFinding, FindingStatus

def payload():
    return {"policy_id":"P1","policy_version":"v1","policy_requirement":"Encrypt data","status":"COMPLIANT","severity":"HIGH","confidence":0.9,"explanation":"Evidence matches.","retrieved_clause":"Encrypt data with AES-256.","contract_page":2,"chunk_id":"c1","retrieval_distance":0.2,"recommended_remediation":"No change.","requires_human_review":False,"embedding_model":"embed","inference_model":"llm","prompt_version":"v1"}

def test_compliant_requires_evidence():
    data=payload(); data["retrieved_clause"]=None
    with pytest.raises(ValidationError): AuditFinding.model_validate(data)

def test_missing_clears_evidence_and_requires_review():
    data=payload(); data["status"]="MISSING"
    finding=AuditFinding.model_validate(data)
    assert finding.status == FindingStatus.MISSING
    assert finding.contract_page is None
    assert finding.requires_human_review is True
