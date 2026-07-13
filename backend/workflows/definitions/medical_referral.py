"""Medical referral workflow definition."""
from backend.domains.workflow.domain.entities.workflow import Workflow, WorkflowTask
import uuid


def create_medical_referral_workflow(
    tenant_id: str,
    initiator_id: str,
    patient_id: str,
    specialist_type: str,
) -> Workflow:
    """
    Medical Referral Workflow:
    1. AI Pre-screening (automated)
    2. Primary Doctor Review (human)
    3. Insurance Authorization (human)
    4. Specialist Booking Confirmation (automated)
    """
    wf = Workflow.create(
        tenant_id=tenant_id,
        definition_id="medical_referral_v1",
        name=f"Medical Referral — {specialist_type}",
        initiator_id=initiator_id,
        context={"patient_id": patient_id, "specialist_type": specialist_type},
    )

    wf.tasks = [
        WorkflowTask(
            task_id=str(uuid.uuid4()),
            name="AI Pre-screening",
            task_type="ai_decision",
            input_data={"patient_id": patient_id, "specialist_type": specialist_type},
        ),
        WorkflowTask(
            task_id=str(uuid.uuid4()),
            name="Primary Doctor Review",
            task_type="human_approval",
        ),
        WorkflowTask(
            task_id=str(uuid.uuid4()),
            name="Insurance Authorization",
            task_type="human_approval",
        ),
        WorkflowTask(
            task_id=str(uuid.uuid4()),
            name="Specialist Booking Confirmation",
            task_type="automated",
        ),
    ]

    return wf
