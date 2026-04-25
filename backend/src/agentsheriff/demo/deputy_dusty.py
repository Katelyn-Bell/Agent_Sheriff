from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import httpx

from agentsheriff.models.dto import ToolCallRequest


SCENARIOS = ("good", "injection", "approval")
SCENARIO_DIR = Path(__file__).with_name("scenarios")


def load_scenario(name: str) -> dict[str, Any]:
    if name not in SCENARIOS:
        raise ValueError(f"Unknown scenario '{name}'. Choose from: {', '.join(SCENARIOS)}")
    payload = json.loads((SCENARIO_DIR / f"{name}.json").read_text())
    return _tool_call_payload(payload)


def run_scenario(name: str, *, base_url: str, approve: bool = True, timeout: float = 10.0) -> dict[str, Any]:
    payload = load_scenario(name)
    ToolCallRequest.model_validate(payload)
    with httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout) as client:
        response = client.post("/v1/tool-call", json=payload)
        response.raise_for_status()
        result = response.json()
        if name == "approval" and approve and result.get("approval_id"):
            approval_response = client.post(f"/v1/approvals/{result['approval_id']}", json={"action": "approve"})
            approval_response.raise_for_status()
            result["approval_resolution"] = approval_response.json()
        return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Deputy Dusty demo scenarios against a live AgentSheriff backend.")
    parser.add_argument("--base-url", default="http://localhost:8000", help="AgentSheriff backend URL.")
    parser.add_argument("--scenario", choices=SCENARIOS, help="Scenario to run.")
    parser.add_argument("--all", action="store_true", help="Run all canonical scenarios.")
    parser.add_argument("--no-approve", action="store_true", help="Leave approval scenario pending.")
    args = parser.parse_args(argv)

    if not args.all and not args.scenario:
        parser.error("Choose --scenario good|injection|approval or --all.")

    names = SCENARIOS if args.all else (args.scenario,)
    for name in names:
        result = run_scenario(name, base_url=args.base_url, approve=not args.no_approve)
        print(json.dumps({"scenario": name, "result": result}, indent=2, sort_keys=True))
    return 0


def _tool_call_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key in ToolCallRequest.model_fields}


if __name__ == "__main__":
    raise SystemExit(main())
