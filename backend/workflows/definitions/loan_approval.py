"""Loan approval workflow definition."""
from backend.domains.workflow.domain.entities.workflow import Workflow, WorkflowTask
import uuid


def create_loan_approval_workflow(
    tenant_id: str,
    initiator_id: str,
    loan_amount: float,
    applicant_name: str,
) -> Workflow:
    """
    Loan Approval Workflow:
    1. AI Risk Assessment (automated)
    2. Manager Approval (human)
    3. Compliance Review (human, if amount > 50k)
    4. Final Decision (automated)
    """
    wf = Workflow.create(
        tenant_id=tenant_id,
        definition_id="loan_approval_v1",
        name=f"Loan Approval — {applicant_name}",
        initiator_id=initiator_id,
        context={"loan_amount": loan_amount, "applicant_name": applicant_name},
    )

    wf.tasks = [
        WorkflowTask(
            task_id=str(uuid.uuid4()),
            name="AI Risk Assessment",
            task_type="ai_decision",
            input_data={"loan_amount": loan_amount, "applicant": applicant_name},
        ),
        WorkflowTask(
            task_id=str(uuid.uuid4()),
            name="Manager Approval",
            task_type="human_approval",
        ),
    ]

    if loan_amount > 50_000:
        wf.tasks.append(
            WorkflowTask(
                task_id=str(uuid.uuid4()),
                name="Compliance Review",
                task_type="human_approval",
            )
        )

    wf.tasks.append(
        WorkflowTask(
            task_id=str(uuid.uuid4()),
            name="Final Decision",
            task_type="automated",
        )
    )

    return wf
