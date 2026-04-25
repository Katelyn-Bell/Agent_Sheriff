from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _scrub_external_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force test isolation from any real credentials in ``backend/.env``.

    Local developer machines may carry real OPENAI/OPENROUTER/ANTHROPIC keys
    plus a real Google OAuth client. Tests that exercise those paths inject
    stubs or assert the not-configured branch, so we override every relevant
    env var for the whole test session.

    Setting to empty string (rather than ``delenv``) is deliberate:
    pydantic-settings reads env vars *after* the ``env_file``, so an empty
    string is what reliably overrides whatever sits in the ``.env`` file.
    """

    for key in (
        "OPENAI_API_KEY",
        "OPENROUTER_API_KEY",
        "ANTHROPIC_API_KEY",
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
    ):
        monkeypatch.setenv(key, "")
    # Also clear cached Settings so the new env propagates.
    from agentsheriff import config

    config.get_settings.cache_clear()
    yield
    config.get_settings.cache_clear()
