"""Chat endpoint: completeness results carry the data the follow-up form needs."""
import pytest

from backend.ai.agents.base_agent import AgentResult
from backend.ai.multilingual import QueryAnalysis
from backend.api.rest import ai_router
from backend.core.security.jwt import create_access_token
from fakes import FakeProvider


def _headers() -> dict[str, str]:
    token = create_access_token(
        "user-chat-cmp",
        extra_claims={"tenant_id": "tenant-chat-cmp", "roles": ["user"], "scopes": ["users:read"]},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_chat_returns_missing_fields_for_the_form(client, monkeypatch) -> None:
    async def fake_analyze_query(question, provider, requested_language=None):
        return QueryAnalysis(language="en", english_query=None, source="heuristic")

    class FakeOrchestrator:
        async def run(self, context):
            return AgentResult(
                answer="## Missing information",
                sources=["document-imci"],
                agent_name="completeness",
                requires_human_review=True,
                metadata={
                    "workflow_id": "workflow-19",
                    "missing_fields": ["child_age", "immunization_status"],
                    "source_pages": [19],
                    "used_translated_input": False,
                },
            )

    monkeypatch.setattr(ai_router, "get_provider", lambda: FakeProvider())
    monkeypatch.setattr(ai_router, "analyze_query", fake_analyze_query)
    monkeypatch.setattr(ai_router, "OrchestratorAgent", FakeOrchestrator)

    response = await client.post(
        "/api/v1/ai/chat", headers=_headers(), json={"message": "child has cough"}
    )

    expected = {
        "workflow_id": "workflow-19",
        "missing_fields": ["child_age", "immunization_status"],
        "source_pages": [19],
    }
    assert response.status_code == 200
    assert response.json()["completeness"] == expected

    # Reopening the conversation must bring the form back.
    conversation_id = response.json()["conversation_id"]
    history = await client.get(f"/api/v1/ai/chat/conversations/{conversation_id}", headers=_headers())

    assert history.status_code == 200
    assistant = [m for m in history.json()["messages"] if m["role"] == "assistant"]
    assert assistant[-1]["citations"]["completeness"] == expected
    assert assistant[-1]["citations"]["sources"] == ["document-imci"]
