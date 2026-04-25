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
    assert "--prod" in kalshi.risky_flags


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
    assert "--prod" in payload["risky_flags"]


def test_get_v1_skills_id_404s_for_unknown(client: TestClient) -> None:
    response = client.get("/v1/skills/does-not-exist")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Law generator — fallback path runs without the LLM
# ---------------------------------------------------------------------------


def test_generate_skill_laws_fallback_emits_prod_approval_rule() -> None:
    parsed = get_parsed_skill("kalshi-trading")
    assert parsed is not None
    settings = Settings(USE_LLM_CLASSIFIER=False, ANTHROPIC_API_KEY=None)

    result = generate_skill_laws(parsed, "Trade up to $50/market on demo, never real money.", settings=settings)

    assert result.intent_summary
    assert result.judge_prompt
    rule_ids = [rule.id for rule in result.static_rules]

    prod_rule = next(rule for rule in result.static_rules if "prod" in rule.id)
    assert prod_rule.action is RuleAction.require_approval
    assert prod_rule.tool_match.value == "shell.run"
    assert prod_rule.skill_match is not None
    assert prod_rule.skill_match.value == "kalshi-trading"
    assert any(predicate.value == "--prod" for predicate in prod_rule.arg_predicates)

    # Judge fallback rule must be present so unknown commands still get inspected.
    assert any(rule.action is RuleAction.delegate_to_judge for rule in result.static_rules)
    # Read-only commands should be allow-listed.
    assert any(rule.action is RuleAction.allow for rule in result.static_rules)
    assert len(rule_ids) == len(set(rule_ids)), "rule ids must be unique"


def test_generate_skill_laws_with_mocked_llm_filters_hallucinated_flags() -> None:
    parsed = get_parsed_skill("kalshi-trading")
    assert parsed is not None

    response_payload = {
        "intent_summary": "Hold the line on real money.",
        "judge_prompt": "Be conservative.",
        "static_rules": [
            {
                "name": "Block real-money trades",
                "action": "deny",
                "predicates": [{"operator": "contains", "value": "--prod"}],
                "severity_floor": 95,
                "reason": "Real money disabled by user law.",
                "user_explanation": "You banned real-money trades.",
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
    assert "Block real-money trades" in rule_names
    assert "Hallucinated rule" not in rule_names
    assert "Match everything" not in rule_names

    deny_rule = next(rule for rule in result.static_rules if rule.name == "Block real-money trades")
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
    assert "--prod" in user_payload["vocabulary"]["all_flags"]


def test_generate_skill_laws_post_endpoint(client: TestClient) -> None:
    # POST /v1/skills/{id}/generate-laws should hit the fallback path when the
    # test environment has no Anthropic key configured.
    response = client.post(
        "/v1/skills/kalshi-trading/generate-laws",
        json={"user_intent": "Trade up to $50/market on demo, never real money."},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["intent_summary"]
    assert payload["judge_prompt"]
    assert payload["static_rules"]
    assert any(
        any(p.get("value") == "--prod" for p in rule.get("arg_predicates", []))
        for rule in payload["static_rules"]
    )


def test_generate_skill_laws_post_endpoint_unknown_skill(client: TestClient) -> None:
    response = client.post(
        "/v1/skills/no-such-skill/generate-laws",
        json={"user_intent": "anything"},
    )
    assert response.status_code == 404
