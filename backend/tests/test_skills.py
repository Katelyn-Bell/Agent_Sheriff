from __future__ import annotations

import json
import textwrap
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from agentsheriff.config import Settings
from agentsheriff.main import app
from agentsheriff.models.dto import RuleAction
from agentsheriff.models.orm import Base
from agentsheriff.skills.laws import generate_skill_laws
from agentsheriff.skills.parser import parse_skill_md
from agentsheriff.skills.registry import get_parsed_skill, installed_skills


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


_SAMPLE_SKILL = textwrap.dedent(
    """
    ---
    id: kalshi-trading
    name: Kalshi Trading
    description: Trade on Kalshi via kalshi-cli.
    base_command: kalshi-cli
    ---

    # Kalshi Trading

    ```bash
    kalshi-cli markets list
    kalshi-cli markets get --market KXBTC-26FEB12-B97000
    kalshi-cli orders create --market KXBTC-26FEB12-B97000 --side yes --qty 10 --price 50
    kalshi-cli --prod orders create --market KXBTC-26FEB12-B97000 --side yes --qty 10000 --price 99 --yes
    kalshi-cli orders cancel-all
    kalshi-cli portfolio subaccounts transfer --from 1 --to 2 --amount 50000
    ```
    """
).strip()


def test_parser_extracts_metadata_and_commands() -> None:
    skill = parse_skill_md(_SAMPLE_SKILL)
    assert skill.id == "kalshi-trading"
    assert skill.name == "Kalshi Trading"
    assert skill.base_command == "kalshi-cli"

    names = {command.name for command in skill.commands}
    assert {
        "markets list",
        "markets get",
        "orders create",
        "orders cancel-all",
        "portfolio subaccounts transfer",
    } <= names


def test_parser_merges_demo_and_prod_invocations_under_one_command() -> None:
    skill = parse_skill_md(_SAMPLE_SKILL)
    orders_create = next(c for c in skill.commands if c.name == "orders create")
    assert "--prod" in orders_create.flags
    assert "--qty" in orders_create.flags
    assert "--prod" in orders_create.risky_flags
    assert "--yes" in orders_create.risky_flags


def test_parser_marks_inherently_risky_subcommands() -> None:
    skill = parse_skill_md(_SAMPLE_SKILL)
    cancel_all = next(c for c in skill.commands if c.name == "orders cancel-all")
    assert "::risky-subcommand" in cancel_all.risky_flags

    transfer = next(c for c in skill.commands if c.name == "portfolio subaccounts transfer")
    assert "::risky-subcommand" in transfer.risky_flags


def test_parser_falls_back_to_default_id_when_frontmatter_missing() -> None:
    body = "```bash\nkalshi-cli markets list\n```"
    skill = parse_skill_md(body, default_id="manual-id", default_name="Manual")
    assert skill.id == "manual-id"
    assert skill.name == "Manual"
    assert skill.base_command == "kalshi-cli"


def test_parser_rejects_skill_with_no_commands() -> None:
    with pytest.raises(ValueError):
        parse_skill_md("# Empty SKILL\nNo commands here.")


# ---------------------------------------------------------------------------
# Registry — Kalshi fixture is checked into skills/fixtures/.
# ---------------------------------------------------------------------------


def test_registry_discovers_bundled_kalshi_fixture() -> None:
    skills = installed_skills()
    ids = {skill.id for skill in skills}
    assert "kalshi-trading" in ids


def test_registry_kalshi_dto_shape_matches_sticky_note_contract() -> None:
    parsed = get_parsed_skill("kalshi-trading")
    assert parsed is not None

    skills = installed_skills()
    kalshi = next(skill for skill in skills if skill.id == "kalshi-trading")
    assert kalshi.base_command == "kalshi-cli"
    assert any(command.name == "orders create" for command in kalshi.commands)
    # The `## Command Reference` table drives the vocabulary; risky-subcommand
    # tokens like `cancel-all` and `transfer` still surface as risky markers.
    assert "::risky-subcommand" in kalshi.risky_flags


# ---------------------------------------------------------------------------
# REST API
# ---------------------------------------------------------------------------


@pytest.fixture()
def client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    original_factory = app.state.session_factory
    app.state.session_factory = SessionLocal
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.state.session_factory = original_factory


def test_get_v1_skills_lists_kalshi(client: TestClient) -> None:
    response = client.get("/v1/skills")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    ids = {skill["id"] for skill in payload}
    assert "kalshi-trading" in ids


def test_get_v1_skills_id_returns_full_command_vocabulary(client: TestClient) -> None:
    response = client.get("/v1/skills/kalshi-trading")
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "kalshi-trading"
    assert payload["base_command"] == "kalshi-cli"
    assert any(cmd["name"] == "orders create" for cmd in payload["commands"])
    # `## Command Reference` is now the source of truth — the table doesn't
    # list `--prod`, so we verify the inherent risky-subcommand marker instead.
    assert "::risky-subcommand" in payload["risky_flags"]


def test_get_v1_skills_id_404s_for_unknown(client: TestClient) -> None:
    response = client.get("/v1/skills/does-not-exist")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Law generator — fallback path runs without the LLM
# ---------------------------------------------------------------------------


def test_generate_skill_laws_fallback_emits_risky_subcommand_rule() -> None:
    parsed = get_parsed_skill("kalshi-trading")
    assert parsed is not None
    settings = Settings(
        USE_LLM_CLASSIFIER=False,
        ANTHROPIC_API_KEY=None,
        OPENAI_API_KEY=None,
        OPENROUTER_API_KEY=None,
    )

    result = generate_skill_laws(parsed, "Trade up to $50/market on demo, never real money.", settings=settings)

    assert result.intent_summary
    assert result.judge_prompt
    rule_ids = [rule.id for rule in result.static_rules]

    # The `## Command Reference` table drives the vocabulary, so risky-subcommand
    # tokens like `cancel-all` / `transfer` should produce require_approval rules.
    risky_subcmd_rule = next(
        rule
        for rule in result.static_rules
        if rule.action is RuleAction.require_approval
        and any(
            predicate.value in {"cancel-all", "transfer"}
            for predicate in rule.arg_predicates
        )
    )
    assert risky_subcmd_rule.tool_match.value == "shell.run"
    assert risky_subcmd_rule.skill_match is not None
    assert risky_subcmd_rule.skill_match.value == "kalshi-trading"

    # Judge fallback rule must be present so unknown commands still get inspected.
    assert any(rule.action is RuleAction.delegate_to_judge for rule in result.static_rules)
    # Read-only commands should be allow-listed.
    assert any(rule.action is RuleAction.allow for rule in result.static_rules)
    assert len(rule_ids) == len(set(rule_ids)), "rule ids must be unique"


def test_generate_skill_laws_with_mocked_llm_filters_hallucinated_flags() -> None:
    parsed = get_parsed_skill("kalshi-trading")
    assert parsed is not None

    response_payload = {
        "intent_summary": "Hold the line on cancellations.",
        "judge_prompt": "Be conservative.",
        "static_rules": [
            {
                "name": "Block cancel-all",
                "action": "deny",
                "predicates": [{"operator": "contains", "value": "cancel-all"}],
                "severity_floor": 95,
                "reason": "Bulk cancellation disabled by user law.",
                "user_explanation": "You banned cancel-all.",
            },
            {
                # This one references a flag that does NOT exist in vocabulary — it must be dropped.
                "name": "Hallucinated rule",
                "action": "deny",
                "predicates": [{"operator": "contains", "value": "--nuke-portfolio"}],
                "reason": "should be filtered",
            },
            {
                # No predicates and a concrete action → must be dropped.
                "name": "Match everything",
                "action": "allow",
                "predicates": [],
                "reason": "too broad",
            },
        ],
        "notes": ["LLM was here."],
    }

    class _StubMessages:
        def __init__(self) -> None:
            self.calls: list[dict[str, Any]] = []

        def create(self, **kwargs: Any) -> Any:
            self.calls.append(kwargs)

            class _Resp:
                content = [{"type": "text", "text": json.dumps(response_payload)}]

            return _Resp()

    class _StubClient:
        def __init__(self) -> None:
            self.messages = _StubMessages()

    stub = _StubClient()
    settings = Settings(USE_LLM_CLASSIFIER=True, ANTHROPIC_API_KEY="test-key")

    result = generate_skill_laws(
        parsed,
        "Never touch real money without approval.",
        settings=settings,
        llm_client=stub,
    )

    rule_names = [rule.name for rule in result.static_rules]
    assert "Block cancel-all" in rule_names
    assert "Hallucinated rule" not in rule_names
    assert "Match everything" not in rule_names

    deny_rule = next(rule for rule in result.static_rules if rule.name == "Block cancel-all")
    assert deny_rule.action is RuleAction.deny
    assert deny_rule.tool_match.value == "shell.run"
    assert deny_rule.skill_match is not None
    assert deny_rule.skill_match.value == "kalshi-trading"

    # Prompt-cache + constrained-vocabulary contract: the LLM must have been
    # told the skill id, base command, and full vocabulary.
    assert stub.messages.calls, "LLM should have been called"
    call = stub.messages.calls[0]
    system_text = call["system"][0]["text"]
    assert "kalshi-trading" in system_text
    assert "kalshi-cli" in system_text
    user_payload = json.loads(call["messages"][0]["content"])
    assert "vocabulary" in user_payload
    # `cancel-all` is one of the table tokens; verify the LLM saw it.
    all_tokens = set(user_payload["vocabulary"]["all_flags"]) | {
        token
        for command in user_payload["vocabulary"]["commands"]
        for token in command["name"].split()
    }
    assert "cancel-all" in all_tokens


def test_generate_skill_laws_post_endpoint(client: TestClient) -> None:
    # POST /v1/skills/{id}/generate-laws should hit the fallback path when the
    # test environment has no LLM key configured.
    response = client.post(
        "/v1/skills/kalshi-trading/generate-laws",
        json={"user_intent": "Trade up to $50/market on demo, never real money."},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["intent_summary"]
    assert payload["judge_prompt"]
    assert payload["static_rules"]
    # Risky-subcommand tokens from the `## Command Reference` table should
    # produce predicates referencing them.
    risky_tokens = {"cancel-all", "transfer"}
    assert any(
        any(p.get("value") in risky_tokens for p in rule.get("arg_predicates", []))
        for rule in payload["static_rules"]
    )


def test_generate_skill_laws_post_endpoint_unknown_skill(client: TestClient) -> None:
    response = client.post(
        "/v1/skills/no-such-skill/generate-laws",
        json={"user_intent": "anything"},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Command Reference section extraction (REVISION B)
# ---------------------------------------------------------------------------


_COMMAND_REFERENCE_SAMPLE = textwrap.dedent(
    """
    ---
    id: sample-skill
    name: Sample Skill
    description: A sample.
    base_command: sample-cli
    ---

    # Sample Skill

    Some prose with a fenced block that should be ignored once the table is present.

    ```bash
    sample-cli ignored --do-not-extract
    ```

    ## Command Reference

    | Subcommand | Purpose |
    | --- | --- |
    | `auth login` | Log in. |
    | `markets list` | List markets. |
    | `orders cancel-all` | Cancel everything. |
    | `portfolio transfer --from 1 --to 2` | Move funds (with flags). |
    """
).strip()


def test_parser_prefers_command_reference_section() -> None:
    skill = parse_skill_md(_COMMAND_REFERENCE_SAMPLE)
    names = {command.name for command in skill.commands}
    # The fenced-block invocation `ignored` should be skipped because the
    # `## Command Reference` table is present and produces commands.
    assert "ignored" not in names
    assert {"auth login", "markets list", "orders cancel-all", "portfolio transfer"} <= names

    cancel_all = next(c for c in skill.commands if c.name == "orders cancel-all")
    assert "::risky-subcommand" in cancel_all.risky_flags

    transfer = next(c for c in skill.commands if c.name == "portfolio transfer")
    # Flags from the table cell should flow through to the parsed flags.
    assert "--from" in transfer.flags
    assert "--to" in transfer.flags


def test_parser_falls_back_when_command_reference_absent() -> None:
    # _SAMPLE_SKILL has no `## Command Reference` section; the legacy fenced-
    # block scan should still extract commands.
    skill = parse_skill_md(_SAMPLE_SKILL)
    names = {command.name for command in skill.commands}
    assert "markets list" in names
    assert "orders create" in names


def test_parser_handles_renamed_kalshi_fixture() -> None:
    parsed = get_parsed_skill("kalshi-trading")
    assert parsed is not None
    names = {command.name for command in parsed.commands}
    # A representative slice of the table-driven command set. Stable enough
    # that adding rows to the SKILL.md won't break this test.
    expected = {
        "auth login",
        "auth status",
        "markets list",
        "markets get",
        "markets orderbook",
        "orders create",
        "orders list",
        "orders cancel",
        "orders cancel-all",
        "portfolio balance",
        "portfolio positions",
        "portfolio subaccounts list",
        "portfolio subaccounts transfer",
    }
    assert expected <= names
    # Section-header rows like ``| **Auth** |`` and table column labels must
    # never leak through as commands.
    assert not any(name.startswith("**") for name in names)
    assert "Task" not in names
    assert "Command" not in names


# ---------------------------------------------------------------------------
# guardrails plumbing + coverage pass
# ---------------------------------------------------------------------------


def test_generate_skill_laws_forwards_guardrails_to_payload() -> None:
    parsed = get_parsed_skill("kalshi-trading")
    assert parsed is not None

    captured: dict[str, Any] = {}

    class _StubMessages:
        def create(self, **kwargs: Any) -> Any:
            captured.update(kwargs)

            class _Resp:
                content = [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "intent_summary": "ok",
                                "judge_prompt": "ok",
                                "static_rules": [
                                    {
                                        "name": "Allow markets list",
                                        "action": "allow",
                                        "predicates": [
                                            {"operator": "contains", "value": "markets list"}
                                        ],
                                        "reason": "read-only",
                                    }
                                ],
                                "notes": [],
                            }
                        ),
                    }
                ]

            return _Resp()

    class _StubClient:
        messages = _StubMessages()

    settings = Settings(USE_LLM_CLASSIFIER=True, ANTHROPIC_API_KEY="test-key")

    result = generate_skill_laws(
        parsed,
        "Watch the markets.",
        "Never place real-money trades; never use --prod.",
        settings=settings,
        llm_client=_StubClient(),
    )

    user_payload = json.loads(captured["messages"][0]["content"])
    assert user_payload["guardrails"] == "Never place real-money trades; never use --prod."
    assert user_payload["user_intent"] == "Watch the markets."

    # The generated judge_prompt must wrap the guardrails inside delimited tags
    # so a malicious guardrails string can't escape the framing.
    assert "<guardrails>Never place real-money trades; never use --prod.</guardrails>" in result.judge_prompt
    assert "<user_intent>Watch the markets.</user_intent>" in result.judge_prompt


def test_generate_skill_laws_post_endpoint_accepts_guardrails(client: TestClient) -> None:
    response = client.post(
        "/v1/skills/kalshi-trading/generate-laws",
        json={
            "user_intent": "Watch the markets.",
            "guardrails": "Never place real-money trades.",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    # Even on the deterministic fallback path the guardrails should be folded
    # into the judge prompt template.
    assert "<guardrails>Never place real-money trades.</guardrails>" in payload["judge_prompt"]


def test_generate_skill_laws_coverage_pass_fills_uncovered_commands() -> None:
    parsed = get_parsed_skill("kalshi-trading")
    assert parsed is not None

    # The LLM only returns a rule for one command; every other command should
    # get an auto-coverage `require_approval` rule appended.
    response_payload = {
        "intent_summary": "narrow",
        "judge_prompt": "be careful",
        "static_rules": [
            {
                "name": "Allow markets list",
                "action": "allow",
                "predicates": [{"operator": "contains", "value": "markets list"}],
                "reason": "read-only",
            }
        ],
        "notes": [],
    }

    class _StubMessages:
        def create(self, **kwargs: Any) -> Any:
            class _Resp:
                content = [{"type": "text", "text": json.dumps(response_payload)}]

            return _Resp()

    class _StubClient:
        messages = _StubMessages()

    settings = Settings(USE_LLM_CLASSIFIER=True, ANTHROPIC_API_KEY="test-key")

    result = generate_skill_laws(
        parsed,
        "Watch the markets.",
        settings=settings,
        llm_client=_StubClient(),
    )

    # Every command in the skill should now have at least one rule referencing it.
    for command in parsed.commands:
        assert any(
            any(predicate.value == command.name for predicate in rule.arg_predicates)
            or any(command.name in (predicate.value or "") for predicate in rule.arg_predicates)
            for rule in result.static_rules
        ), f"command {command.name!r} was not covered"

    # The auto-added rules should default to require_approval and carry the
    # documented reason string.
    auto_rules = [
        rule
        for rule in result.static_rules
        if rule.reason == "AI had no recommendation for this command — review."
    ]
    assert auto_rules, "expected at least one auto-coverage rule"
    for rule in auto_rules:
        assert rule.action is RuleAction.require_approval

    # Notes should flag that auto-coverage happened.
    assert any("Auto-added" in note for note in result.notes)
