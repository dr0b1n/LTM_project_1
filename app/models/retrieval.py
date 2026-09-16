from pydantic import BaseModel, Field


class RetrievedEvidence(BaseModel):
    policy_id: str
    chunk_id: str
    document_id: str
    source: str
    page_number: int = Field(ge=1)
    text: str
    distance: float | None = None
