"""Qdrant vector store adapter."""
from __future__ import annotations

import uuid

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from backend.ai.rag.chunker import Chunk
from backend.core.config.settings import settings


class QdrantStore:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self._collection = f"chunks_{tenant_id}"
        self._client = AsyncQdrantClient(
            url=settings.qdrant_url, api_key=settings.qdrant_api_key or None
        )

    async def _ensure_collection(self, vector_size: int) -> None:
        collections = await self._client.get_collections()
        names = [c.name for c in collections.collections]
        if self._collection not in names:
            await self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

    async def upsert(
        self,
        document_id: str,
        chunks: list[Chunk],
        embeddings: list[list[float]],
        metadata: dict,
    ) -> None:
        if embeddings:
            await self._ensure_collection(len(embeddings[0]))
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "document_id": document_id,
                    "chunk_index": chunk.chunk_index,
                    "chunk_text": chunk.text,
                    "tenant_id": self.tenant_id,
                    **metadata,
                },
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]
        await self._client.upsert(collection_name=self._collection, points=points)

    async def search(self, query_embedding: list[float], top_k: int = 5) -> list[Chunk]:
        results = await self._client.search(
            collection_name=self._collection,
            query_vector=query_embedding,
            limit=top_k,
        )
        return [
            Chunk(
                text=r.payload["chunk_text"],
                chunk_index=r.payload["chunk_index"],
                document_id=r.payload["document_id"],
            )
            for r in results
        ]
