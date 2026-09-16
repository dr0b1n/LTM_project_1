from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.models.document import ExtractedDocument, ExtractedPage


class DocumentExtractionError(ValueError):
    """Raised when a PDF cannot be safely extracted for the demo."""


def extract_pdf(pdf_bytes: bytes, filename: str) -> ExtractedDocument:
    if not pdf_bytes:
        raise DocumentExtractionError("The uploaded PDF is empty.")

    try:
        reader = PdfReader(BytesIO(pdf_bytes))
    except (PdfReadError, OSError, ValueError) as exc:
        raise DocumentExtractionError(
            "The uploaded file could not be read as a PDF."
        ) from exc

    if reader.is_encrypted:
        raise DocumentExtractionError(
            "Encrypted PDFs are not supported in this demonstration."
        )

    if not reader.pages:
        raise DocumentExtractionError("The PDF contains no pages.")

    pages: list[ExtractedPage] = []

    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as exc:
            raise DocumentExtractionError(
                f"Text extraction failed on page {page_number}."
            ) from exc

        pages.append(
            ExtractedPage(
                page_number=page_number,
                text=text.strip(),
            )
        )

    if not any(page.text for page in pages):
        raise DocumentExtractionError(
            "No extractable text was found. Use a text-based PDF for this demo."
        )

    return ExtractedDocument(
        filename=filename,
        page_count=len(pages),
        pages=pages,
    )
