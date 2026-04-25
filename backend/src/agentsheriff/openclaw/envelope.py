from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class OpenClawCallEnvelope(BaseModel):
    """Tolerant model for OpenClaw outbound tool-call payloads.

    The real OpenClaw shape is captured as demo fixtures over time; this model
    deliberately keeps unknown fields so the translator can inspect nested
    variants without rejecting useful payloads.
    """

    id: str | None = None
    call_id: str | None = None
    task_id: str | None = None
    conversation_id: str | None = None
    prompt: str | None = None
    source_prompt: str | None = None
    source_content: str | None = None
    tool: str | None = None
    tool_name: str | None = None
    name: str | None = None
    args: dict[str, Any] | None = None
    arguments: dict[str, Any] | str | None = None
    input: dict[str, Any] | str | None = None
    context: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "allow"}


class OpenClawToolCallResult(BaseModel):
    ok: bool
    decision: str
    reason: str
    blocked: bool
    approval_required: bool
    audit_id: str
    approval_id: str | None = None
    result: dict[str, Any] | None = None
    agentsheriff: dict[str, Any]
