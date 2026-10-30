"""Unit tests for the Gemini adapter (SDK calls are faked; no network)."""
from types import SimpleNamespace

import pytest

from backend.ai.base import ChatMessage
from backend.ai.providers import gemini
from backend.ai.providers.gemini import GeminiProvider


class FakeModel:
    instances: list["FakeModel"] = []

    def __init__(self, model_name, system_instruction=None):
        self.model_name = model_name
        self.system_instruction = system_instruction
        self.calls: list[dict] = []
        FakeModel.instances.append(self)

    async def generate_content_async(self, contents, generation_config=None, stream=False):
        self.calls.append({"contents": contents, "stream": stream})
        if not stream:
            return SimpleNamespace(text="ok")

        async def chunks():
            for text in ["Hel", "lo"]:
                yield SimpleNamespace(text=text)

        return chunks()


@pytest.fixture
def provider(monkeypatch):
    FakeModel.instances = []
    monkeypatch.setattr(gemini.genai, "configure", lambda **kwargs: None)
    monkeypatch.setattr(gemini.genai, "GenerativeModel", FakeModel)
    return GeminiProvider()


MESSAGES = [
    ChatMessage(role="system", content="Answer in Amharic. Context: guideline text"),
    ChatMessage(role="user", content="first question"),
    ChatMessage(role="assistant", content="first answer"),
    ChatMessage(role="user", content="second question"),
]


@pytest.mark.asyncio
async def test_chat_sends_system_prompt_as_system_instruction(provider) -> None:
    response = await provider.chat(MESSAGES)

    model = FakeModel.instances[-1]
    assert response.content == "ok"
    assert model.system_instruction == "Answer in Amharic. Context: guideline text"
    assert [turn["role"] for turn in model.calls[0]["contents"]] == ["user", "model", "user"]
    assert model.calls[0]["contents"][-1]["parts"] == ["second question"]


@pytest.mark.asyncio
async def test_stream_keeps_system_prompt_and_history(provider) -> None:
    chunks = [chunk async for chunk in provider.stream_chat(MESSAGES)]

    model = FakeModel.instances[-1]
    assert "".join(chunks) == "Hello"
    assert model.system_instruction == "Answer in Amharic. Context: guideline text"
    assert model.calls[0]["stream"] is True
    assert len(model.calls[0]["contents"]) == 3


@pytest.mark.asyncio
async def test_embed_batches_and_sets_task_type(provider, monkeypatch) -> None:
    calls = []

    async def fake_embed_content_async(**kwargs):
        calls.append(kwargs)
        return {"embedding": [[0.1, 0.2], [0.3, 0.4]]}

    monkeypatch.setattr(gemini.genai, "embed_content_async", fake_embed_content_async)

    vectors = await provider.embed(["chunk one", "chunk two"], input_type="document")

    assert vectors == [[0.1, 0.2], [0.3, 0.4]]
    assert len(calls) == 1
    assert calls[0]["content"] == ["chunk one", "chunk two"]
    assert calls[0]["task_type"] == "retrieval_document"


@pytest.mark.asyncio
async def test_embed_query_task_type_and_empty_input(provider, monkeypatch) -> None:
    calls = []

    async def fake_embed_content_async(**kwargs):
        calls.append(kwargs)
        return {"embedding": [[1.0]]}

    monkeypatch.setattr(gemini.genai, "embed_content_async", fake_embed_content_async)

    assert await provider.embed([]) == []
    await provider.embed(["question"], input_type="query")

    assert len(calls) == 1
    assert calls[0]["task_type"] == "retrieval_query"
