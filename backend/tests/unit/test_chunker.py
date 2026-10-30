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


def test_text_without_spaces_is_split_by_max_chars():
    # Scripts written without spaces between words arrive as one huge "word".
    text = "ሀ" * 12000
    chunks = TextChunker(chunk_size=512, overlap=64, max_chars=5000).chunk(text, document_id="doc4")

    assert len(chunks) == 3
    assert all(len(c.text) <= 5000 for c in chunks)
    assert "".join(c.text for c in chunks) == text
    assert [c.chunk_index for c in chunks] == [0, 1, 2]


def test_long_text_breaks_at_ethiopic_full_stop():
    sentence = "ሰላም" * 10 + "።"  # 31 characters ending in the Ethiopic full stop
    chunks = TextChunker(chunk_size=512, overlap=0, max_chars=100).chunk(sentence * 10)

    assert len(chunks) > 1
    assert all(c.text.endswith("።") for c in chunks)


def test_english_chunks_are_not_split_by_default_max_chars():
    words = ["word" + str(i % 1000).zfill(3) for i in range(1200)]
    chunks = TextChunker(chunk_size=512, overlap=64).chunk(" ".join(words))

    assert len(chunks) == 3
    assert chunks[0].text.split() == words[:512]
