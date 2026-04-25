from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from agentsheriff.models.dto import Decision, EvalResultDTO, EvalRunDTO, EvalStatus, RuleAction, ToolCallRequest
from agentsheriff.models.orm import AuditEntry, EvalResult, EvalRun
from agentsheriff.policy.engine import evaluate_static_rules
from agentsheriff.policy.store import PolicyStore, utc_iso
from agentsheriff.threats.detector import ThreatReport, judge_tool_call


class EvalStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_runs(self) -> list[EvalRunDTO]:
        rows = self.session.scalars(select(EvalRun).order_by(EvalRun.created_at.desc())).all()
        return [self.run_to_dto(row) for row in rows]

    def get_run(self, eval_id: str) -> EvalRunDTO | None:
        row = self.session.get(EvalRun, eval_id)
        return self.run_to_dto(row) if row else None

    def list_results(self, eval_id: str) -> list[EvalResultDTO]:
        rows = self.session.scalars(select(EvalResult).where(EvalResult.eval_run_id == eval_id)).all()
        return [self.result_to_dto(row) for row in rows]

    def create_and_run(self, policy_version_id: str, filters: dict[str, str]) -> EvalRunDTO:
        policy = PolicyStore(self.session).get_version(policy_version_id)
        if policy is None:
            raise KeyError(policy_version_id)

        audit_rows = self._audit_rows(filters)
        run = EvalRun(
            id=f"eval_{uuid4().hex[:12]}",
            policy_version_id=policy_version_id,
            status=EvalStatus.running.value,
            total_entries=len(audit_rows),
        )
        self.session.add(run)
        self.session.commit()

        agreed = 0
        disagreed = 0
        errored = 0
        for audit in audit_rows:
            try:
                replayed, matched_rule_id, judge_used, reason = self._replay(audit, policy)
                agreement = replayed == Decision(audit.decision)
                agreed += int(agreement)
                disagreed += int(not agreement)
                self.session.add(EvalResult(
                    id=f"er_{uuid4().hex[:12]}",
                    eval_run_id=run.id,
                    audit_id=audit.id,
                    original_decision=audit.decision,
                    replayed_decision=replayed.value,
                    matched_rule_id=matched_rule_id,
                    judge_used=judge_used,
                    replay_reason=reason,
                    agreement=agreement,
                ))
            except Exception as exc:  # pragma: no cover - defensive ledger isolation
                errored += 1
                self.session.add(EvalResult(
                    id=f"er_{uuid4().hex[:12]}",
                    eval_run_id=run.id,
                    audit_id=audit.id,
                    original_decision=audit.decision,
                    replayed_decision=Decision.deny.value,
                    matched_rule_id=None,
                    judge_used=False,
                    replay_reason=f"Replay failed: {exc}",
                    agreement=False,
                ))

            run.processed_entries += 1
            run.agreed = agreed
            run.disagreed = disagreed
            run.errored = errored
            self.session.commit()

        run.status = EvalStatus.completed.value
        run.completed_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(run)
        return self.run_to_dto(run)

    def _audit_rows(self, filters: dict[str, str]) -> list[AuditEntry]:
        statement = select(AuditEntry).order_by(AuditEntry.ts.asc())
        if agent_id := filters.get("agent_id"):
            statement = statement.where(AuditEntry.agent_id == agent_id)
        if decision := filters.get("decision"):
            statement = statement.where(AuditEntry.decision == decision)
        if policy_version_id := filters.get("policy_version_id"):
            statement = statement.where(AuditEntry.policy_version_id == policy_version_id)
        return list(self.session.scalars(statement).all())

    def _replay(self, audit: AuditEntry, policy) -> tuple[Decision, str | None, bool, str]:
        request = ToolCallRequest(
            agent_id=audit.agent_id,
            agent_label=audit.agent_label,
            tool=audit.tool,
            args=audit.args,
            context=audit.context,
        )
        heuristic = audit.heuristic_summary or {}
        threat_report = ThreatReport(
            risk_score=int(heuristic.get("risk_score", audit.risk_score)),
            signals=list(heuristic.get("signals", [])),
        )
        evaluation = evaluate_static_rules(request, policy.static_rules, base_risk_score=threat_report.risk_score)
        if evaluation.action == RuleAction.allow:
            return Decision.allow, evaluation.matched_rule_id, False, evaluation.reason
        if evaluation.action == RuleAction.deny:
            return Decision.deny, evaluation.matched_rule_id, False, evaluation.reason
        if evaluation.action == RuleAction.require_approval:
            return Decision.approval_required, evaluation.matched_rule_id, False, evaluation.reason

        judge = judge_tool_call(policy, request, threat_report)
        return judge.decision, evaluation.matched_rule_id, True, judge.rationale

    @staticmethod
    def run_to_dto(row: EvalRun) -> EvalRunDTO:
        return EvalRunDTO(
            id=row.id,
            policy_version_id=row.policy_version_id,
            status=EvalStatus(row.status),
            created_at=utc_iso(row.created_at) or "",
            completed_at=utc_iso(row.completed_at),
            total_entries=row.total_entries,
            processed_entries=row.processed_entries,
            agreed=row.agreed,
            disagreed=row.disagreed,
            errored=row.errored,
        )

    @staticmethod
    def result_to_dto(row: EvalResult) -> EvalResultDTO:
        return EvalResultDTO(
            id=row.id,
            eval_run_id=row.eval_run_id,
            audit_id=row.audit_id,
            original_decision=Decision(row.original_decision),
            replayed_decision=Decision(row.replayed_decision),
            matched_rule_id=row.matched_rule_id,
            judge_used=row.judge_used,
            replay_reason=row.replay_reason,
            agreement=row.agreement,
        )
