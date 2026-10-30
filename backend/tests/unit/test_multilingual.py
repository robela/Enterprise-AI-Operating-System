"""Unit tests for query analysis and answer localization."""
import pytest

from backend.ai import multilingual
from backend.ai.multilingual import analyze_query, localize_answer
from fakes import FailingProvider, FakeProvider

AMHARIC_QUESTION = "የትኩሳት መመሪያ የት ነው?"
ENGLISH_TRANSLATION = "Where is the fever guideline?"


@pytest.mark.asyncio
async def test_plain_english_skips_the_llm_call() -> None:
    provider = FakeProvider()
    analysis = await analyze_query("What should I do when the child has a fever?", provider)

    assert analysis.language == "en"
    assert analysis.english_query is None
    assert analysis.source == "heuristic"
    assert provider.chat_calls == []


@pytest.mark.asyncio
async def test_detects_language_and_translates_from_fenced_json() -> None:
    provider = FakeProvider(
        replies=['```json\n{"language": "am", "english": "Where is the fever guideline?"}\n```']
    )
    analysis = await analyze_query(AMHARIC_QUESTION, provider)

    assert analysis.language == "am"
    assert analysis.english_query == ENGLISH_TRANSLATION
    assert analysis.source == "llm"
    assert provider.chat_calls[0][-1].content == AMHARIC_QUESTION


@pytest.mark.asyncio
async def test_language_name_from_model_is_normalized() -> None:
    provider = FakeProvider(replies=['{"language": "Amharic", "english": "Where is the guideline?"}'])
    analysis = await analyze_query(AMHARIC_QUESTION, provider)

    assert analysis.language == "am"


@pytest.mark.asyncio
async def test_requested_language_wins_over_detection() -> None:
    provider = FakeProvider(replies=['{"language": "am", "english": "Where is the fever guideline?"}'])
    analysis = await analyze_query(AMHARIC_QUESTION, provider, requested_language="om")

    assert analysis.language == "om"
    assert analysis.english_query == ENGLISH_TRANSLATION


@pytest.mark.asyncio
async def test_unchanged_translation_is_dropped() -> None:
    question = "Daa'imni dhukkubsate maal gochuu qaba?"
    provider = FakeProvider(replies=[f'{{"language": "om", "english": "{question}"}}'])
    analysis = await analyze_query(question, provider)

    assert analysis.language == "om"
    assert analysis.english_query is None


@pytest.mark.asyncio
async def test_unparseable_reply_falls_back() -> None:
    analysis = await analyze_query(AMHARIC_QUESTION, FakeProvider(replies=["Sorry, I cannot help."]))

    assert analysis.language is None
    assert analysis.english_query is None
    assert analysis.source == "fallback"


@pytest.mark.asyncio
async def test_provider_error_falls_back_without_raising() -> None:
    analysis = await analyze_query(AMHARIC_QUESTION, FailingProvider(), requested_language="am")

    assert analysis.language == "am"
    assert analysis.english_query is None


@pytest.mark.asyncio
async def test_disabled_analysis_makes_no_call(monkeypatch) -> None:
    monkeypatch.setattr(multilingual.settings, "multilingual_query_analysis", False)
    provider = FakeProvider()
    analysis = await analyze_query(AMHARIC_QUESTION, provider)

    assert analysis.language is None
    assert provider.chat_calls == []


@pytest.mark.asyncio
async def test_localize_answer_returns_translation() -> None:
    provider = FakeProvider(replies=["## የጎደለ መረጃ\n\n- የልጁ ዕድሜ ስንት ነው?"])
    translated = await localize_answer("## Missing information\n\n- What is the child's age?", "am", provider)

    assert translated is not None
    assert translated.startswith("## የጎደለ መረጃ")
    assert "Amharic" in provider.chat_calls[0][0].content


@pytest.mark.asyncio
async def test_localize_answer_rejects_wrong_script() -> None:
    provider = FakeProvider(replies=["## Missing information\n\n- What is the child's age?"])
    assert await localize_answer("## Missing information", "am", provider) is None


@pytest.mark.asyncio
async def test_localize_answer_returns_none_on_error() -> None:
    assert await localize_answer("text", "am", FailingProvider()) is None
