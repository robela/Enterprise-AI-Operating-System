"""pgvector vector store adapter."""
from __future__ import annotations

from backend.ai.rag.chunker import Chunk
from backend.core.database.session import AsyncSessionLocal


class PgVectorStore:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

    async def upsert(
        self,
        document_id: str,
        chunks: list[Chunk],
        embeddings: list[list[float]],
        metadata: dict,
    ) -> None:
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            for chunk, embedding in zip(chunks, embeddings):
                await session.execute(
                    text(
                        """
                        INSERT INTO document_chunks
                            (tenant_id, document_id, chunk_index, chunk_text, embedding, metadata)
                        VALUES
                            (:tenant_id, :document_id, :chunk_index, :chunk_text, :embedding, :metadata)
                        ON CONFLICT (tenant_id, document_id, chunk_index)
                        DO UPDATE SET chunk_text = EXCLUDED.chunk_text,
                                      embedding  = EXCLUDED.embedding
                        """
                    ),
                    {
                        "tenant_id": self.tenant_id,
                        "document_id": document_id,
                        "chunk_index": chunk.chunk_index,
                        "chunk_text": chunk.text,
                        "embedding": str(embedding),
                        "metadata": str(metadata),
                    },
                )
            await session.commit()

    async def search(self, query_embedding: list[float], top_k: int = 5) -> list[Chunk]:
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(
                    """
                    SELECT document_id, chunk_index, chunk_text
                    FROM document_chunks
                    WHERE tenant_id = :tenant_id
                    ORDER BY embedding <=> :embedding
                    LIMIT :top_k
                    """
                ),
                {
                    "tenant_id": self.tenant_id,
                    "embedding": str(query_embedding),
                    "top_k": top_k,
                },
            )
            rows = result.fetchall()
            return [
                Chunk(
                    text=row.chunk_text,
                    chunk_index=row.chunk_index,
                    document_id=row.document_id,
                )
                for row in rows
            ]
