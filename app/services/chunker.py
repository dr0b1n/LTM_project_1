import re

from app.models.chunk import ContractChunk
from app.models.document import ExtractedDocument


def _split_paragraphs(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = re.split(r"\n\s*\n+", normalized)
    return [" ".join(part.split()) for part in paragraphs if part.strip()]

def _split_long_text(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]

    sentences = re.split(r"(?<=[.!?])\s+", text)
    pieces: list[str] = []
    current = ""

    for sentence in sentences:
        if len(sentence) > max_chars:
            if current:
                pieces.append(current)
                current = ""
            for start in range(0, len(sentence), max_chars):
                pieces.append(sentence[start:start + max_chars].strip())
            continue

        candidate = f"{current} {sentence}".strip()
        if current and len(candidate) > max_chars:
            pieces.append(current)
            current = sentence
        else:
            current = candidate

    if current:
        pieces.append(current)

    return [piece for piece in pieces if piece]


def chunk_document(
    document: ExtractedDocument,
    document_id: str,
    max_chars: int = 900,
) -> list[ContractChunk]:
    if max_chars < 200:
        raise ValueError("max_chars must be at least 200.")

    chunks: list[ContractChunk] = []
    chunk_number = 1

    for page in document.pages:
        paragraphs = _split_paragraphs(page.text)
        if not paragraphs and page.text.strip():
            paragraphs = [" ".join(page.text.split())]

        for paragraph in paragraphs:
            for piece in _split_long_text(paragraph, max_chars):
                chunks.append(
                    ContractChunk(
                        chunk_id=f"{document_id}-chunk-{chunk_number:03d}",
                        document_id=document_id,
                        source=document.filename,
                        page_number=page.page_number,
                        text=piece,
                        sanitized=True,
                    )
                )
                chunk_number += 1

    return chunks
