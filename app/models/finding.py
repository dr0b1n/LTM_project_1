from pydantic import BaseModel

class Finding(BaseModel):
    policy: str
    status: str
    severity: str
    evidence: str
    page: int
    explanation: str
    recommendation: str