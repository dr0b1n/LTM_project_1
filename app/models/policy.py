from pydantic import BaseModel, Field


class Policy(BaseModel):
    policy_id: str
    title: str
    category: str
    requirement: str = Field(min_length=1)
    severity: str
    expected_commitment: str
    remediation_guidance: str
    policy_version: str


class PolicySet(BaseModel):
    policy_set_id: str
    policies: list[Policy]
