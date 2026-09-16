from app.models.chunk import ContractChunk
from app.services.vector_store import replace_document_chunks


class FakeCollection:
    def __init__(self) -> None:
        self.upsert_payload = None
        self.deleted = []

    def get(self, **kwargs):
        return {"ids": ["old-chunk"]}

    def delete(self, ids):
        self.deleted = ids

    def upsert(self, **kwargs):
        self.upsert_payload = kwargs


def test_only_sanitized_chunks_are_stored() -> None:
    collection = FakeCollection()
    chunks = [ContractChunk(
        chunk_id="doc-chunk-001",
        document_id="doc",
        source="contract.pdf",
        page_number=1,
        text="Contact <PERSON> at <EMAIL_ADDRESS>.",
        sanitized=True,
    )]
    count = replace_document_chunks(collection, chunks, [[0.0] * 384])
    assert count == 1
    assert collection.deleted == ["old-chunk"]
    assert collection.upsert_payload["documents"][0] == chunks[0].text
    assert collection.upsert_payload["metadatas"][0]["sanitized"] is True
