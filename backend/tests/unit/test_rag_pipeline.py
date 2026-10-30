"""Unit tests for multilingual retrieval and answering in the RAG pipeline."""
import pytest

from backend.ai.rag import pipeline as pipeline_module
from backend.ai.rag.chunker import Chunk
from backend.ai.rag.pipeline import RAGPipeline
from fakes import FakeProvider

AMHARIC_QUESTION = "የትኩሳት መመሪያ የት ነው?"
ENGLISH_TRANSLATION = "Where is the fever guideline?"
ENGLISH_ANSWER = "The fever guideline is on page four. [Source: doc-en]"
AMHARIC_ANSWER = "የትኩሳት መመሪያው በገጽ አራት ላይ ነው። [Source: doc-en]"


class FakeRetriever:
    """Returns different chunks for the Amharic and the English query vectors."""

    def __init__(self):
        self.calls: list[tuple[float, ...]] = []

    async def retrieve(self, query_embedding, top_k=10):
        self.calls.append(tuple(query_embedding))
        if query_embedding == [1.0, 0.0, 0.0]:  # Amharic question
            return [
                Chunk(text="Amharic summary", chunk_index=0, document_id="doc-am", score=0.55),
                Chunk(text="Fever guideline, page four.", chunk_index=3, document_id="doc-en", score=0.50),
            ]
        return [  # English translation
            Chunk(text="Fever guideline, page four.", chunk_index=3, document_id="doc-en", score=0.88),
            Chunk(text="Vaccination schedule.", chunk_index=7, document_id="doc-vax", score=0.30),
        ]


@pytest.fixture
def rag(monkeypatch):
    def setup(chat_replies):
        chat = FakeProvider(replies=chat_replies)
        embedder = FakeProvider(
            vectors={AMHARIC_QUESTION: [1.0, 0.0, 0.0], ENGLISH_TRANSLATION: [0.0, 1.0, 0.0]}
        )
        monkeypatch.setattr(pipeline_module, "get_provider", lambda: chat)
        monkeypatch.setattr(pipeline_module, "get_embedding_provider", lambda: embedder)
        pipeline = RAGPipeline(tenant_id="tenant-ml")
        pipeline._retriever = FakeRetriever()
        return pipeline, chat, embedder

    return setup


@pytest.mark.asyncio
async def test_searches_with_question_and_translation(rag) -> None:
    pipeline, chat, embedder = rag([AMHARIC_ANSWER])

    result = await pipeline.query(
        AMHARIC_QUESTION, top_k=2, language="am", english_query=ENGLISH_TRANSLATION
    )

    assert embedder.embed_calls == [([AMHARIC_QUESTION, ENGLISH_TRANSLATION], "query")]
    assert len(pipeline._retriever.calls) == 2
    # The English guideline ranks first through its best score (from the English search).
    assert result["sources"][0] == "doc-en"
    assert result["answer"] == AMHARIC_ANSWER
    assert result["language"] == "am"
    assert "Response language: Amharic (am)" in chat.chat_calls[0][0].content


@pytest.mark.asyncio
async def test_retries_once_when_answer_is_in_the_wrong_script(rag) -> None:
    pipeline, chat, _ = rag([ENGLISH_ANSWER, AMHARIC_ANSWER])

    result = await pipeline.query(
        AMHARIC_QUESTION, language="am", english_query=ENGLISH_TRANSLATION
    )

    assert len(chat.chat_calls) == 2
    retry_messages = chat.chat_calls[1]
    assert retry_messages[-2].role == "assistant"
    assert "Amharic" in retry_messages[-1].content
    assert result["answer"] == AMHARIC_ANSWER


@pytest.mark.asyncio
async def test_keeps_first_answer_when_retry_is_still_wrong(rag) -> None:
    pipeline, chat, _ = rag([ENGLISH_ANSWER, ENGLISH_ANSWER])

    result = await pipeline.query(AMHARIC_QUESTION, language="am")

    assert len(chat.chat_calls) == 2
    assert result["answer"] == ENGLISH_ANSWER


@pytest.mark.asyncio
async def test_unknown_language_answers_in_question_language(rag) -> None:
    pipeline, chat, embedder = rag(["The guideline is on page four."])

    result = await pipeline.query("Where is the fever guideline?")

    assert embedder.embed_calls == [(["Where is the fever guideline?"], "query")]
    assert len(chat.chat_calls) == 1
    assert "same language as the user's question" in chat.chat_calls[0][0].content
    assert result["language"] is None


@pytest.mark.asyncio
async def test_language_directive_follows_tenant_prompt_override(rag) -> None:
    pipeline, chat, _ = rag([AMHARIC_ANSWER])

    await pipeline.query(AMHARIC_QUESTION, system_prompt="Custom tenant prompt.\n{context}", language="am")

    system_prompt = chat.chat_calls[0][0].content
    assert system_prompt.startswith("Custom tenant prompt.")
    assert system_prompt.rstrip().endswith("Write the entire answer in Amharic.")


@pytest.mark.asyncio
async def test_uses_the_injected_reranker(rag) -> None:
    pipeline, _, _ = rag([AMHARIC_ANSWER])

    class RecordingReranker:
        def __init__(self):
            self.calls = []

        async def rerank(self, query, chunks, top_k=5):
            self.calls.append((query, [c.document_id for c in chunks], top_k))
            return [c for c in chunks if c.document_id == "doc-vax"]

    reranker = RecordingReranker()
    pipeline._reranker = reranker

    result = await pipeline.query(
        AMHARIC_QUESTION, top_k=2, language="am", english_query=ENGLISH_TRANSLATION
    )

    assert reranker.calls[0][0] == [AMHARIC_QUESTION, ENGLISH_TRANSLATION]
    assert reranker.calls[0][2] == 2
    assert result["sources"] == ["doc-vax"]


def test_reranker_is_injected_through_the_constructor() -> None:
    sentinel = object()

    assert RAGPipeline(tenant_id="tenant-ml", reranker=sentinel)._reranker is sentinel


@pytest.mark.asyncio
async def test_ingest_embeds_chunks_as_documents(monkeypatch) -> None:
    embedder = FakeProvider()
    stored = {}

    class StoringRetriever:
        async def store(self, document_id, chunks, embeddings, metadata):
            stored.update(document_id=document_id, chunks=chunks, embeddings=embeddings)

    monkeypatch.setattr(pipeline_module, "get_embedding_provider", lambda: embedder)
    pipeline = RAGPipeline(tenant_id="tenant-ml")
    pipeline._retriever = StoringRetriever()

    count = await pipeline.ingest("doc-am", "የትኩሳት መመሪያ በገጽ አራት ላይ ነው።")

    assert count == 1
    assert embedder.embed_calls[0][1] == "document"
    assert stored["document_id"] == "doc-am"
