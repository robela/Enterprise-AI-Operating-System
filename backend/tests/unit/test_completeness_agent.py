from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.ai.agents.base_agent import AgentContext
from backend.ai.agents.completeness_agent import CompletenessAgent, has_danger_sign
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

LETHARGIC_QUESTION = "Child is lethargic what should I do"


@pytest.mark.asyncio
async def test_lethargic_child_routes_to_completeness() -> None:
    intent = await OrchestratorAgent()._classify_intent(
        AgentContext(user_query=LETHARGIC_QUESTION, tenant_id="tenant-danger", user_id="user-1")
    )

    assert intent == "completeness"


@pytest.mark.asyncio
async def test_danger_sign_asks_the_built_in_checklist(db_session) -> None:
    # No approved workflows exist for this tenant; the built-in rule still applies.
    session_factory = async_sessionmaker(db_session.bind, class_=AsyncSession, expire_on_commit=False)

    result = await CompletenessAgent(session_factory=session_factory).run(
        AgentContext(user_query=LETHARGIC_QUESTION, tenant_id="tenant-danger", user_id="user-1")
    )

    assert result.agent_name == "completeness"
    assert result.requires_human_review is True
    assert result.metadata["workflow_id"] == "builtin:danger-signs"
    assert result.metadata["missing_fields"] == [
        "child_age",
        "other_danger_signs",
        "symptom_assessment",
        "child_weight",
    ]
    answer = result.answer.lower()
    assert "other general danger signs" in answer
    assert "cough, diarrhoea, malnutrition, and ear problems" in answer
    assert "weight (kg)" in answer and "drug dose" in answer


@pytest.mark.asyncio
async def test_danger_sign_checklist_accepts_follow_up_form_answers(db_session) -> None:
    session_factory = async_sessionmaker(db_session.bind, class_=AsyncSession, expire_on_commit=False)
    form_answer = (
        "Child's age (years): 2. Other danger signs: No other danger signs. "
        "Cough, diarrhoea, malnutrition, ear problems: none found. Child's weight (kg): 11.5"
    )

    intent = await OrchestratorAgent()._classify_intent(
        AgentContext(user_query=form_answer, tenant_id="tenant-danger", user_id="user-1")
    )
    result = await CompletenessAgent(session_factory=session_factory).run(
        AgentContext(
            user_query=form_answer,
            tenant_id="tenant-danger",
            user_id="user-1",
            conversation_history=[{"role": "user", "content": LETHARGIC_QUESTION}],
        )
    )

    assert intent == "completeness"
    assert result.metadata["missing_fields"] == []
    assert "all details in the danger-sign checklist are present" in result.answer.lower()


@pytest.mark.asyncio
async def test_partial_answers_only_ask_for_what_is_missing(db_session) -> None:
    session_factory = async_sessionmaker(db_session.bind, class_=AsyncSession, expire_on_commit=False)

    result = await CompletenessAgent(session_factory=session_factory).run(
        AgentContext(
            user_query="The 3 year old child is lethargic and has cough, weighs 12 kg",
            tenant_id="tenant-danger",
            user_id="user-1",
        )
    )

    assert result.metadata["missing_fields"] == ["other_danger_signs"]


def test_negated_danger_signs_do_not_trigger_the_rule() -> None:
    assert has_danger_sign("Child is lethargic")
    assert has_danger_sign("the child is not able to drink")
    assert not has_danger_sign("child has cough, no convulsions")
    assert not has_danger_sign("child is not lethargic")
    assert not has_danger_sign("child has fever without any convulsions")


@pytest.mark.asyncio
async def test_new_case_after_danger_sign_uses_approved_workflow(db_session) -> None:
    session_factory = async_sessionmaker(db_session.bind, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        now = datetime.now(timezone.utc)
        session.add(ExtractedWorkflowModel(
            workflow_id="workflow-after-danger", tenant_id="tenant-after-danger", document_id="document-imci",
            name="Child assessment", workflow_type="assessment", steps=[],
            required_fields=["child_age", "immunization_status"], source_pages=[15],
            source_excerpt="", confidence="high", status="approved", created_at=now, updated_at=now,
        ))
        await session.commit()

    result = await CompletenessAgent(session_factory=session_factory).run(
        AgentContext(
            user_query="3 years of child has cough",
            tenant_id="tenant-after-danger",
            user_id="user-1",
            conversation_history=[
                {"role": "user", "content": LETHARGIC_QUESTION},
                {"role": "user", "content": "3 years of child has cough"},
            ],
        )
    )

    assert result.metadata["workflow_id"] == "workflow-after-danger"


@pytest.mark.asyncio
async def test_checklist_form_answer_continues_the_danger_sign_case(db_session) -> None:
    session_factory = async_sessionmaker(db_session.bind, class_=AsyncSession, expire_on_commit=False)

    result = await CompletenessAgent(session_factory=session_factory).run(
        AgentContext(
            user_query="Child's age (years): 2",
            tenant_id="tenant-danger",
            user_id="user-1",
            conversation_history=[
                {"role": "user", "content": LETHARGIC_QUESTION},
                {"role": "user", "content": "Child's age (years): 2"},
            ],
        )
    )

    assert result.metadata["workflow_id"] == "builtin:danger-signs"
    assert "child_age" not in result.metadata["missing_fields"]


@pytest.mark.asyncio
async def test_earlier_case_facts_do_not_answer_a_new_question(db_session) -> None:
    session_factory = async_sessionmaker(db_session.bind, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        now = datetime.now(timezone.utc)
        session.add(ExtractedWorkflowModel(
            workflow_id="workflow-new-case", tenant_id="tenant-new-case", document_id="document-imci",
            name="Child assessment", workflow_type="assessment", steps=[],
            required_fields=["child_age", "immunization_status"], source_pages=[15],
            source_excerpt="", confidence="high", status="approved", created_at=now, updated_at=now,
        ))
        await session.commit()

    result = await CompletenessAgent(session_factory=session_factory).run(
        AgentContext(
            user_query="Another child has cough",
            tenant_id="tenant-new-case",
            user_id="user-1",
            conversation_history=[
                {"role": "user", "content": "A 3 year old child has fever"},
                {"role": "user", "content": "Immunization status: Up to date"},
                {"role": "user", "content": "Another child has cough"},
            ],
        )
    )

    assert result.metadata["missing_fields"] == ["child_age", "immunization_status"]
