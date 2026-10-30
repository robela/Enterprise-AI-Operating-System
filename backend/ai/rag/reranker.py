"""Reranker — vector similarity with a light keyword-overlap boost (pure Python)."""
from __future__ import annotations

import re

from backend.ai.rag.chunker import Chunk
from backend.core.config.settings import settings

_TOKEN_RE = re.compile(r"\w+")


class CrossEncoderReranker:
    """
    Ranks chunks mainly by the vector store's similarity score, which works across
    languages (an Amharic question still ranks English chunks correctly). Keyword overlap
    with any query variant (e.g. the question and its English translation) only breaks
    near-ties. For better quality, replace with a multilingual cross-encoder model.
    """

    def __init__(self, lexical_weight: float | None = None):
        weight = settings.rag_rerank_lexical_weight if lexical_weight is None else lexical_weight
        self.lexical_weight = min(max(weight, 0.0), 1.0)

    def rerank(self, query: str | list[str], chunks: list[Chunk], top_k: int = 5) -> list[Chunk]:
        queries = [query] if isinstance(query, str) else query
        query_tokens = [tokens for tokens in (self._tokens(q) for q in queries) if tokens]
        scored = []
        for rank, chunk in enumerate(chunks):
            # Without a score from the store, fall back to the store's own order.
            vector = chunk.score if chunk.score is not None else 1.0 - rank / len(chunks)
            lexical = max((self._score(tokens, chunk.text) for tokens in query_tokens), default=0.0)
            scored.append((chunk, (1 - self.lexical_weight) * vector + self.lexical_weight * lexical))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [c for c, _ in scored[:top_k]]

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {token.casefold() for token in _TOKEN_RE.findall(text)}

    @classmethod
    def _score(cls, query_tokens: set[str], text: str) -> float:
        text_tokens = cls._tokens(text)
        if not text_tokens:
            return 0.0
        return len(query_tokens & text_tokens) / len(query_tokens | text_tokens)
