import json

from app.services.policy_loader import load_policy_set


def test_policy_file_loads(tmp_path) -> None:
    path = tmp_path / "policies.json"
    path.write_text(
        json.dumps({
            "policy_set_id": "test-v1",
            "policies": [{
                "policy_id": "POL-001",
                "title": "Encryption",
                "category": "Security",
                "requirement": "Encrypt stored data.",
                "severity": "HIGH",
                "expected_commitment": "Explicit encryption.",
                "remediation_guidance": "Add encryption wording.",
                "policy_version": "v1"
            }]
        }),
        encoding="utf-8",
    )
    result = load_policy_set(path)
    assert result.policy_set_id == "test-v1"
    assert result.policies[0].policy_id == "POL-001"
