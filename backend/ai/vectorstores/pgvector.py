"""pgvector vector store adapter."""
from __future__ import annotations

import asyncio
import json
import math

from sqlalchemy.exc import OperationalError

from backend.ai.rag.chunker import Chunk
from backend.core.config.settings import settings
from backend.core.database.session import AsyncSessionLocal


class PgVectorStore:
    _sqlite_table_ready: bool = False
    _sqlite_table_lock = asyncio.Lock()

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

    @classmethod
    async def _ensure_sqlite_table(cls, session) -> None:
        if cls._sqlite_table_ready:
            return

        async with cls._sqlite_table_lock:
            if cls._sqlite_table_ready:
                return

            from sqlalchemy import text

            await session.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS document_chunks (
                        tenant_id TEXT NOT NULL,
                        document_id TEXT NOT NULL,
                        chunk_index INTEGER NOT NULL,
                        chunk_text TEXT NOT NULL,
                        embedding TEXT,
                        metadata TEXT,
                        PRIMARY KEY (tenant_id, document_id, chunk_index)
                    )
                    """
                )
            )
            cls._sqlite_table_ready = True

    @staticmethod
    def _is_sqlite_locked(exc: Exception) -> bool:
        return "database is locked" in str(exc).lower()

    async def _sqlite_upsert_once(
        self,
        document_id: str,
        chunks: list[Chunk],
        embeddings: list[list[float]],
        metadata: dict,
    ) -> None:
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            await self._ensure_sqlite_table(session)
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

    async def upsert(
        self,
        document_id: str,
        chunks: list[Chunk],
        embeddings: list[list[float]],
        metadata: dict,
    ) -> None:
        from sqlalchemy import text

        if settings.database_url.startswith("sqlite"):
            attempts = 4
            for attempt in range(attempts):
                try:
                    await self._sqlite_upsert_once(document_id, chunks, embeddings, metadata)
                    return
                except OperationalError as exc:
                    if self._is_sqlite_locked(exc) and attempt < attempts - 1:
                        await asyncio.sleep(0.05 * (2**attempt))
                        continue
                    raise
            return

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

    async def delete_document(self, document_id: str) -> None:
        from sqlalchemy import text

        if settings.database_url.startswith("sqlite"):
            attempts = 4
            for attempt in range(attempts):
                try:
                    async with AsyncSessionLocal() as session:
                        await self._ensure_sqlite_table(session)
                        await session.execute(
                            text(
                                """
                                DELETE FROM document_chunks
                                WHERE tenant_id = :tenant_id AND document_id = :document_id
                                """
                            ),
                            {
                                "tenant_id": self.tenant_id,
                                "document_id": document_id,
                            },
                        )
                        await session.commit()
                        return
                except OperationalError as exc:
                    if self._is_sqlite_locked(exc) and attempt < attempts - 1:
                        await asyncio.sleep(0.05 * (2**attempt))
                        continue
                    raise
            return

        async with AsyncSessionLocal() as session:
            await session.execute(
                text(
                    """
                    DELETE FROM document_chunks
                    WHERE tenant_id = :tenant_id AND document_id = :document_id
                    """
                ),
                {
                    "tenant_id": self.tenant_id,
                    "document_id": document_id,
                },
            )
            await session.commit()

    async def search(self, query_embedding: list[float], top_k: int = 5) -> list[Chunk]:
        from sqlalchemy import text

        if settings.database_url.startswith("sqlite"):
            attempts = 3
            for attempt in range(attempts):
                try:
                    async with AsyncSessionLocal() as session:
                        result = await session.execute(
                            text(
                                """
                                SELECT document_id, chunk_index, chunk_text, embedding
                                FROM document_chunks
                                WHERE tenant_id = :tenant_id
                                ORDER BY rowid DESC
                                """
                            ),
                            {"tenant_id": self.tenant_id},
                        )
                        return rank_by_similarity(result.fetchall(), query_embedding, top_k)
                except OperationalError as exc:
                    if self._is_sqlite_locked(exc) and attempt < attempts - 1:
                        await asyncio.sleep(0.03 * (2**attempt))
                        continue
                    raise
            return []

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(
                    """
                    SELECT document_id, chunk_index, chunk_text,
                           embedding <=> :embedding AS distance
                    FROM document_chunks
                    WHERE tenant_id = :tenant_id
                    ORDER BY distance
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
                    # Cosine distance -> cosine similarity, so higher means more relevant.
                    score=1.0 - float(row.distance),
                )
                for row in rows
            ]


def rank_by_similarity(rows, query_embedding: list[float], top_k: int) -> list[Chunk]:
    """Cosine ranking for the SQLite dev store, which has no vector operators.

    Rows must be ordered newest first; the stable sort keeps that order for ties.
    Rows whose embedding is missing or has a different dimension are skipped.
    """
    scored: list[Chunk] = []
    for row in rows:
        try:
            embedding = json.loads(row.embedding) if row.embedding else None
        except ValueError:
            embedding = None
        if not embedding or len(embedding) != len(query_embedding):
            continue
        scored.append(
            Chunk(
                text=row.chunk_text,
                chunk_index=row.chunk_index,
                document_id=row.document_id,
                score=_cosine_similarity(query_embedding, embedding),
            )
        )
    scored.sort(key=lambda chunk: chunk.score, reverse=True)
    return scored[:top_k]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    if not norm:
        return 0.0
    return sum(x * y for x, y in zip(a, b)) / norm
