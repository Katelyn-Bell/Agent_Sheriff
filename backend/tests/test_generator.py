from __future__ import annotations

from agentsheriff.models.dto import RuleAction
from agentsheriff.threats import generate_starter_policy


def _rules(result):
    return {rule.id: rule for rule in result.static_rules}


def test_generator_finance_policy_is_conservative() -> None:
    result = generate_starter_policy(
        "I use OpenClaw to triage finance email, draft notes, and send invoices internally.",
        ["gmail.read_inbox", "gmail.send_email", "files.read"],
        domain_hint="finance",
    )
    rules = _rules(result)

    assert "Finance assistant" in result.intent_summary
    assert "invoices" in result.judge_prompt
    assert rules["policy.generated.allow_gmail_read_inbox"].action == RuleAction.allow
    assert rules["policy.generated.review_external_gmail_send_email"].action == RuleAction.require_approval
    assert rules["policy.generated.review_email_attachments"].severity_floor == 65
    assert "policy.generated.judge_fallback_gmail" in rules


def test_generator_inbox_policy_handles_support_style_input() -> None:
    result = generate_starter_policy(
        "Inbox assistant that reads support mail and drafts customer replies.",
        ["gmail.read_inbox", "gmail.send_email", "calendar.create_event"],
    )
    rules = _rules(result)

    assert "Inbox assistant" in result.intent_summary
    assert "customer data" in result.judge_prompt
    assert rules["policy.generated.review_external_gmail_send_email"].action == RuleAction.require_approval
    assert "policy.generated.judge_fallback_calendar" in rules


def test_generator_repo_maintenance_blocks_force_pushes() -> None:
    result = generate_starter_policy(
        "Repo maintenance assistant that opens PRs and manages branches.",
        ["github.list_repos", "github.push_branch", "shell.run"],
    )
    rules = _rules(result)

    assert "Repo-Maintenance assistant" in result.intent_summary
    assert rules["policy.generated.allow_github_list_repos"].action == RuleAction.allow
    assert rules["policy.generated.block_force_push"].action == RuleAction.deny
    assert rules["policy.generated.block_force_push"].severity_floor == 90
    assert "policy.generated.judge_fallback_shell" in rules


def test_generator_research_policy_delegates_browser_actions() -> None:
    result = generate_starter_policy(
        "Browser research assistant that searches the web and summarizes articles.",
        ["browser.search", "browser.open_url", "files.write"],
    )
    rules = _rules(result)

    assert "Research assistant" in result.intent_summary
    assert "untrusted URLs" in result.judge_prompt
    assert "policy.generated.judge_fallback_browser" in rules
    assert any(rule.action == RuleAction.delegate_to_judge for rule in result.static_rules)
