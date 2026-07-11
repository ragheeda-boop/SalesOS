from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

_STALE_TIMEOUT = 60.0


class WebSocketManager:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._connections: dict[str, dict[str, Any]] = {}

    async def connect(self, websocket: Any, tenant_id: str, user_id: str) -> None:
        conn_id = id(websocket)
        async with self._lock:
            self._connections[conn_id] = {
                "ws": websocket,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "connected_at": time.time(),
                "last_active": time.time(),
            }
        logger.info("WS connected: tenant=%s user=%s conn=%s", tenant_id, user_id, conn_id)

    async def disconnect(self, websocket: Any) -> None:
        conn_id = id(websocket)
        async with self._lock:
            self._connections.pop(conn_id, None)
        logger.info("WS disconnected: conn=%s", conn_id)

    async def broadcast(self, tenant_id: str, event_type: str, data: Any) -> int:
        payload = json.dumps({"type": event_type, "data": data})
        sent = 0
        stale: list[int] = []

        async with self._lock:
            for conn_id, info in list(self._connections.items()):
                if info["tenant_id"] != tenant_id:
                    continue
                ws = info.get("ws")
                if ws is None:
                    stale.append(conn_id)
                    continue
                try:
                    await ws.send_text(payload)
                    info["last_active"] = time.time()
                    sent += 1
                except Exception:
                    stale.append(conn_id)

            for conn_id in stale:
                self._connections.pop(conn_id, None)

        if stale:
            logger.info("Cleaned %d stale WS connections", len(stale))
        return sent

    async def send_to_user(self, tenant_id: str, user_id: str, event_type: str, data: Any) -> int:
        payload = json.dumps({"type": event_type, "data": data})
        sent = 0
        stale: list[int] = []

        async with self._lock:
            for conn_id, info in list(self._connections.items()):
                if info["tenant_id"] != tenant_id or info["user_id"] != user_id:
                    continue
                ws = info.get("ws")
                if ws is None:
                    stale.append(conn_id)
                    continue
                try:
                    await ws.send_text(payload)
                    info["last_active"] = time.time()
                    sent += 1
                except Exception:
                    stale.append(conn_id)

            for conn_id in stale:
                self._connections.pop(conn_id, None)

        return sent

    async def cleanup_stale(self) -> int:
        now = time.time()
        stale: list[int] = []
        async with self._lock:
            for conn_id, info in list(self._connections.items()):
                if now - info["last_active"] > _STALE_TIMEOUT:
                    stale.append(conn_id)
            for conn_id in stale:
                self._connections.pop(conn_id, None)
        if stale:
            logger.info("Cleanup removed %d stale connections", len(stale))
        return len(stale)

    @property
    def active_connections(self) -> int:
        return len(self._connections)

    async def get_connection_count(self) -> int:
        async with self._lock:
            return len(self._connections)

    async def cleanup_task(self, interval: float = 30.0) -> None:
        while True:
            await asyncio.sleep(interval)
            await self.cleanup_stale()
