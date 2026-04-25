from __future__ import annotations

import shlex
import os
import subprocess
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
    cmd = _command_arg(args)
    if cmd not in ALLOWED_COMMANDS:
        if cmd == "kalshi-cli" or cmd.startswith("kalshi-cli "):
            return _run_kalshi_cli(cmd)
        if _is_kalshi_compound(cmd):
            return _run_kalshi_compound(cmd)
        if os.environ.get("AGENTSHERIFF_ALLOW_REAL_SHELL", "").lower() in {"1", "true", "yes"}:
            return _run_real_shell(cmd)
        raise AdapterValidationError(f"Command is not allowlisted for the local demo shell: {cmd}")
    return ok("shell.run", cmd=cmd, exit_code=0, stdout=ALLOWED_COMMANDS[cmd], stderr="")


def _command_arg(args: dict[str, Any]) -> str:
    if "command" in args and args.get("command") is not None:
        return text_arg(args, "command").strip()
    return text_arg(args, "cmd").strip()


def _run_kalshi_cli(cmd: str) -> dict[str, Any]:
    argv = shlex.split(cmd)
    real_kalshi_cli = os.environ.get("AGENTSHERIFF_REAL_KALSHI_CLI", "").strip()
    if real_kalshi_cli and argv:
        argv[0] = real_kalshi_cli
    try:
        completed = subprocess.run(
            argv,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError as exc:
        raise AdapterValidationError("kalshi-cli is not installed or not on PATH.") from exc
    except subprocess.TimeoutExpired as exc:
        raise AdapterValidationError("kalshi-cli command timed out after 30 seconds.") from exc

    return ok(
        "shell.run",
        cmd=cmd,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


_KALSHI_ALLOWED_BUILTINS = {"printf", "echo", "kalshi-cli", "command"}
_KALSHI_SHELL_OPERATORS = {"&&", "||", ";", "|"}


def _is_kalshi_compound(cmd: str) -> bool:
    if "kalshi-cli" not in cmd:
        return False
    try:
        tokens = shlex.split(cmd, posix=True)
    except ValueError:
        return False
    if not tokens:
        return False
    expecting_command = True
    saw_kalshi = False
    for tok in tokens:
        if tok in _KALSHI_SHELL_OPERATORS:
            expecting_command = True
            continue
        if expecting_command:
            if tok not in _KALSHI_ALLOWED_BUILTINS:
                return False
            if tok == "kalshi-cli":
                saw_kalshi = True
            expecting_command = False
    return saw_kalshi


def _run_kalshi_compound(cmd: str) -> dict[str, Any]:
    real_kalshi_cli = os.environ.get("AGENTSHERIFF_REAL_KALSHI_CLI", "").strip()
    effective_cmd = cmd
    if real_kalshi_cli:
        effective_cmd = cmd.replace("kalshi-cli", shlex.quote(real_kalshi_cli))
    try:
        completed = subprocess.run(
            effective_cmd,
            shell=True,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired as exc:
        raise AdapterValidationError("kalshi-cli command timed out after 30 seconds.") from exc

    return ok(
        "shell.run",
        cmd=cmd,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _run_real_shell(cmd: str) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            cmd,
            shell=True,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired as exc:
        raise AdapterValidationError("Shell command timed out after 30 seconds.") from exc

    return ok(
        "shell.run",
        cmd=cmd,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
