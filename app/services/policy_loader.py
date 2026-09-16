import json
from pathlib import Path

from app.models.policy import PolicySet


def load_policy_set(path: str | Path) -> PolicySet:
    policy_path = Path(path)
    if not policy_path.exists():
        raise FileNotFoundError(f"Policy file not found: {policy_path}")

    with policy_path.open(encoding="utf-8") as file:
        payload = json.load(file)

    policy_set = PolicySet.model_validate(payload)
    if not policy_set.policies:
        raise ValueError("The policy file contains no policies.")
    return policy_set
