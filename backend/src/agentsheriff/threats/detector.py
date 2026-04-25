from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from agentsheriff.models.dto import Decision, PolicyVersionDTO, ToolCallRequest


@dataclass(frozen=True)
class ThreatReport:
    risk_score: int
    signals: list[str]

    def summary(self) -> dict[str, Any]:
        return {"risk_score": self.risk_score, "signals": self.signals}


@dataclass(frozen=True)
class JudgeResult:
    decision: Decision
    rationale: str
    user_explanation: str | None
    risk_score: int


def detect_threats(request: ToolCallRequest) -> ThreatReport:
    blob = json.dumps({"tool": request.tool, "args": request.args, "context": request.context.model_dump()}, default=str).lower()
    signals: list[str] = []
    risk = 10
    if "outlaw" in blob or "exfiltrat" in blob or "ignore previous" in blob:
        signals.append("prompt_injection_or_exfiltration")
        risk = max(risk, 85)
    if request.tool == "github.push_branch" and request.args.get("force") is True:
        signals.append("destructive_git_operation")
        risk = max(risk, 80)
    if request.tool == "gmail.send_email" and request.args.get("attachments"):
        signals.append("email_with_attachment")
        risk = max(risk, 55)
    return ThreatReport(risk_score=risk, signals=signals)


def judge_tool_call(policy: PolicyVersionDTO, request: ToolCallRequest, threat_report: ThreatReport) -> JudgeResult:
    _ = policy
    if threat_report.risk_score >= 80:
        return JudgeResult(
            decision=Decision.deny,
            rationale="Stub judge denied a high-risk tool call.",
            user_explanation="This action looks risky based on the current threat signals.",
            risk_score=threat_report.risk_score,
        )
    return JudgeResult(
        decision=Decision.allow,
        rationale="Stub judge allowed a low-risk tool call.",
        user_explanation=None,
        risk_score=threat_report.risk_score,
    )
