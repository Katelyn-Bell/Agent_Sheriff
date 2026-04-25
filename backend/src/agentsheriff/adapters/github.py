from __future__ import annotations

from typing import Any

from ._common import ok, require_gateway_token, stable_id, text_arg


def create_issue(*, args: dict[str, Any], gateway_token: str) -> dict[str, Any]:
    require_gateway_token(gateway_token)
    repo = text_arg(args, "repo", "agentsheriff/demo")
    title = text_arg(args, "title", "Untitled issue")
    body = text_arg(args, "body")
    issue_number = int(stable_id("issue", repo, title, body).split("_", 1)[1][:6], 16) % 1000 + 1
    return ok("github.create_issue", repo=repo, issue={"number": issue_number, "title": title, "body": body})


def push_branch(*, args: dict[str, Any], gateway_token: str) -> dict[str, Any]:
    require_gateway_token(gateway_token)
    repo = text_arg(args, "repo", "agentsheriff/demo")
    branch = text_arg(args, "branch", "person-4/adapters-openclaw-demo")
    force = bool(args.get("force", False))
    return ok("github.push_branch", repo=repo, branch=branch, force=force, pushed=True, remote="mock-origin")
