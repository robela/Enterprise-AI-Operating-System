"""Simple cross-encoder-style reranker (lexical fallback in pure Python)."""
from __future__ import annotations

from backend.ai.rag.chunker import Chunk


class CrossEncoderReranker:
    """
    Reranks retrieved chunks by keyword overlap with the query.
    In production, replace with a real cross-encoder model
    (e.g. cross-encoder/ms-marco-MiniLM-L-6-v2 via sentence-transformers).
    """

    def rerank(self, query: str, chunks: list[Chunk], top_k: int = 5) -> list[Chunk]:
        query_tokens = set(query.lower().split())
        scored = [
            (chunk, self._score(query_tokens, chunk.text))
            for chunk in chunks
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [c for c, _ in scored[:top_k]]

    @staticmethod
    def _score(query_tokens: set[str], text: str) -> float:
        text_tokens = set(text.lower().split())
        if not text_tokens:
            return 0.0
        return len(query_tokens & text_tokens) / len(query_tokens | text_tokens)
