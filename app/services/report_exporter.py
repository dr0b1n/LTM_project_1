import csv
import io
import json

from app.models.audit_run import AuditRun
from app.models.evaluation import AuditEvaluation


def audit_run_to_json(
    audit_run: AuditRun,
    evaluation: AuditEvaluation | None = None,
) -> str:
    payload = {
        "audit_run": audit_run.model_dump(mode="json"),
        "evaluation": (
            evaluation.model_dump(mode="json") if evaluation is not None else None
        ),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def audit_run_to_csv(audit_run: AuditRun) -> str:
    output = io.StringIO(newline="")
    fieldnames = [
        "policy_id",
        "policy_version",
        "status",
        "severity",
        "confidence",
        "contract_page",
        "chunk_id",
        "retrieval_distance",
        "explanation",
        "recommended_remediation",
        "requires_human_review",
        "embedding_model",
        "inference_model",
        "prompt_version",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for finding in audit_run.findings:
        writer.writerow({
            "policy_id": finding.policy_id,
            "policy_version": finding.policy_version,
            "status": finding.status.value,
            "severity": finding.severity,
            "confidence": finding.confidence,
            "contract_page": finding.contract_page,
            "chunk_id": finding.chunk_id,
            "retrieval_distance": finding.retrieval_distance,
            "explanation": finding.explanation,
            "recommended_remediation": finding.recommended_remediation,
            "requires_human_review": finding.requires_human_review,
            "embedding_model": finding.embedding_model,
            "inference_model": finding.inference_model,
            "prompt_version": finding.prompt_version,
        })
    return output.getvalue()
