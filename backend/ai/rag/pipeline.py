"""RAG pipeline — ingest and query documents."""
from __future__ import annotations

import structlog

from backend.ai.rag.chunker import TextChunker
from backend.ai.rag.retriever import VectorRetriever
from backend.ai.rag.reranker import CrossEncoderReranker
from backend.ai.providers import get_provider
from backend.ai.base import ChatMessage

logger = structlog.get_logger(__name__)


class RAGPipeline:
    """
    Full RAG pipeline:
    Ingest: Document → Chunks → Embeddings → Vector Store
    Query:  Question → Retrieve → Rerank → LLM → Answer + Citations
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self._chunker = TextChunker()
        self._retriever = VectorRetriever(tenant_id=tenant_id)
        self._reranker = CrossEncoderReranker()

    async def ingest(self, document_id: str, text: str, metadata: dict | None = None) -> int:
        """Chunk, embed, and store a document. Returns chunk count."""
        chunks = self._chunker.chunk(text)
        provider = get_provider()
        embeddings = await provider.embed([c.text for c in chunks])
        await self._retriever.store(
            document_id=document_id,
            chunks=chunks,
            embeddings=embeddings,
            metadata=metadata or {},
        )
        logger.info("rag_ingested", document_id=document_id, chunk_count=len(chunks))
        return len(chunks)

    async def query(
        self,
        question: str,
        top_k: int = 5,
        system_prompt: str | None = None,
    ) -> dict:
        """Retrieve relevant chunks and generate an answer."""
        provider = get_provider()
        query_embedding = (await provider.embed([question]))[0]

        candidates = await self._retriever.retrieve(query_embedding, top_k=top_k * 2)
        chunks = self._reranker.rerank(question, candidates, top_k=top_k)

        context = "\n\n".join(
            f"[Source: {c.document_id}]\n{c.text}" for c in chunks
        )

        messages = [
            ChatMessage(
                role="system",
                content=system_prompt or (
                    "You are a helpful assistant. Answer based on the context below. "
                    "Always cite sources using [Source: ...] notation.\n\n"
                    f"Context:\n{context}"
                ),
            ),
            ChatMessage(role="user", content=question),
        ]

        response = await provider.chat(messages, temperature=0.3)

        return {
            "answer": response.content,
            "sources": [c.document_id for c in chunks],
            "chunks_used": len(chunks),
        }
