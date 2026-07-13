"""Prompt version registry."""
from __future__ import annotations
from typing import Any


_PROMPTS: dict[str, dict[str, str]] = {
    "rag_system_v1": {
        "template": (
            "You are a helpful enterprise AI assistant. "
            "Answer questions using the context below.\n\n"
            "Context:\n{context}\n\n"
            "Rules:\n"
            "- Cite sources with [Source: document_id].\n"
            "- If the answer is not in the context, say 'I don't have that information'.\n"
            "- Be concise and accurate."
        ),
        "version": "1",
    },
    "validation_system_v1": {
        "template": (
            "You are a validation expert. Check the input for correctness and compliance. "
            "Return JSON: {{\"valid\": bool, \"issues\": [str], \"suggestions\": [str]}}"
        ),
        "version": "1",
    },
}


class PromptRegistry:
    def get(self, prompt_id: str, variables: dict[str, Any] | None = None) -> str:
        entry = _PROMPTS.get(prompt_id)
        if not entry:
            raise KeyError(f"Prompt {prompt_id!r} not found in registry")
        template = entry["template"]
        if variables:
            return template.format(**variables)
        return template

    def register(self, prompt_id: str, template: str, version: str = "1") -> None:
        _PROMPTS[prompt_id] = {"template": template, "version": version}


prompt_registry = PromptRegistry()
