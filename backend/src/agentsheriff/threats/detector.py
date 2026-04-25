from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from urllib.parse import urlparse

from agentsheriff.models.dto import Decision, PolicyVersionDTO, ToolCallRequest


class JudgeDecision(StrEnum):
    allow = "allow"
    deny = "deny"
    require_approval = "require_approval"


@dataclass(frozen=True)
class ThreatSignal:
    name: str
    score: int
    detail: str
    evidence: str | None = None


@dataclass(frozen=True)
class ThreatReport:
    signals: list[ThreatSignal] = field(default_factory=list)
    aggregate_score: int = 10
    summary: str = "No notable threat signals detected."
    recommended_floor: int = 10

    @property
    def risk_score(self) -> int:
        return self.aggregate_score

    def as_dict(self) -> dict[str, Any]:
        return {
            "risk_score": self.aggregate_score,
            "aggregate_score": self.aggregate_score,
            "signals": [signal.name for signal in self.signals],
            "signal_details": [signal.__dict__ for signal in self.signals],
            "summary": self.summary,
            "recommended_floor": self.recommended_floor,
        }


@dataclass(frozen=True)
class JudgeResult:
    decision: Decision
    rationale: str
    user_explanation: str | None
    risk_score: int
    severity_recommendation: int | None = None


SENSITIVE_FILE_RE = re.compile(
    r"(?i)(salary|passport|payroll|confidential|invoice|employees|customers|"
    r"ssn|tax_return|credentials|secret|private[_-]?key)",
)

PROMPT_INJECTION_RE = re.compile(
    r"(ignore (all )?(previous|prior|above) instructions|system prompt|developer message|"
    r"jailbreak|prompt injection|exfiltrat|send.*secret|leak.*(secret|token|key))",
    re.IGNORECASE,
)
CREDENTIAL_RE = re.compile(
    r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token|bearer\s+[a-z0-9._\-]+|"
    r"password\s*[:=]|-----BEGIN [A-Z ]*PRIVATE KEY-----)"
)
SENSITIVE_PATH_RE = re.compile(
    r"(?i)(^|/)(\.env|id_rsa|id_ed25519|credentials|secrets?|private[_-]?key|"
    r"token|passwd|shadow|\.aws|\.ssh)(/|$|\.)"
)
DESTRUCTIVE_SHELL_RE = re.compile(
    r"(?i)(\brm\s+-[^\n;|&]*[rf]|mkfs\.|dd\s+if=.*\bof=|chmod\s+-R\s+777|"
    r"curl\b.*\|\s*(sh|bash)|wget\b.*\|\s*(sh|bash)|sudo\s+rm)"
)
GIT_REWRITE_RE = re.compile(r"(?i)(--force|-f\b|push\s+.*\+|reset\s+--hard|rebase\s+-i)")
URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)

SENSITIVE_EXTENSIONS = {".key", ".pem", ".p12", ".pfx", ".kdbx", ".env", ".sqlite", ".db"}
SENSITIVE_NAMES = {"credentials", "secrets", "secret", "tokens", "passwords", "payroll", "ssn", "tax"}
SAFE_DOMAINS = {"example.com", "localhost", "127.0.0.1", "company.internal", "internal.example.com"}


def detect_threats(request: Any) -> ThreatReport:
    try:
        tool = _safe_tool(request)
        args = _safe_mapping(getattr(request, "args", {}))
        context = _safe_context(getattr(request, "context", {}))
        blob = _json_blob({"tool": tool, "args": args, "context": context})

        signals: list[ThreatSignal] = []
        _append_prompt_injection(signals, blob)
        _append_external_recipient(signals, tool, args)
        _append_sensitive_attachment(signals, args)
        _append_sensitive_path(signals, args, blob)
        _append_bulk_exfiltration(signals, tool, args, blob)
        _append_destructive_shell(signals, tool, args, blob)
        _append_git_rewrite(signals, tool, args, blob)
        _append_credential_material(signals, blob)
        _append_untrusted_url(signals, blob)

        score = _aggregate(signals)
        return ThreatReport(
            signals=signals,
            aggregate_score=score,
            summary=_summarize(signals),
            recommended_floor=_recommended_floor(score),
        )
    except Exception as exc:  # pragma: no cover - defensive malformed-input guarantee
        signal = ThreatSignal(
            name="malformed_request",
            score=40,
            detail="Threat detector could not fully parse this request.",
            evidence=str(exc)[:120],
        )
        return ThreatReport(signals=[signal], aggregate_score=40, summary=signal.detail, recommended_floor=40)


def judge_tool_call(policy: PolicyVersionDTO, request: ToolCallRequest, threat_report: ThreatReport) -> JudgeResult:
    _ = policy, request
    if threat_report.aggregate_score >= 80:
        return JudgeResult(
            decision=Decision.deny,
            rationale=f"Deterministic judge fallback denied high-risk request: {threat_report.summary}",
            user_explanation="This action matched high-risk safety signals and was blocked.",
            risk_score=threat_report.aggregate_score,
            severity_recommendation=threat_report.recommended_floor,
        )
    if threat_report.aggregate_score >= 55:
        return JudgeResult(
            decision=Decision.approval_required,
            rationale=f"Deterministic judge fallback requires approval: {threat_report.summary}",
            user_explanation="This action has risk signals that need human review before continuing.",
            risk_score=threat_report.aggregate_score,
            severity_recommendation=threat_report.recommended_floor,
        )
    return JudgeResult(
        decision=Decision.allow,
        rationale="Deterministic judge fallback allowed a low-risk tool call.",
        user_explanation=None,
        risk_score=threat_report.aggregate_score,
        severity_recommendation=threat_report.recommended_floor,
    )


def _append_prompt_injection(signals: list[ThreatSignal], blob: str) -> None:
    if match := PROMPT_INJECTION_RE.search(blob):
        signals.append(ThreatSignal("prompt_injection", 85, "Text resembles prompt injection or exfiltration instructions.", match.group(0)))


def _append_external_recipient(signals: list[ThreatSignal], tool: str, args: dict[str, Any]) -> None:
    recipients = _flatten([args.get(key) for key in ("to", "cc", "bcc", "recipient", "recipients", "email")])
    external = [value for value in recipients if isinstance(value, str) and "@" in value and not value.lower().endswith("@example.com")]
    if tool.endswith("send_email") and external:
        signals.append(ThreatSignal("external_recipient", 45, "Outbound message targets an external recipient.", external[0]))


def _append_sensitive_attachment(signals: list[ThreatSignal], args: dict[str, Any]) -> None:
    attachments = [str(item).lower() for item in _flatten(args.get("attachments", []))]
    for attachment in attachments:
        if any(attachment.endswith(ext) for ext in SENSITIVE_EXTENSIONS) or any(name in attachment for name in SENSITIVE_NAMES):
            signals.append(ThreatSignal("sensitive_attachment", 65, "Attachment name suggests sensitive material.", attachment))
            return


def _append_sensitive_path(signals: list[ThreatSignal], args: dict[str, Any], blob: str) -> None:
    path_candidates = _flatten([args.get(key) for key in ("path", "paths", "file", "files", "filepath", "cwd")])
    for candidate in path_candidates:
        if isinstance(candidate, str) and SENSITIVE_PATH_RE.search(candidate):
            signals.append(ThreatSignal("sensitive_path", 70, "Tool arguments reference a sensitive filesystem path.", candidate))
            return
    if match := SENSITIVE_PATH_RE.search(blob):
        signals.append(ThreatSignal("sensitive_path", 70, "Request text references a sensitive filesystem path.", match.group(0)))


def _append_bulk_exfiltration(signals: list[ThreatSignal], tool: str, args: dict[str, Any], blob: str) -> None:
    count = args.get("count") or args.get("limit") or args.get("max_results")
    many_items = isinstance(count, int) and count >= 100
    archive = any(token in blob for token in ("zip", "tar", "archive", "all files", "entire inbox", "export"))
    send_or_upload = any(token in tool for token in ("send", "upload", "post")) or any(key in args for key in ("url", "to", "destination"))
    if send_or_upload and (many_items or archive):
        signals.append(ThreatSignal("bulk_exfiltration_pattern", 75, "Request resembles bulk collection followed by transfer."))


def _append_destructive_shell(signals: list[ThreatSignal], tool: str, args: dict[str, Any], blob: str) -> None:
    command = str(args.get("cmd") or args.get("command") or blob)
    if ("shell" in tool or "terminal" in tool or "exec" in tool) and (match := DESTRUCTIVE_SHELL_RE.search(command)):
        signals.append(ThreatSignal("destructive_shell", 90, "Shell command appears destructive or unsafe.", match.group(0)))


def _append_git_rewrite(signals: list[ThreatSignal], tool: str, args: dict[str, Any], blob: str) -> None:
    if ("git" in tool or "github" in tool) and (args.get("force") is True or GIT_REWRITE_RE.search(blob)):
        signals.append(ThreatSignal("git_history_rewrite", 82, "Git operation appears to rewrite published history."))


def _append_credential_material(signals: list[ThreatSignal], blob: str) -> None:
    if match := CREDENTIAL_RE.search(blob):
        signals.append(ThreatSignal("credential_like_material", 88, "Request contains credential-like material.", match.group(0)))


def _append_untrusted_url(signals: list[ThreatSignal], blob: str) -> None:
    for url in URL_RE.findall(blob):
        host = (urlparse(url).hostname or "").lower()
        if host and host not in SAFE_DOMAINS and not host.endswith(".example.com"):
            signals.append(ThreatSignal("untrusted_url", 42, "Request references a URL outside the trusted demo domains.", url[:160]))
            return


def _aggregate(signals: list[ThreatSignal]) -> int:
    if not signals:
        return 10
    score = max(signal.score for signal in signals)
    score += min(15, max(0, len(signals) - 1) * 5)
    return min(100, score)


def _recommended_floor(score: int) -> int:
    if score >= 80:
        return 80
    if score >= 55:
        return 55
    if score >= 40:
        return 40
    return 10


def _summarize(signals: list[ThreatSignal]) -> str:
    if not signals:
        return "No notable threat signals detected."
    names = ", ".join(signal.name for signal in signals)
    return f"Detected {len(signals)} threat signal(s): {names}."


def _safe_tool(request: Any) -> str:
    return str(getattr(request, "tool", "") or "")


def _safe_mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_context(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        dumped = value.model_dump(mode="json")
        return dumped if isinstance(dumped, dict) else {}
    return value if isinstance(value, dict) else {}


def _json_blob(value: Any) -> str:
    return json.dumps(value, default=str, sort_keys=True).lower()


def _flatten(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (str, bytes)):
        return [value.decode() if isinstance(value, bytes) else value]
    if isinstance(value, dict):
        return list(value.values())
    if isinstance(value, (list, tuple, set)):
        flattened: list[Any] = []
        for item in value:
            flattened.extend(_flatten(item))
        return flattened
    return [value]
