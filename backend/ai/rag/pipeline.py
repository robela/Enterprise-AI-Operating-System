"""RAG pipeline — ingest and query documents."""
from __future__ import annotations

import asyncio
import re

import structlog

from backend.ai.rag.chunker import Chunk, TextChunker
from backend.ai.rag.query_rewriter import rewrite_with_history
from backend.ai.rag.retriever import VectorRetriever
from backend.ai.rag.reranker import Reranker, VectorReranker
from backend.ai.providers import get_embedding_provider, get_provider
from backend.ai.base import ChatMessage
from backend.ai.language import answer_matches_language, language_directive, rewrite_instruction
from backend.core.config.settings import settings

logger = structlog.get_logger(__name__)

# Appended to every system prompt, including tenant overrides, because the cited ids are
# how the answer's sources are chosen.
_CITATION_DIRECTIVE = (
    "Cite each fact with [Source: document_id], using the document ids shown in the context. "
    "Cite nothing when the answer is not based on the context."
)
_CITATION_RE = re.compile(r"\[Source:\s*([^\]]+)\]", re.IGNORECASE)


def cited_sources(answer: str, chunks: list[Chunk]) -> list[str]:
    """Document ids the answer cites, in citation order, limited to the retrieved chunks.

    Answers that cite nothing (greetings, "I don't have that information") get no sources,
    instead of every retrieved document.
    """
    available = {chunk.document_id for chunk in chunks}
    cited: list[str] = []
    for match in _CITATION_RE.finditer(answer or ""):
        for part in re.split(r"[,;]", match.group(1)):
            document_id = part.strip()
            if document_id in available and document_id not in cited:
                cited.append(document_id)
    return cited


class RAGPipeline:
    """
    Full RAG pipeline:
    Ingest: Document → Chunks → Embeddings → Vector Store
    Query:  Question (+ English translation) → Retrieve → Rerank → LLM → Answer in the
            user's language + Citations
    """

    def __init__(self, tenant_id: str, reranker: Reranker | None = None):
        """reranker: use build_reranker(tenant_settings) to honor the tenant's choice."""
        self.tenant_id = tenant_id
        self._chunker = TextChunker()
        self._retriever = VectorRetriever(tenant_id=tenant_id)
        self._reranker = reranker or VectorReranker()

    async def ingest(self, document_id: str, text: str, metadata: dict | None = None) -> int:
        """Chunk, embed, and store a document. Returns chunk count."""
        chunks = self._chunker.chunk(text)
        provider = get_embedding_provider()
        embeddings = await provider.embed([c.text for c in chunks], input_type="document")
        await self._retriever.store(
            document_id=document_id,
            chunks=chunks,
            embeddings=embeddings,
            metadata=metadata or {},
        )
        logger.info("rag_ingested", document_id=document_id, chunk_count=len(chunks))
        return len(chunks)

    async def delete_document(self, document_id: str) -> None:
        """Delete all indexed chunks for a document."""
        await self._retriever.delete_document(document_id)
        logger.info("rag_document_deleted", document_id=document_id)

    async def query(
        self,
        question: str,
        top_k: int | None = None,
        system_prompt: str | None = None,
        language: str | None = None,
        english_query: str | None = None,
        history: list[str] | None = None,
    ) -> dict:
        """Retrieve relevant chunks and answer in the user's language.

        language is the answer language (ISO code); None means "same as the question".
        english_query is an English translation of a non-English question. Searching
        with both finds English and same-language documents.
        history is the user's earlier messages in the conversation, oldest first; a
        follow-up question is rewritten with them before searching.
        """
        top_k = top_k or settings.rag_top_k
        provider = get_provider()
        rewrite = await rewrite_with_history(question, history or [], provider)
        if rewrite.rewritten:
            question = rewrite.question
            # The given translation was made from the follow-up without its context.
            english_query = rewrite.english
        search_queries = [question]
        if english_query and english_query.strip().casefold() != question.strip().casefold():
            search_queries.append(english_query)
        query_embeddings = await get_embedding_provider().embed(search_queries, input_type="query")

        try:
            candidates = await self._retrieve(query_embeddings, top_k * 2)
            chunks = await self._reranker.rerank(search_queries, candidates, top_k=top_k)
        except Exception as exc:
            logger.warning("rag_retrieval_failed", tenant_id=self.tenant_id, error=str(exc))
            chunks = []

        context = "\n\n".join(
            f"[Source: {c.document_id}]\n{c.text}" for c in chunks
        )

        if system_prompt:
            if "{context}" in system_prompt:
                rendered_system_prompt = system_prompt.replace("{context}", context)
            else:
                rendered_system_prompt = f"{system_prompt}\n\nContext:\n{context}"
        else:
            rendered_system_prompt = (
                "You are a helpful assistant. Answer based on the context below. "
                "Always cite sources using [Source: ...] notation.\n\n"
                f"Context:\n{context}"
            )
        # Appended last so they also apply to tenant prompt overrides.
        rendered_system_prompt = (
            f"{rendered_system_prompt}\n\n{_CITATION_DIRECTIVE}\n\n{language_directive(language)}"
        )

        messages = [
            ChatMessage(
                role="system",
                content=rendered_system_prompt,
            ),
            ChatMessage(role="user", content=question),
        ]

        response = await provider.chat(messages, temperature=settings.rag_temperature)
        answer = response.content

        # Models sometimes answer in the context's language (usually English) instead of
        # the user's. When the script shows that clearly, ask once for a rewrite.
        if not answer_matches_language(answer, language, question):
            logger.warning("rag_answer_language_mismatch", tenant_id=self.tenant_id, language=language)
            retry = await provider.chat(
                messages
                + [
                    ChatMessage(role="assistant", content=answer),
                    ChatMessage(role="user", content=rewrite_instruction(language)),
                ],
                temperature=settings.rag_temperature,
            )
            if answer_matches_language(retry.content, language, question):
                answer = retry.content

        sources = cited_sources(answer, chunks)
        return {
            "answer": answer,
            "sources": sources,
            "chunks_used": len(chunks),
            "language": language,
            "query_rewritten": rewrite.rewritten,
        }

    async def _retrieve(self, query_embeddings: list[list[float]], limit: int) -> list[Chunk]:
        """Search with each query embedding and merge, keeping each chunk's best score."""
        results = await asyncio.gather(
            *(self._retriever.retrieve(embedding, top_k=limit) for embedding in query_embeddings)
        )
        merged: dict[tuple[str, int], Chunk] = {}
        for chunks in results:
            for chunk in chunks:
                key = (chunk.document_id, chunk.chunk_index)
                best = merged.get(key)
                if best is None or (chunk.score or 0.0) > (best.score or 0.0):
                    merged[key] = chunk
        return list(merged.values())
