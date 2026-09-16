from app.models.document import ExtractedDocument, ExtractedPage
from app.services.chunker import chunk_document


def test_chunks_preserve_page_and_source_metadata() -> None:
    document = ExtractedDocument(
        filename="contract.pdf",
        page_count=2,
        pages=[
            ExtractedPage(page_number=1, text="First clause.\n\nSecond clause."),
            ExtractedPage(page_number=2, text="Third clause."),
        ],
    )

    chunks = chunk_document(document, document_id="contract-001")

    assert len(chunks) == 3
    assert [chunk.page_number for chunk in chunks] == [1, 1, 2]
    assert all(chunk.source == "contract.pdf" for chunk in chunks)
    assert all(chunk.sanitized is True for chunk in chunks)
    assert len({chunk.chunk_id for chunk in chunks}) == 3


def test_long_text_is_split() -> None:
    document = ExtractedDocument(
        filename="contract.pdf",
        page_count=1,
        pages=[ExtractedPage(page_number=1, text=("Contract sentence. " * 80))],
    )

    chunks = chunk_document(
        document, document_id="contract-001", max_chars=300
    )

    assert len(chunks) > 1
    assert all(len(chunk.text) <= 300 for chunk in chunks)
