from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)

_STALE_TIMEOUT = 60.0
_HEARTBEAT_INTERVAL = 30.0
_MAX_CONNECTIONS_PER_TENANT = 100


class _ConnectionMetrics:
    """Per-process connection metrics tracked in-memory."""

    def __init__(self) -> None:
        self.total_connections_opened: int = 0
        self.total_connections_closed: int = 0
        self.total_heartbeats_sent: int = 0
        self.total_heartbeats_received: int = 0
        self.total_messages_sent: int = 0
        self.total_messages_received: int = 0
        self.rejected_by_limit: int = 0

    def snapshot(self) -> dict[str, int]:
        return {
            "total_connections_opened": self.total_connections_opened,
            "total_connections_closed": self.total_connections_closed,
            "total_heartbeats_sent": self.total_heartbeats_sent,
            "total_heartbeats_received": self.total_heartbeats_received,
            "total_messages_sent": self.total_messages_sent,
            "total_messages_received": self.total_messages_received,
            "rejected_by_limit": self.rejected_by_limit,
        }


class WebSocketManager:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._connections: dict[int, dict[str, Any]] = {}
        self._metrics = _ConnectionMetrics()
        self._tenant_counts: dict[str, int] = defaultdict(int)

    async def connect(self, websocket: Any, tenant_id: str, user_id: str) -> bool:
        """Register a new connection. Returns False if rejected by tenant limit."""
        async with self._lock:
            current_count = self._tenant_counts.get(tenant_id, 0)
            if current_count >= _MAX_CONNECTIONS_PER_TENANT:
                self._metrics.rejected_by_limit += 1
                logger.warning(
                    "WS rejected: tenant=%s at limit %d/%d",
                    tenant_id, current_count, _MAX_CONNECTIONS_PER_TENANT,
                )
                return False

            conn_id = id(websocket)
            self._connections[conn_id] = {
                "ws": websocket,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "connected_at": time.time(),
                "last_active": time.time(),
                "last_pong": time.time(),
            }
            self._tenant_counts[tenant_id] = current_count + 1
            self._metrics.total_connections_opened += 1

        logger.info(
            "WS connected: tenant=%s user=%s conn=%s active=%d",
            tenant_id, user_id, conn_id, self._metrics.total_connections_opened - self._metrics.total_connections_closed,
        )
        return True

    async def disconnect(self, websocket: Any) -> None:
        conn_id = id(websocket)
        async with self._lock:
            info = self._connections.pop(conn_id, None)
            if info:
                tid = info["tenant_id"]
                self._tenant_counts[tid] = max(0, self._tenant_counts.get(tid, 1) - 1)
                self._metrics.total_connections_closed += 1
        logger.info("WS disconnected: conn=%s", conn_id)

    async def handle_pong(self, websocket: Any) -> None:
        conn_id = id(websocket)
        async with self._lock:
            info = self._connections.get(conn_id)
            if info:
                info["last_pong"] = time.time()
                info["last_active"] = time.time()
                self._metrics.total_heartbeats_received += 1

    async def heartbeat_loop(self, interval: float = _HEARTBEAT_INTERVAL) -> None:
        """Send ping to all connections every *interval* seconds; evict stale ones."""
        while True:
            await asyncio.sleep(interval)
            now = time.time()
            stale: list[int] = []

            async with self._lock:
                for conn_id, info in list(self._connections.items()):
                    ws = info.get("ws")
                    if ws is None:
                        stale.append(conn_id)
                        continue

                    # Evict connections that missed 2 heartbeat cycles
                    if now - info["last_pong"] > interval * 3:
                        stale.append(conn_id)
                        continue

                    try:
                        await ws.send_text(json.dumps({
                            "type": "ping",
                            "ts": now,
                        }))
                        info["last_active"] = now
                        self._metrics.total_heartbeats_sent += 1
                    except Exception:
                        stale.append(conn_id)

                for conn_id in stale:
                    info = self._connections.pop(conn_id, None)
                    if info:
                        tid = info["tenant_id"]
                        self._tenant_counts[tid] = max(0, self._tenant_counts.get(tid, 1) - 1)
                        self._metrics.total_connections_closed += 1

            if stale:
                logger.info("Heartbeat evicted %d stale connections", len(stale))

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
                    self._metrics.total_messages_sent += 1
                    sent += 1
                except Exception:
                    stale.append(conn_id)

            for conn_id in stale:
                info = self._connections.pop(conn_id, None)
                if info:
                    tid = info["tenant_id"]
                    self._tenant_counts[tid] = max(0, self._tenant_counts.get(tid, 1) - 1)
                    self._metrics.total_connections_closed += 1

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
                    self._metrics.total_messages_sent += 1
                    sent += 1
                except Exception:
                    stale.append(conn_id)

            for conn_id in stale:
                info = self._connections.pop(conn_id, None)
                if info:
                    tid = info["tenant_id"]
                    self._tenant_counts[tid] = max(0, self._tenant_counts.get(tid, 1) - 1)
                    self._metrics.total_connections_closed += 1

        return sent

    async def cleanup_stale(self) -> int:
        now = time.time()
        stale: list[int] = []
        async with self._lock:
            for conn_id, info in list(self._connections.items()):
                if now - info["last_active"] > _STALE_TIMEOUT:
                    stale.append(conn_id)
            for conn_id in stale:
                info = self._connections.pop(conn_id, None)
                if info:
                    tid = info["tenant_id"]
                    self._tenant_counts[tid] = max(0, self._tenant_counts.get(tid, 1) - 1)
                    self._metrics.total_connections_closed += 1
        if stale:
            logger.info("Cleanup removed %d stale connections", len(stale))
        return len(stale)

    @property
    def active_connections(self) -> int:
        return len(self._connections)

    async def get_connection_count(self) -> int:
        async with self._lock:
            return len(self._connections)

    async def get_metrics(self) -> dict[str, Any]:
        """Return current connection metrics snapshot."""
        async with self._lock:
            by_tenant: dict[str, int] = dict(self._tenant_counts)
        return {
            **self._metrics.snapshot(),
            "active_connections": len(self._connections),
            "by_tenant": by_tenant,
            "max_per_tenant": _MAX_CONNECTIONS_PER_TENANT,
            "heartbeat_interval_seconds": _HEARTBEAT_INTERVAL,
        }

    async def cleanup_task(self, interval: float = 30.0) -> None:
        while True:
            await asyncio.sleep(interval)
            await self.cleanup_stale()
