"""Unit tests for the RAG chunker."""
import pytest

from backend.ai.rag.chunker import TextChunker


def test_chunk_basic():
    chunker = TextChunker(chunk_size=5, overlap=1)
    words = ["w" + str(i) for i in range(20)]
    text = " ".join(words)
    chunks = chunker.chunk(text, document_id="doc1")
    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.text
        assert chunk.document_id == "doc1"


def test_chunk_short_text():
    chunker = TextChunker(chunk_size=100, overlap=10)
    chunks = chunker.chunk("hello world", document_id="doc2")
    assert len(chunks) == 1
    assert chunks[0].text == "hello world"


def test_chunk_empty_text():
    chunker = TextChunker()
    chunks = chunker.chunk("", document_id="doc3")
    assert chunks == []
