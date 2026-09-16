from io import BytesIO

import pytest
from pypdf import PdfWriter

from app.services.document_extractor import (
    DocumentExtractionError,
    extract_pdf,
)


def test_empty_upload_is_rejected() -> None:
    with pytest.raises(DocumentExtractionError, match="empty"):
        extract_pdf(b"", "empty.pdf")


def test_invalid_pdf_is_rejected() -> None:
    with pytest.raises(DocumentExtractionError, match="could not be read"):
        extract_pdf(b"not a pdf", "invalid.pdf")


def test_textless_pdf_is_rejected() -> None:
    output = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.write(output)

    with pytest.raises(DocumentExtractionError, match="No extractable text"):
        extract_pdf(output.getvalue(), "blank.pdf")
