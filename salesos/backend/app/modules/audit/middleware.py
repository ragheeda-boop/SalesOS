import asyncio
import logging

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.config import settings
from app.database import async_session

from .service import AuditService, PostgresAuditRepository

logger = logging.getLogger(__name__)

# Bound post-response audit so idle-DB / pool checkout cannot hold the ASGI
# cycle (IL-2A: evaluate persisted ~100ms but client waited 20–60s with no body).
_AUDIT_WRITE_TIMEOUT_SECONDS = 5.0


class AuditMiddleware:
    """Log audit entries for state-changing API requests.

    Uses ASGI __call__ pattern (not BaseHTTPMiddleware) to avoid
    body streaming deadlocks with nested middleware + exception handlers.

    Audit DB writes are scheduled off the request critical path — awaiting
    them after ``send`` still keeps the ASGI app from returning and can
    stall proxies/clients until pool/command timeouts elapse.
    """

    def __init__(self, app, session_factory: async_sessionmaker | None = None):
        self.app = app
        self.session_factory = session_factory or async_session
        self.excluded_paths = set(settings.audit_excluded_paths)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        path = scope.get("path", "")
        method = scope.get("method", "GET")

        if any(path.startswith(ex) for ex in self.excluded_paths):
            return await self.app(scope, receive, send)

        if method not in ("POST", "PUT", "PATCH", "DELETE") and not path.startswith("/api/v1/"):
            return await self.app(scope, receive, send)

        # Capture headers before passing through
        raw_headers = dict(scope.get("headers", []))
        status_code = 0

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
            await send(message)

        await self.app(scope, receive, send_wrapper)

        should_audit = (
            method in ("POST", "PUT", "PATCH", "DELETE") and path.startswith("/api/v1/")
        ) or status_code == 403
        if should_audit:
            self._schedule_audit_log(scope, raw_headers, method, path, status_code)

    def _schedule_audit_log(
        self,
        scope: dict,
        raw_headers: dict,
        method: str,
        path: str,
        status_code: int,
    ) -> None:
        """Fire-and-forget audit write — never block ASGI return on DB."""

        async def _write() -> None:
            try:
                tenant_id = ""
                auth = raw_headers.get(b"authorization", b"").decode()
                user_id = None
                if auth.startswith("Bearer "):
                    try:
                        from app.modules.identity.service import decode_access_token

                        payload = decode_access_token(auth.replace("Bearer ", ""))
                        user_id = payload.get("sub")
                        # Prefer verified JWT tenant over client-controlled header (14-05).
                        tid = payload.get("tenant_id")
                        if tid:
                            tenant_id = str(tid)
                    except Exception:
                        pass
                if not tenant_id:
                    tenant_id = raw_headers.get(b"x-tenant-id", b"").decode()
                if not user_id:
                    api_key = raw_headers.get(b"x-api-key", b"").decode()
                    if api_key:
                        user_id = "api_key_user"

                action = method.lower() if status_code != 403 else "permission_denied"

                async def _persist() -> None:
                    async with self.session_factory() as db:
                        repo = PostgresAuditRepository(db)
                        service = AuditService(repository=repo)
                        await service.log(
                            tenant_id=tenant_id or "",
                            user_id=user_id,
                            action=action,
                            resource_type=path,
                            resource_id=str(status_code) if status_code == 403 else None,
                            details={"path": path, "method": method, "status_code": status_code},
                            ip_address=scope.get("client")[0] if scope.get("client") else None,
                            user_agent=raw_headers.get(b"user-agent", b"").decode() or None,
                            request_id=raw_headers.get(b"x-request-id", b"").decode() or None,
                        )
                        await db.commit()

                await asyncio.wait_for(_persist(), timeout=_AUDIT_WRITE_TIMEOUT_SECONDS)
            except TimeoutError:
                logger.warning(
                    "audit_middleware.write_timeout path=%s status=%s",
                    path,
                    status_code,
                )
            except Exception:
                pass

        try:
            asyncio.get_running_loop().create_task(_write())
        except Exception:
            pass
