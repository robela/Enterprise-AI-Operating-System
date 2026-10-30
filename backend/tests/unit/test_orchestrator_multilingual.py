"""Routing and answer localization for non-English questions."""
import pytest

from backend.ai.agents.base_agent import AgentContext, AgentResult
from backend.ai.orchestration import orchestrator as orchestrator_module
from backend.ai.orchestration.orchestrator import OrchestratorAgent
from fakes import FakeProvider

AMHARIC_CASE = "ልጁ የሦስት ዓመት ልጅ ሲሆን ሳል አለበት"


def _context(user_query: str, **metadata) -> AgentContext:
    return AgentContext(user_query=user_query, tenant_id="tenant-ml", user_id="user-1", metadata=metadata)


@pytest.mark.asyncio
async def test_translated_child_symptom_case_routes_to_completeness() -> None:
    intent = await OrchestratorAgent()._classify_intent(
        _context(AMHARIC_CASE, english_query="The child is three years old and has a cough.")
    )

    assert intent == "completeness"


@pytest.mark.asyncio
async def test_untranslated_non_english_question_routes_to_knowledge() -> None:
    intent = await OrchestratorAgent()._classify_intent(_context(AMHARIC_CASE))

    assert intent == "knowledge"


@pytest.mark.asyncio
async def test_completeness_answer_is_localized_with_english_original(monkeypatch) -> None:
    monkeypatch.setattr(
        orchestrator_module,
        "get_provider",
        lambda: FakeProvider(replies=["## የጎደለ መረጃ\n\n- የልጁ ክትባት ሁኔታ ምንድን ነው?"]),
    )
    english = "## Missing information\n\n- What is the child's immunization status?"
    result = AgentResult(answer=english, agent_name="completeness", requires_human_review=True)

    localized = await OrchestratorAgent()._localize(result, "am")

    assert localized.answer.startswith("## የጎደለ መረጃ")
    assert localized.answer.endswith(english)
    assert localized.metadata["machine_translated"] is True
    assert localized.requires_human_review is True


@pytest.mark.asyncio
async def test_english_answers_are_not_localized(monkeypatch) -> None:
    provider = FakeProvider()
    monkeypatch.setattr(orchestrator_module, "get_provider", lambda: provider)
    result = AgentResult(answer="## Missing information", agent_name="completeness")

    assert (await OrchestratorAgent()._localize(result, "en")).answer == "## Missing information"
    assert (await OrchestratorAgent()._localize(result, None)).answer == "## Missing information"
    assert provider.chat_calls == []
