from __future__ import annotations

from dataclasses import dataclass, field

from agentsheriff.models.dto import PolicyGenerationResponse


@dataclass(frozen=True)
class PolicyGenerationResult:
    intent_summary: str
    judge_prompt: str
    static_rules: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_response(self) -> PolicyGenerationResponse:
        return PolicyGenerationResponse.model_validate(self.__dict__)


def generate_starter_policy(
    user_intent: str,
    tool_manifest: list[str],
    domain_hint: str | None = None,
) -> PolicyGenerationResult:
    domain = domain_hint or "general"
    summary = f"{domain.title()} assistant policy draft for: {user_intent.strip() or 'unspecified agent work'}"
    return PolicyGenerationResult(
        intent_summary=summary,
        judge_prompt=(
            "You are a conservative security reviewer for agent tool calls. Allow clearly low-risk actions, "
            "deny credential exfiltration and destructive changes, and require approval for external sends, "
            "sensitive material, or irreversible operations."
        ),
        static_rules=[],
        notes=[
            f"Drafted for {len(tool_manifest)} manifest tool(s).",
            "Leave unmatched actions delegated to the judge by default.",
            "Review generated rules before publishing.",
        ],
    )
