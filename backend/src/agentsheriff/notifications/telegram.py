from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from agentsheriff.models.dto import ApprovalDTO

logger = logging.getLogger(__name__)

_API = "https://api.telegram.org"
_SEND_TIMEOUT = httpx.Timeout(10.0, connect=5.0)

# Maximum characters in callback_data is 64 bytes.
# "approve:" + approval_id (approval_ + 12 hex = 21) = 29 — safely within limit.


class TelegramApprovalNotifier:
    def __init__(self, token: str, chat_id: str) -> None:
        self._token = token
        self._chat_id = chat_id
        self._base = f"{_API}/bot{token}"
        # approval_id -> telegram message_id, used for editing after resolution
        self._msg_ids: dict[str, int] = {}

    async def send_approval(self, approval: ApprovalDTO) -> None:
        agent = approval.agent_label or approval.agent_id
        explanation = approval.user_explanation or approval.reason
        args_snippet = json.dumps(approval.args, indent=2)
        if len(args_snippet) > 400:
            args_snippet = args_snippet[:397] + "…"

        text = (
            f"🔔 *Approval Required*\n"
            f"*Agent:* {_esc(agent)}\n"
            f"*Tool:* `{_esc(approval.tool)}`\n\n"
            f"{_esc(explanation)}\n\n"
            f"```json\n{args_snippet}\n```"
        )
        # callback_data is namespaced "agentsheriff:" so the OpenClaw plugin
        # (registerInteractiveHandler) routes these taps to the AgentSheriff API.
        keyboard = {
            "inline_keyboard": [[
                {"text": "✅ Approve", "callback_data": f"agentsheriff:approve:{approval.id}"},
                {"text": "❌ Deny", "callback_data": f"agentsheriff:deny:{approval.id}"},
                {"text": "🔒 Redact", "callback_data": f"agentsheriff:redact:{approval.id}"},
            ]]
        }
        try:
            async with httpx.AsyncClient(timeout=_SEND_TIMEOUT) as client:
                resp = await client.post(
                    f"{self._base}/sendMessage",
                    json={
                        "chat_id": self._chat_id,
                        "text": text,
                        "parse_mode": "MarkdownV2",
                        "reply_markup": keyboard,
                    },
                )
                resp.raise_for_status()
                self._msg_ids[approval.id] = resp.json()["result"]["message_id"]
        except Exception:
            logger.exception("telegram_send_failed approval_id=%s", approval.id)

    async def edit_resolved(self, approval_id: str, resolution: str) -> None:
        """Delete the approval request message. Idempotent — no-ops if already deleted (e.g. by the OpenClaw plugin on a Telegram-initiated tap)."""
        msg_id = self._msg_ids.pop(approval_id, None)
        if msg_id is None:
            return
        try:
            async with httpx.AsyncClient(timeout=_SEND_TIMEOUT) as client:
                resp = await client.post(
                    f"{self._base}/deleteMessage",
                    json={
                        "chat_id": self._chat_id,
                        "message_id": msg_id,
                    },
                )
                # 400 "message to delete not found" is expected when the plugin
                # already deleted the message on tap; don't raise on it.
                if resp.status_code != 200 and resp.status_code != 400:
                    resp.raise_for_status()
        except Exception:
            logger.exception("telegram_delete_failed approval_id=%s", approval_id)

    async def poll(
        self,
        on_callback: Callable[[str, str], Awaitable[None]],
    ) -> None:
        """Long-poll Telegram for callback_query events and invoke on_callback(approval_id, action)."""
        offset: int | None = None
        async with httpx.AsyncClient(timeout=httpx.Timeout(40.0, connect=10.0)) as client:
            # Drop any registered webhook so getUpdates isn't blocked with 409
            await client.post(f"{self._base}/deleteWebhook", json={"drop_pending_updates": False})
            while True:
                try:
                    params: dict[str, Any] = {
                        "timeout": 30,
                        "allowed_updates": ["callback_query"],
                    }
                    if offset is not None:
                        params["offset"] = offset

                    resp = await client.get(f"{self._base}/getUpdates", params=params)
                    resp.raise_for_status()
                    for update in resp.json().get("result", []):
                        offset = update["update_id"] + 1
                        cq = update.get("callback_query")
                        if not cq:
                            continue
                        # Acknowledge immediately so Telegram stops the loading indicator
                        await client.post(
                            f"{self._base}/answerCallbackQuery",
                            json={"callback_query_id": cq["id"]},
                        )
                        parsed = parse_callback_data(cq.get("data", ""))
                        if parsed is None:
                            continue
                        action, approval_id = parsed
                        try:
                            await on_callback(approval_id, action)
                        except Exception:
                            logger.exception("telegram_callback_error data=%s", cq.get("data", ""))
                except asyncio.CancelledError:
                    return
                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code == 409:
                        # Another getUpdates is still in-flight on Telegram's side.
                        # Wait for it to expire (our poll timeout is 30s) then retry.
                        logger.warning("telegram_poll_conflict_waiting")
                        await asyncio.sleep(35)
                    else:
                        logger.exception("telegram_poll_error")
                        await asyncio.sleep(5)
                except Exception:
                    logger.exception("telegram_poll_error")
                    await asyncio.sleep(5)


def _esc(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2."""
    special = r"\_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{c}" if c in special else c for c in text)


def parse_callback_data(data: str) -> tuple[str, str] | None:
    """Return (action, approval_id) for AgentSheriff approval callbacks."""
    parts = data.split(":")
    if len(parts) == 2:
        action, approval_id = parts
    elif len(parts) == 3 and parts[0] == "agentsheriff":
        _, action, approval_id = parts
    else:
        return None

    if action not in {"approve", "deny", "redact"} or not approval_id:
        return None
    return action, approval_id
