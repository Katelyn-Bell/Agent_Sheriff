from __future__ import annotations

import asyncio
import time
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class StreamHub:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast(self, frame: dict[str, Any]) -> None:
        stale: list[WebSocket] = []
        for websocket in self._connections:
            try:
                await websocket.send_json(frame)
            except RuntimeError:
                stale.append(websocket)
        for websocket in stale:
            self.disconnect(websocket)

    def broadcast_nowait(self, frame: dict[str, Any]) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        loop.create_task(self.broadcast(frame))


hub = StreamHub()


@router.websocket("/v1/stream")
async def stream(websocket: WebSocket) -> None:
    await hub.connect(websocket)
    try:
        while True:
            await websocket.send_json({"type": "heartbeat", "ts": int(time.time())})
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        hub.disconnect(websocket)
