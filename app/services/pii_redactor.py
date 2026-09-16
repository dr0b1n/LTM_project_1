from dataclasses import dataclass
from functools import lru_cache

from presidio_analyzer import (
    AnalyzerEngine,
    Pattern,
    PatternRecognizer,
)
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from app.models.document import ExtractedDocument, ExtractedPage

ALLOWED_ENTITIES = (
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "IP_ADDRESS",
)


@dataclass(frozen=True)
class RedactionSummary:
    sanitized_document: ExtractedDocument
    counts: dict[str, int]

    @property
    def total_detections(self) -> int:
        return sum(self.counts.values())


@lru_cache(maxsize=1)
def get_analyzer() -> AnalyzerEngine:
    configuration = {
        "nlp_engine_name": "spacy",
        "models": [
            {
                "lang_code": "en",
                "model_name": "en_core_web_lg",
            }
        ],
    }

    provider = NlpEngineProvider(
        nlp_configuration=configuration
    )

    analyzer = AnalyzerEngine(
        nlp_engine=provider.create_engine(),
        supported_languages=["en"],
    )

    synthetic_email_pattern = Pattern(
        name="synthetic_test_email",
        regex=(
            r"\b[A-Za-z0-9._%+-]+@"
            r"[A-Za-z0-9.-]+\.test\b"
        ),
        score=0.9,
    )

    synthetic_email_recognizer = PatternRecognizer(
        supported_entity="EMAIL_ADDRESS",
        patterns=[synthetic_email_pattern],
        supported_language="en",
    )

    analyzer.registry.add_recognizer(
        synthetic_email_recognizer
    )

    return analyzer


@lru_cache(maxsize=1)
def get_anonymizer() -> AnonymizerEngine:
    return AnonymizerEngine()


def redact_text(text: str) -> tuple[str, dict[str, int]]:
    if not text.strip():
        return text, {entity: 0 for entity in ALLOWED_ENTITIES}

    results = [
        result
        for result in get_analyzer().analyze(
            text=text,
            language="en",
            entities=list(ALLOWED_ENTITIES),
        )
        if result.entity_type in ALLOWED_ENTITIES
    ]

    counts = {entity: 0 for entity in ALLOWED_ENTITIES}

    for result in results:
        counts[result.entity_type] += 1

    operators = {
        entity: OperatorConfig(
            "replace",
            {"new_value": f"<{entity}>"},
        )
        for entity in ALLOWED_ENTITIES
    }

    sanitized = get_anonymizer().anonymize(
        text=text,
        analyzer_results=results,
        operators=operators,
    ).text

    return sanitized, counts


def redact_document(document: ExtractedDocument) -> RedactionSummary:
    total_counts = {entity: 0 for entity in ALLOWED_ENTITIES}
    sanitized_pages: list[ExtractedPage] = []

    for page in document.pages:
        sanitized_text, page_counts = redact_text(page.text)
        sanitized_pages.append(
            ExtractedPage(
                page_number=page.page_number,
                text=sanitized_text,
            )
        )
        for entity, count in page_counts.items():
            total_counts[entity] += count

    return RedactionSummary(
        sanitized_document=ExtractedDocument(
            filename=document.filename,
            page_count=document.page_count,
            pages=sanitized_pages,
        ),
        counts=total_counts,
    )
