"""Rewriting follow-up questions with the earlier turns."""
from backend.ai.rag import query_rewriter
from backend.ai.rag.query_rewriter import rewrite_with_history
from fakes import FailingProvider, FakeProvider

EARLIER = "What is the refund policy for online orders?"
FOLLOW_UP = "How long does it take?"
STANDALONE = "How long does a refund for an online order take?"


async def test_no_history_skips_the_call() -> None:
    provider = FakeProvider()

    result = await rewrite_with_history(FOLLOW_UP, [FOLLOW_UP], provider)

    assert result.question == FOLLOW_UP and not result.rewritten
    assert provider.chat_calls == []


async def test_rewrites_with_earlier_messages() -> None:
    provider = FakeProvider(replies=[f'{{"question": "{STANDALONE}", "english": "{STANDALONE}"}}'])

    result = await rewrite_with_history(FOLLOW_UP, [EARLIER, FOLLOW_UP], provider)

    assert result.rewritten
    assert result.question == STANDALONE
    assert result.english is None  # same as the question
    prompt = provider.chat_calls[0][1].content
    assert EARLIER in prompt and prompt.count(FOLLOW_UP) == 1


async def test_keeps_the_english_version_of_a_non_english_question() -> None:
    provider = FakeProvider(
        replies=['{"question": "ተመላሽ ገንዘብ ስንት ቀን ይወስዳል?", "english": "' + STANDALONE + '"}']
    )

    result = await rewrite_with_history("ስንት ቀን ይወስዳል?", [EARLIER], provider)

    assert result.rewritten
    assert result.english == STANDALONE


async def test_failures_keep_the_original_question() -> None:
    for provider in (FailingProvider(), FakeProvider(replies=["not json"])):
        result = await rewrite_with_history(FOLLOW_UP, [EARLIER], provider)
        assert result.question == FOLLOW_UP and not result.rewritten


async def test_can_be_disabled(monkeypatch) -> None:
    monkeypatch.setattr(query_rewriter.settings, "rag_query_rewrite", False)
    provider = FakeProvider()

    result = await rewrite_with_history(FOLLOW_UP, [EARLIER], provider)

    assert not result.rewritten
    assert provider.chat_calls == []
