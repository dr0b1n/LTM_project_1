from pydantic import BaseModel, Field


class PolicyEvaluation(BaseModel):
    policy_id: str
    expected_status: str
    generated_status: str | None
    status_match: bool
    expected_pages: list[int] = Field(default_factory=list)
    generated_page: int | None = None
    page_match: bool
    note: str | None = None


class AuditEvaluation(BaseModel):
    document_id: str
    evaluated_policies: int = Field(ge=0)
    status_matches: int = Field(ge=0)
    page_matches: int = Field(ge=0)
    status_accuracy: float = Field(ge=0.0, le=1.0)
    page_accuracy: float = Field(ge=0.0, le=1.0)
    results: list[PolicyEvaluation] = Field(default_factory=list)
