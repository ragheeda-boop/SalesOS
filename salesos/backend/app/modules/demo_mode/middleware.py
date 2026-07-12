"""DemoModeMiddleware — isolates demo data to separate schema and blocks writes."""

from contextvars import ContextVar

from fastapi import Request
from starlette.responses import JSONResponse

demo_schema_ctx: ContextVar[str | None] = ContextVar("demo_schema", default=None)

WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
DEMO_DB_PREFIX = "demo_"


def get_demo_schema() -> str | None:
    return demo_schema_ctx.get(None)


class DemoModeMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request = Request(scope, receive)
        is_demo = request.headers.get("x-demo-mode", "").lower() == "true"

        if not is_demo:
            return await self.app(scope, receive, send)

        if request.method in WRITE_METHODS:
            response = JSONResponse(
                status_code=403,
                content={
                    "detail": "Write operations are not allowed in demo mode. "
                              "Demo mode is read-only to protect data integrity.",
                    "demo_mode": True,
                },
            )
            await response(scope, receive, send)
            return

        token = demo_schema_ctx.set(DEMO_DB_PREFIX)
        try:
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    headers.append((b"x-demo-mode", b"true"))
                    message["headers"] = headers
                await send(message)

            await self.app(scope, receive, send_wrapper)
        finally:
            demo_schema_ctx.reset(token)
