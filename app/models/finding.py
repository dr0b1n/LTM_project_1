from enum import Enum
from pydantic import BaseModel, Field, model_validator

class FindingStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    AMBIGUOUS = "AMBIGUOUS"
    MISSING = "MISSING"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"

class AuditFinding(BaseModel):
    policy_id: str
    policy_version: str
    policy_requirement: str
    status: FindingStatus
    severity: str
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str = Field(min_length=1)
    retrieved_clause: str | None = None
    contract_page: int | None = Field(default=None, ge=1)
    chunk_id: str | None = None
    retrieval_distance: float | None = None
    recommended_remediation: str = Field(min_length=1)
    requires_human_review: bool
    embedding_model: str
    inference_model: str
    prompt_version: str

    @model_validator(mode="after")
    def validate_evidence_rules(self):
        evidence_fields = (self.retrieved_clause, self.contract_page, self.chunk_id)
        if self.status == FindingStatus.COMPLIANT and not all(evidence_fields):
            raise ValueError("COMPLIANT findings require clause, page, and chunk evidence.")
        if self.status == FindingStatus.MISSING:
            self.retrieved_clause = None
            self.contract_page = None
            self.chunk_id = None
            self.retrieval_distance = None
            self.requires_human_review = True
        if self.status in {FindingStatus.AMBIGUOUS, FindingStatus.REVIEW_REQUIRED, FindingStatus.NON_COMPLIANT}:
            self.requires_human_review = True
        return self
