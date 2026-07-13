"""AI background worker tasks."""
import asyncio
import structlog

from backend.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="backend.workers.ai_worker.run_agent_task", bind=True, max_retries=2)
def run_agent_task(self, tenant_id: str, user_id: str, query: str, workflow_id: str | None = None):
    """Run an AI agent task asynchronously and optionally advance a workflow."""
    try:
        result = asyncio.run(_run_agent(tenant_id, user_id, query))
        if workflow_id:
            logger.info("ai_task_completed", workflow_id=workflow_id, answer_length=len(result))
        return result
    except Exception as exc:
        logger.error("ai_task_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=30)


async def _run_agent(tenant_id: str, user_id: str, query: str) -> str:
    from backend.ai.orchestration.orchestrator import OrchestratorAgent
    from backend.ai.agents.base_agent import AgentContext

    orchestrator = OrchestratorAgent()
    context = AgentContext(user_query=query, tenant_id=tenant_id, user_id=user_id)
    result = await orchestrator.run(context)
    return result.answer
