"""Cosine ranking used by the SQLite development vector store."""
import json
from types import SimpleNamespace

from backend.ai.vectorstores.pgvector import rank_by_similarity


def _row(index: int, embedding) -> SimpleNamespace:
    return SimpleNamespace(
        document_id=f"doc-{index}",
        chunk_index=index,
        chunk_text=f"chunk {index}",
        embedding=json.dumps(embedding) if embedding is not None else None,
    )


def test_ranks_by_cosine_similarity() -> None:
    rows = [_row(0, [0.0, 1.0]), _row(1, [1.0, 0.0]), _row(2, [0.7, 0.7])]
    ranked = rank_by_similarity(rows, [1.0, 0.0], top_k=2)

    assert [c.chunk_index for c in ranked] == [1, 2]
    assert ranked[0].score == 1.0


def test_skips_missing_and_mismatched_embeddings() -> None:
    rows = [_row(0, None), _row(1, [1.0, 0.0, 0.0]), _row(2, [1.0, 0.0])]
    ranked = rank_by_similarity(rows, [1.0, 0.0], top_k=5)

    assert [c.chunk_index for c in ranked] == [2]


def test_ties_keep_newest_first_order() -> None:
    rows = [_row(5, [0.1, 0.1]), _row(4, [0.1, 0.1]), _row(3, [0.1, 0.1])]
    ranked = rank_by_similarity(rows, [0.1, 0.1], top_k=3)

    assert [c.chunk_index for c in ranked] == [5, 4, 3]
