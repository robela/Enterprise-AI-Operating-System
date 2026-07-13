"""Base agent interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentContext:
    user_query: str
    tenant_id: str
    user_id: str
    conversation_history: list[dict] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    require_human_approval: bool = False


@dataclass
class AgentResult:
    answer: str
    sources: list[str] = field(default_factory=list)
    confidence: float = 1.0
    requires_human_review: bool = False
    agent_name: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    agent_name: str = "base"

    @abstractmethod
    async def run(self, context: AgentContext) -> AgentResult: ...
