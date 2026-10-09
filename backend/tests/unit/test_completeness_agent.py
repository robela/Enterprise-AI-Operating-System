from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.ai.agents.base_agent import AgentContext
from backend.ai.agents.completeness_agent import CompletenessAgent
from backend.ai.orchestration.orchestrator import OrchestratorAgent
from backend.infrastructure.persistence.models import ExtractedWorkflowModel


@pytest.mark.asyncio
async def test_completeness_agent_reports_missing_approved_fields(db_session) -> None:
    session_factory = async_sessionmaker(db_session.bind, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        session.add(
            ExtractedWorkflowModel(
                workflow_id="workflow-completeness-agent",
                tenant_id="tenant-completeness-agent",
                document_id="document-imci",
                name="Assess sick child",
                workflow_type="assessment",
                steps=[],
                required_fields=["child_age", "main_symptoms", "immunization_status"],
                source_pages=[15],
                source_excerpt="",
                confidence="high",
                status="approved",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()

    result = await CompletenessAgent(session_factory=session_factory).run(
        AgentContext(
            user_query="Check missing questions: the child is 3 years old and has fever.",
            tenant_id="tenant-completeness-agent",
            user_id="user-1",
        )
    )

    assert result.agent_name == "completeness"
    assert "immunization status" in result.answer.lower()
    assert "child's age" not in result.answer.lower()
    assert result.metadata["source_pages"] == [15]


@pytest.mark.asyncio
async def test_completeness_agent_prefers_workflow_matching_case_facts(db_session) -> None:
    session_factory = async_sessionmaker(db_session.bind, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        now = datetime.now(timezone.utc)
        session.add_all([
            ExtractedWorkflowModel(
                workflow_id="workflow-nutrition", tenant_id="tenant-match", document_id="document-imci",
                name="Nutrition review", workflow_type="assessment", steps=[], required_fields=["nutrition_status"],
                source_pages=[58], source_excerpt="", confidence="high", status="approved", created_at=now, updated_at=now,
            ),
            ExtractedWorkflowModel(
                workflow_id="workflow-general", tenant_id="tenant-match", document_id="document-imci",
                name="General sick child", workflow_type="assessment", steps=[], required_fields=["child_age", "main_symptoms", "immunization_status"],
                source_pages=[15], source_excerpt="", confidence="high", status="approved", created_at=now, updated_at=now,
            ),
        ])
        await session.commit()

    result = await CompletenessAgent(session_factory=session_factory).run(
        AgentContext(user_query="Check missed questions: child is 3 years old with fever.", tenant_id="tenant-match", user_id="user-1")
    )

    assert result.metadata["workflow_id"] == "workflow-general"
    assert result.metadata["source_pages"] == [15]


@pytest.mark.asyncio
async def test_completeness_agent_recognizes_age_without_old(db_session) -> None:
    session_factory = async_sessionmaker(db_session.bind, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        now = datetime.now(timezone.utc)
        session.add(ExtractedWorkflowModel(
            workflow_id="workflow-age", tenant_id="tenant-age", document_id="document-imci",
            name="Child assessment", workflow_type="assessment", steps=[],
            required_fields=["child_age", "immunization_status"], source_pages=[15],
            source_excerpt="", confidence="high", status="approved", created_at=now, updated_at=now,
        ))
        await session.commit()

    result = await CompletenessAgent(session_factory=session_factory).run(
        AgentContext(user_query="3 years of child has cough", tenant_id="tenant-age", user_id="user-1")
    )

    assert "child's age" not in result.answer.lower()
    assert "immunization status" in result.answer.lower()


@pytest.mark.asyncio
async def test_orchestrator_routes_child_symptom_case_to_completeness() -> None:
    orchestrator = OrchestratorAgent()
    intent = await orchestrator._classify_intent(
        AgentContext(user_query="3 years of child has cough", tenant_id="tenant-age", user_id="user-1")
    )

    assert intent == "completeness"


@pytest.mark.asyncio
async def test_orchestrator_routes_clinical_follow_up_to_completeness() -> None:
    orchestrator = OrchestratorAgent()
    intent = await orchestrator._classify_intent(
        AgentContext(
            user_query="Nutrition or feeding status: Eating and drinking normally",
            tenant_id="tenant-age",
            user_id="user-1",
        )
    )

    assert intent == "completeness"