from starlette.requests import Request

from .service import ApiKeyService


class ApiKeyMiddleware:
    """Validate API key from X-API-Key header.

    Uses ASGI __call__ pattern (not BaseHTTPMiddleware) to avoid
    body streaming deadlocks with nested middleware + exception handlers.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request = Request(scope, receive)
        api_key = request.headers.get("X-API-Key", "")
        if api_key and not request.headers.get("Authorization", "").startswith("Bearer "):
            db_session = getattr(request.app.state, "db_session_factory", None)
            if db_session:
                async with db_session() as db:
                    service = ApiKeyService(db=db)
                    key_record = await service.validate(api_key)
                    if key_record:
                        request.state.api_key_authenticated = True
                        request.state.api_key_user_id = str(key_record.user_id)
                        request.state.api_key_tenant_id = str(key_record.tenant_id)
                        request.state.api_key_scopes = key_record.scopes.split(",") if key_record.scopes else []
                    else:
                        request.state.api_key_authenticated = False
        await self.app(scope, receive, send)
