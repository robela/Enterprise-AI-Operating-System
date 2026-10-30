"""Unit tests for the rerankers."""
import pytest

from backend.ai.rag import reranker as reranker_module
from backend.ai.rag.chunker import Chunk
from backend.ai.rag.reranker import (
    LLMReranker,
    VectorReranker,
    build_reranker,
    resolve_reranker_name,
)
from fakes import FailingProvider, FakeProvider

AMHARIC_QUESTION = "የትኩሳት መመሪያ የት ነው?"


def _chunk(index: int, text: str, score: float | None) -> Chunk:
    return Chunk(text=text, chunk_index=index, document_id=f"doc-{index}", score=score)


def _fever_chunks() -> list[Chunk]:
    return [
        _chunk(0, "Fever management for children under five.", 0.91),
        _chunk(1, "Vaccination schedule overview.", 0.42),
        _chunk(2, "When to refer a child with fever.", 0.77),
    ]


async def test_cross_lingual_query_keeps_vector_order() -> None:
    # An Amharic question shares no words with English chunks. Ranking must follow the
    # vector scores instead of collapsing to an arbitrary order.
    ranked = await VectorReranker().rerank(AMHARIC_QUESTION, _fever_chunks(), top_k=3)

    assert [c.chunk_index for c in ranked] == [0, 2, 1]


async def test_english_translation_breaks_near_ties() -> None:
    chunks = [
        _chunk(0, "Vaccination schedule overview.", 0.80),
        _chunk(1, "Where to find the fever guideline.", 0.80),
    ]
    ranked = await VectorReranker().rerank(
        [AMHARIC_QUESTION, "Where is the fever guideline?"], chunks, top_k=2
    )

    assert ranked[0].chunk_index == 1


async def test_missing_scores_fall_back_to_store_order() -> None:
    chunks = [_chunk(i, f"unrelated text {i}", None) for i in range(3)]
    ranked = await VectorReranker().rerank(AMHARIC_QUESTION, chunks, top_k=2)

    assert [c.chunk_index for c in ranked] == [0, 1]


async def test_lexical_weight_one_ranks_by_keyword_overlap() -> None:
    chunks = [
        _chunk(0, "Vaccination schedule overview.", 0.95),
        _chunk(1, "Fever guideline for children.", 0.10),
    ]
    ranked = await VectorReranker(lexical_weight=1.0).rerank("fever guideline", chunks, top_k=1)

    assert ranked[0].chunk_index == 1


def test_punctuation_does_not_block_keyword_matches() -> None:
    reranker = VectorReranker()
    assert reranker._score(reranker._tokens("fever"), "Fever, cough, and rash.") > 0


async def test_llm_reranker_uses_model_order() -> None:
    # Vector order is [0, 2, 1] (passages 1, 2, 3); the model prefers the referral chunk.
    provider = FakeProvider(replies=['{"ranking": [2, 1, 3]}'])

    ranked = await LLMReranker(provider=provider).rerank(
        [AMHARIC_QUESTION, "Ask about referral"], _fever_chunks(), top_k=2
    )

    assert [c.chunk_index for c in ranked] == [2, 0]
    prompt = provider.chat_calls[0][1].content
    assert AMHARIC_QUESTION in prompt and "Ask about referral" in prompt
    assert "[1]\nFever management" in prompt


async def test_llm_reranker_keeps_omitted_passages_in_vector_order() -> None:
    provider = FakeProvider(replies=['Sure: {"ranking": [3, 3, 9, "x"]}'])

    ranked = await LLMReranker(provider=provider).rerank(AMHARIC_QUESTION, _fever_chunks(), top_k=3)

    assert [c.chunk_index for c in ranked] == [1, 0, 2]


@pytest.mark.parametrize("provider", [FailingProvider(), FakeProvider(replies=["not json"])])
async def test_llm_reranker_falls_back_to_vector_order(provider) -> None:
    ranked = await LLMReranker(provider=provider).rerank(AMHARIC_QUESTION, _fever_chunks(), top_k=3)

    assert [c.chunk_index for c in ranked] == [0, 2, 1]


async def test_llm_reranker_skips_the_call_for_one_chunk() -> None:
    provider = FakeProvider()

    ranked = await LLMReranker(provider=provider).rerank(AMHARIC_QUESTION, _fever_chunks()[:1])

    assert len(ranked) == 1
    assert provider.chat_calls == []


async def test_llm_reranker_truncates_long_passages() -> None:
    provider = FakeProvider(replies=['{"ranking": [1, 2]}'])
    chunks = [_chunk(0, "a" * 50, 0.9), _chunk(1, "b" * 50, 0.8)]

    await LLMReranker(provider=provider, max_passage_chars=10).rerank("q", chunks)

    prompt = provider.chat_calls[0][1].content
    assert "a" * 10 in prompt and "a" * 11 not in prompt


def test_tenant_choice_overrides_default(monkeypatch) -> None:
    monkeypatch.setattr(reranker_module.settings, "rag_reranker", "vector")

    assert resolve_reranker_name({"rag": {"reranker": "llm"}}) == "llm"
    assert isinstance(build_reranker({"rag": {"reranker": "llm"}}), LLMReranker)
    assert isinstance(build_reranker({}), VectorReranker)


def test_default_applies_without_valid_tenant_choice(monkeypatch) -> None:
    monkeypatch.setattr(reranker_module.settings, "rag_reranker", "LLM")

    assert resolve_reranker_name(None) == "llm"
    assert resolve_reranker_name({"rag": {"reranker": "cohere"}}) == "llm"
    assert resolve_reranker_name({"rag": "llm"}) == "llm"

    monkeypatch.setattr(reranker_module.settings, "rag_reranker", "typo")
    assert resolve_reranker_name(None) == "vector"
