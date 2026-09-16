from pydantic import BaseModel, Field


class ContractChunk(BaseModel):
    chunk_id: str
    document_id: str
    source: str
    page_number: int = Field(ge=1)
    text: str = Field(min_length=1)
    sanitized: bool = True
