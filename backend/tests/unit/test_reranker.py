"""Unit tests for the reranker."""
from backend.ai.rag.chunker import Chunk
from backend.ai.rag.reranker import CrossEncoderReranker

AMHARIC_QUESTION = "የትኩሳት መመሪያ የት ነው?"


def _chunk(index: int, text: str, score: float | None) -> Chunk:
    return Chunk(text=text, chunk_index=index, document_id=f"doc-{index}", score=score)


def test_cross_lingual_query_keeps_vector_order() -> None:
    # An Amharic question shares no words with English chunks. Ranking must follow the
    # vector scores instead of collapsing to an arbitrary order.
    chunks = [
        _chunk(0, "Fever management for children under five.", 0.91),
        _chunk(1, "Vaccination schedule overview.", 0.42),
        _chunk(2, "When to refer a child with fever.", 0.77),
    ]
    ranked = CrossEncoderReranker().rerank(AMHARIC_QUESTION, chunks, top_k=3)

    assert [c.chunk_index for c in ranked] == [0, 2, 1]


def test_english_translation_breaks_near_ties() -> None:
    chunks = [
        _chunk(0, "Vaccination schedule overview.", 0.80),
        _chunk(1, "Where to find the fever guideline.", 0.80),
    ]
    ranked = CrossEncoderReranker().rerank(
        [AMHARIC_QUESTION, "Where is the fever guideline?"], chunks, top_k=2
    )

    assert ranked[0].chunk_index == 1


def test_missing_scores_fall_back_to_store_order() -> None:
    chunks = [_chunk(i, f"unrelated text {i}", None) for i in range(3)]
    ranked = CrossEncoderReranker().rerank(AMHARIC_QUESTION, chunks, top_k=2)

    assert [c.chunk_index for c in ranked] == [0, 1]


def test_lexical_weight_one_ranks_by_keyword_overlap() -> None:
    chunks = [
        _chunk(0, "Vaccination schedule overview.", 0.95),
        _chunk(1, "Fever guideline for children.", 0.10),
    ]
    ranked = CrossEncoderReranker(lexical_weight=1.0).rerank("fever guideline", chunks, top_k=1)

    assert ranked[0].chunk_index == 1


def test_punctuation_does_not_block_keyword_matches() -> None:
    reranker = CrossEncoderReranker()
    assert reranker._score(reranker._tokens("fever"), "Fever, cough, and rash.") > 0
