from fastapi import Request, Response
from sqlalchemy.ext.asyncio import async_sessionmaker
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.config import settings
from app.database import async_session

from .service import AuditService, PostgresAuditRepository


class AuditMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, session_factory: async_sessionmaker | None = None):
        super().__init__(app)
        self.session_factory = session_factory or async_session
        self.excluded_paths = set(settings.audit_excluded_paths)

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        method = request.method

        if any(path.startswith(ex) for ex in self.excluded_paths):
            return await call_next(request)

        response = await call_next(request)

        try:
            if method in ("POST", "PUT", "PATCH", "DELETE") and path.startswith("/api/v1/") or response.status_code == 403:
                tenant_id = request.headers.get("X-Tenant-Id", "")
                auth = request.headers.get("Authorization", "")
                user_id = None
                if auth.startswith("Bearer "):
                    try:
                        from app.modules.identity.service import decode_access_token
                        payload = decode_access_token(auth.replace("Bearer ", ""))
                        user_id = payload.get("sub")
                    except Exception:
                        pass
                if not user_id:
                    api_key = request.headers.get("X-API-Key", "")
                    if api_key:
                        user_id = "api_key_user"

                action = method.lower() if response.status_code != 403 else "permission_denied"

                async with self.session_factory() as db:
                    repo = PostgresAuditRepository(db)
                    service = AuditService(repository=repo)
                    await service.log(
                        tenant_id=tenant_id or "",
                        user_id=user_id,
                        action=action,
                        resource_type=path,
                        resource_id=str(response.status_code) if response.status_code == 403 else None,
                        details={"path": path, "method": method, "status_code": response.status_code},
                        ip_address=request.client.host if request.client else None,
                        user_agent=request.headers.get("user-agent"),
                        request_id=request.headers.get("X-Request-ID"),
                    )
                    await db.commit()
        except Exception:
            pass

        return response
