from datetime import datetime, timezone

from pydantic import BaseModel, Field

from app.models.finding import AuditFinding


class AuditFailure(BaseModel):
    policy_id: str
    policy_title: str
    error: str


class AuditRun(BaseModel):
    audit_run_id: str
    document_id: str
    source_filename: str
    started_at: datetime
    completed_at: datetime
    policy_set_id: str
    embedding_model: str
    inference_model: str
    prompt_version: str
    total_policies: int = Field(ge=0)
    findings: list[AuditFinding] = Field(default_factory=list)
    failures: list[AuditFailure] = Field(default_factory=list)

    @property
    def successful_findings(self) -> int:
        return len(self.findings)

    @property
    def failed_findings(self) -> int:
        return len(self.failures)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
