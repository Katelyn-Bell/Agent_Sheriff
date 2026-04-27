from __future__ import annotations

from agentsheriff.config import Settings


def test_default_approval_timeout_is_five_minutes() -> None:
    settings = Settings(_env_file=None)

    assert settings.approval_timeout_s == 300


def test_default_openrouter_model_is_claude_opus_4_7() -> None:
    settings = Settings(_env_file=None)

    assert settings.openrouter_model == "anthropic/claude-opus-4.7"
