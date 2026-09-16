from pathlib import Path
from collections.abc import Sequence

import chromadb

from app.models.chunk import ContractChunk

COLLECTION_NAME = "vendor_contract_chunks_v1"


def get_collection(
    path: str | Path = "./data/chroma",
    collection_name: str = COLLECTION_NAME,
):
    client = chromadb.PersistentClient(path=str(path))
    return client.get_or_create_collection(
        name=collection_name,
        metadata={
            "description": "Sanitized vendor-contract chunks",
            "embedding_model": "granite-embedding:30m",
            "embedding_dimension": 384,
        },
    )


def replace_document_chunks(
    collection,
    chunks: Sequence[ContractChunk],
    embeddings: Sequence[Sequence[float]],
) -> int:
    if not chunks:
        raise ValueError("No sanitized chunks were supplied.")
    if len(chunks) != len(embeddings):
        raise ValueError("Chunk and embedding counts must match.")
    if any(not chunk.sanitized for chunk in chunks):
        raise ValueError("Only sanitized chunks may be stored.")

    document_id = chunks[0].document_id
    if any(chunk.document_id != document_id for chunk in chunks):
        raise ValueError("All chunks must belong to one document.")

    existing = collection.get(where={"document_id": document_id})
    existing_ids = existing.get("ids", [])
    if existing_ids:
        collection.delete(ids=existing_ids)

    collection.upsert(
        ids=[chunk.chunk_id for chunk in chunks],
        documents=[chunk.text for chunk in chunks],
        embeddings=[list(vector) for vector in embeddings],
        metadatas=[
            {
                "document_id": chunk.document_id,
                "source": chunk.source,
                "page_number": chunk.page_number,
                "sanitized": True,
            }
            for chunk in chunks
        ],
    )
    return len(chunks)
