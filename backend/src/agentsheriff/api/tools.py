from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from agentsheriff.adapters import manifest_for_json

router = APIRouter(prefix="/v1/tools", tags=["tools"])


@router.get("")
def list_tools() -> list[dict[str, Any]]:
    return manifest_for_json()
