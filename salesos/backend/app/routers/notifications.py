from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect

from app.dependencies import get_current_tenant_id, get_current_user_id, verify_token
from domains.notifications.models import InMemoryNotificationRepository, Notification
from intelligence.notifications.websocket import WebSocketManager

logger = logging.getLogger(__name__)

router = APIRouter()

_repo = InMemoryNotificationRepository()
_ws_manager = WebSocketManager()


@router.websocket("/notifications/ws")
async def notifications_ws(websocket: WebSocket):
    token = websocket.query_params.get("token", "")
    tenant_id = websocket.query_params.get("tenant_id", "")
    if not token or not tenant_id:
        await websocket.close(code=4001)
        return

    try:
        from app.modules.identity.service import decode_access_token
        payload = decode_access_token(token)
        user_id = payload.get("sub", "")
        token_tenant = payload.get("tenant_id", "")
        if token_tenant and str(token_tenant) != tenant_id:
            await websocket.close(code=4003)
            return
    except Exception:
        await websocket.close(code=4001)
        return

    await websocket.accept()
    await _ws_manager.connect(websocket, tenant_id, user_id)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except (json.JSONDecodeError, KeyError):
                pass
    except WebSocketDisconnect:
        pass
    finally:
        await _ws_manager.disconnect(websocket)


@router.get("/notifications/history")
async def list_notifications(
    limit: int = Query(default=50, le=100),
    tenant_id: str = Depends(get_current_tenant_id),
    user_id: str = Depends(get_current_user_id),
):
    notifs = await _repo.list_by_user(tenant_id, user_id, limit)
    unread = await _repo.count_unread(tenant_id, user_id)
    return {
        "notifications": [
            {
                "id": n.id,
                "type": n.type,
                "title": n.title,
                "body": n.body,
                "data": n.data,
                "read": n.read,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifs
        ],
        "unread_count": unread,
        "total": len(notifs),
    }


@router.post("/notifications/mark-read")
async def mark_notification_read(
    body: dict,
    tenant_id: str = Depends(get_current_tenant_id),
    user_id: str = Depends(get_current_user_id),
):
    notification_id = body.get("notification_id")
    if notification_id:
        ok = await _repo.mark_read(notification_id, tenant_id, user_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Notification not found")
        return {"status": "ok", "notification_id": notification_id}

    all_val = body.get("all", False)
    if all_val:
        count = await _repo.mark_all_read(tenant_id, user_id)
        return {"status": "ok", "marked_read": count}

    raise HTTPException(status_code=400, detail="Provide notification_id or all=true")


@router.get("/notifications/unread-count")
async def unread_count(
    tenant_id: str = Depends(get_current_tenant_id),
    user_id: str = Depends(get_current_user_id),
):
    count = await _repo.count_unread(tenant_id, user_id)
    return {"unread_count": count}


async def create_and_notify(
    tenant_id: str,
    user_id: str,
    notif_type: str,
    title: str,
    body: str,
    data: dict | None = None,
) -> Notification:
    notification = Notification(
        id=uuid.uuid4().hex[:12],
        tenant_id=tenant_id,
        user_id=user_id,
        type=notif_type,
        title=title,
        body=body,
        data=data or {},
    )
    await _repo.create(notification)
    await _ws_manager.send_to_user(tenant_id, user_id, notif_type, {
        "id": notification.id,
        "type": notif_type,
        "title": title,
        "body": body,
        "data": data or {},
        "created_at": notification.created_at.isoformat(),
    })
    return notification


async def broadcast_notification(
    tenant_id: str,
    notif_type: str,
    title: str,
    body: str,
    data: dict | None = None,
) -> Notification:
    notification = Notification(
        id=uuid.uuid4().hex[:12],
        tenant_id=tenant_id,
        user_id="",
        type=notif_type,
        title=title,
        body=body,
        data=data or {},
    )
    await _repo.create(notification)
    await _ws_manager.broadcast(tenant_id, notif_type, {
        "id": notification.id,
        "type": notif_type,
        "title": title,
        "body": body,
        "data": data or {},
        "created_at": notification.created_at.isoformat(),
    })
    return notification
