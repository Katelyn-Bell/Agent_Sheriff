#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

curl -fsS "$BASE_URL/v1/health" >/dev/null

cd "$ROOT_DIR/backend"
uv run python -m agentsheriff.demo.deputy_dusty --base-url "$BASE_URL" --all

echo "AgentSheriff demo smoke test passed."
