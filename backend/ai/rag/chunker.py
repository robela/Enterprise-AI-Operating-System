"""Text chunker — splits documents into overlapping chunks."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    chunk_index: int
    document_id: str = ""
    start_char: int = 0
    end_char: int = 0
    metadata: dict | None = None


class TextChunker:
    def __init__(self, chunk_size: int = 512, overlap: int = 64):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str, document_id: str = "") -> list[Chunk]:
        words = text.split()
        chunks: list[Chunk] = []
        step = self.chunk_size - self.overlap
        for i, start in enumerate(range(0, len(words), max(step, 1))):
            end = start + self.chunk_size
            chunk_words = words[start:end]
            if not chunk_words:
                break
            chunks.append(
                Chunk(
                    text=" ".join(chunk_words),
                    chunk_index=i,
                    document_id=document_id,
                )
            )
            if end >= len(words):
                break
        return chunks
