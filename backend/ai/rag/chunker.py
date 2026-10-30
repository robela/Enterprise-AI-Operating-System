"""Text chunker — splits documents into overlapping chunks."""
from __future__ import annotations
from dataclasses import dataclass

from backend.core.config.settings import settings

# Where a long piece may be cut: whitespace, sentence ends, and commas, including the
# Ethiopic wordspace, full stop, and comma, and CJK punctuation.
_BREAK_CHARS = (" ", "\n", ".", "?", "!", "፡", "።", "፣", "。", "、", "，")


@dataclass
class Chunk:
    text: str
    chunk_index: int
    document_id: str = ""
    start_char: int = 0
    end_char: int = 0
    metadata: dict | None = None
    score: float | None = None  # similarity to the query, when the vector store returns it


class TextChunker:
    def __init__(
        self,
        chunk_size: int | None = None,
        overlap: int | None = None,
        max_chars: int | None = None,
    ):
        self.chunk_size = chunk_size if chunk_size is not None else settings.rag_chunk_size
        self.overlap = overlap if overlap is not None else settings.rag_chunk_overlap
        self.max_chars = max_chars if max_chars is not None else settings.rag_chunk_max_chars

    def chunk(self, text: str, document_id: str = "") -> list[Chunk]:
        words = text.split()
        pieces: list[str] = []
        step = self.chunk_size - self.overlap
        for start in range(0, len(words), max(step, 1)):
            end = start + self.chunk_size
            chunk_words = words[start:end]
            if not chunk_words:
                break
            pieces.extend(self._split_long(" ".join(chunk_words)))
            if end >= len(words):
                break
        return [
            Chunk(text=piece, chunk_index=i, document_id=document_id)
            for i, piece in enumerate(pieces)
        ]

    def _split_long(self, text: str) -> list[str]:
        """Split text over max_chars, e.g. languages written without spaces between words."""
        if self.max_chars <= 0 or len(text) <= self.max_chars:
            return [text]
        parts: list[str] = []
        start = 0
        while start < len(text):
            end = min(start + self.max_chars, len(text))
            if end < len(text):
                # Prefer a natural break in the last fifth of the window.
                floor = start + int(self.max_chars * 0.8)
                cut = max(text.rfind(sep, floor, end) for sep in _BREAK_CHARS)
                if cut != -1:
                    end = cut + 1
            part = text[start:end].strip()
            if part:
                parts.append(part)
            start = end
        return parts
