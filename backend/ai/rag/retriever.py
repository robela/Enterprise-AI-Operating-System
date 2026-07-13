"""Vector retriever — stores and retrieves chunks from the vector store."""
from __future__ import annotations

from backend.ai.rag.chunker import Chunk
from backend.core.config.settings import settings


class VectorRetriever:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self._collection = f"{settings.elasticsearch_index_prefix}_{tenant_id}"

    async def store(
        self,
        document_id: str,
        chunks: list[Chunk],
        embeddings: list[list[float]],
        metadata: dict,
    ) -> None:
        if settings.vector_store == "qdrant":
            await self._store_qdrant(document_id, chunks, embeddings, metadata)
        else:
            await self._store_pgvector(document_id, chunks, embeddings, metadata)

    async def retrieve(self, query_embedding: list[float], top_k: int = 10) -> list[Chunk]:
        if settings.vector_store == "qdrant":
            return await self._retrieve_qdrant(query_embedding, top_k)
        return await self._retrieve_pgvector(query_embedding, top_k)

    async def _store_pgvector(self, document_id, chunks, embeddings, metadata):
        from backend.ai.vectorstores.pgvector import PgVectorStore
        store = PgVectorStore(tenant_id=self.tenant_id)
        await store.upsert(document_id, chunks, embeddings, metadata)

    async def _retrieve_pgvector(self, query_embedding, top_k):
        from backend.ai.vectorstores.pgvector import PgVectorStore
        store = PgVectorStore(tenant_id=self.tenant_id)
        return await store.search(query_embedding, top_k=top_k)

    async def _store_qdrant(self, document_id, chunks, embeddings, metadata):
        from backend.ai.vectorstores.qdrant import QdrantStore
        store = QdrantStore(tenant_id=self.tenant_id)
        await store.upsert(document_id, chunks, embeddings, metadata)

    async def _retrieve_qdrant(self, query_embedding, top_k):
        from backend.ai.vectorstores.qdrant import QdrantStore
        store = QdrantStore(tenant_id=self.tenant_id)
        return await store.search(query_embedding, top_k=top_k)
