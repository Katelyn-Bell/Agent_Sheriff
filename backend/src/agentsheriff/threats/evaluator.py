from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class DisagreementCategory(StrEnum):
    more_permissive = "more_permissive"
    more_restrictive = "more_restrictive"
    reason_changed = "reason_changed"
    approval_vs_direct = "approval_vs_direct"
    error = "error"


@dataclass(frozen=True)
class EvalComparisonResult:
    agreement: bool
    replay_reason: str
    disagreement_category: DisagreementCategory | None = None


def compare_replayed_decision(audit_entry: Any, replay_outcome: Any) -> EvalComparisonResult:
    original = _get(audit_entry, "decision")
    replayed = _get(replay_outcome, "decision") or _get(replay_outcome, "replayed_decision")
    original_reason = str(_get(audit_entry, "reason") or "")
    replay_reason = str(_get(replay_outcome, "reason") or _get(replay_outcome, "replay_reason") or "")

    if _get(replay_outcome, "error"):
        return EvalComparisonResult(False, replay_reason or "Replay errored.", DisagreementCategory.error)
    if original == replayed and original_reason == replay_reason:
        return EvalComparisonResult(True, replay_reason or "Replay matched the original decision.")
    if original == replayed:
        return EvalComparisonResult(False, replay_reason or "Decision matched but rationale changed.", DisagreementCategory.reason_changed)
    normalized_decisions = {_normalize(original), _normalize(replayed)}
    if any("approval" in decision for decision in normalized_decisions):
        return EvalComparisonResult(False, replay_reason or "Replay changed approval handling.", DisagreementCategory.approval_vs_direct)
    if _rank(replayed) > _rank(original):
        return EvalComparisonResult(False, replay_reason or "Replay is more permissive than the original.", DisagreementCategory.more_permissive)
    return EvalComparisonResult(False, replay_reason or "Replay is more restrictive than the original.", DisagreementCategory.more_restrictive)


def _get(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        return value.get(key)
    return getattr(value, key, None)


def _rank(value: Any) -> int:
    return {"deny": 0, "approval_required": 1, "require_approval": 1, "allow": 2}.get(_normalize(value), -1)


def _normalize(value: Any) -> str:
    return str(getattr(value, "value", value))
