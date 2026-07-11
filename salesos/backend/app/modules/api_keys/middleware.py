from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .service import ApiKeyService


class ApiKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
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
        return await call_next(request)
