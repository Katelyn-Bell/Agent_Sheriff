#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/demo/docker-compose.yml"
PROFILE_ARGS=()

if [[ "${1:-}" == "--with-openclaw" ]]; then
  PROFILE_ARGS=(--profile openclaw)
fi

cd "$ROOT_DIR"
docker compose -f "$COMPOSE_FILE" "${PROFILE_ARGS[@]}" up --build
