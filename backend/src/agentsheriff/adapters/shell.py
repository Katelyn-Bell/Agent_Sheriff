from __future__ import annotations

from typing import Any

from ._common import AdapterValidationError, ok, require_gateway_token, text_arg


ALLOWED_COMMANDS = {
    "pwd": "/mock/workspace\n",
    "ls": "invoices\nnotes\nreadme.txt\n",
    "ls invoices": "invoice_draft.pdf\n",
    "cat readme.txt": "Welcome to the AgentSheriff mock workspace.\n",
}


def run(*, args: dict[str, Any], gateway_token: str) -> dict[str, Any]:
    require_gateway_token(gateway_token)
    cmd = text_arg(args, "cmd").strip()
    if cmd not in ALLOWED_COMMANDS:
        raise AdapterValidationError(f"Command is not allowlisted for the local demo shell: {cmd}")
    return ok("shell.run", cmd=cmd, exit_code=0, stdout=ALLOWED_COMMANDS[cmd], stderr="")
