"""Workflow entity — BPMN-inspired workflow engine."""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_HUMAN = "awaiting_human"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"


@dataclass
class WorkflowTask:
    task_id: str
    name: str
    task_type: str  # human_approval | automated | ai_decision
    status: TaskStatus = TaskStatus.PENDING
    assignee_id: str | None = None
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    comments: str = ""

    def start(self) -> None:
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.now(timezone.utc)

    def complete(self, output_data: dict | None = None) -> None:
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        if output_data:
            self.output_data = output_data

    def reject(self, comments: str = "") -> None:
        self.status = TaskStatus.REJECTED
        self.comments = comments
        self.completed_at = datetime.now(timezone.utc)

    def request_human(self, assignee_id: str) -> None:
        self.status = TaskStatus.AWAITING_HUMAN
        self.assignee_id = assignee_id


@dataclass
class Workflow:
    workflow_id: str
    tenant_id: str
    definition_id: str
    name: str
    initiator_id: str
    status: WorkflowStatus = WorkflowStatus.ACTIVE
    tasks: list[WorkflowTask] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None

    @classmethod
    def create(
        cls,
        tenant_id: str,
        definition_id: str,
        name: str,
        initiator_id: str,
        context: dict | None = None,
    ) -> Workflow:
        return cls(
            workflow_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            definition_id=definition_id,
            name=name,
            initiator_id=initiator_id,
            context=context or {},
        )

    @property
    def current_task(self) -> WorkflowTask | None:
        for task in self.tasks:
            if task.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.AWAITING_HUMAN):
                return task
        return None

    def complete(self) -> None:
        self.status = WorkflowStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.updated_at = self.completed_at

    def cancel(self) -> None:
        self.status = WorkflowStatus.CANCELLED
        self.updated_at = datetime.now(timezone.utc)
