from app.models.policy import Policy
from app.models.retrieval import RetrievedEvidence
from app.services.embedder import embed_texts


def retrieve_for_policy(
    collection,
    policy: Policy,
    document_id: str,
    top_k: int = 3,
) -> list[RetrievedEvidence]:
    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    query_embedding = embed_texts([policy.requirement])[0]
    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"document_id": document_id},
        include=["documents", "metadatas", "distances"],
    )

    ids = result.get("ids", [[]])[0]
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    evidence: list[RetrievedEvidence] = []
    for index, chunk_id in enumerate(ids):
        metadata = metadatas[index]
        evidence.append(
            RetrievedEvidence(
                policy_id=policy.policy_id,
                chunk_id=chunk_id,
                document_id=str(metadata["document_id"]),
                source=str(metadata["source"]),
                page_number=int(metadata["page_number"]),
                text=documents[index],
                distance=float(distances[index]),
            )
        )
    return evidence
