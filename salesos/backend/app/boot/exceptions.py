from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import settings


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        import traceback

        logger = getattr(request.app.state, "logger", None)
        if logger:
            logger.exception("Unhandled exception", method=request.method, path=request.url.path)
        else:
            traceback.print_exc()
        detail = "An unexpected error occurred" if settings.env == "production" else str(exc)
        return JSONResponse(
            status_code=500,
            content={"detail": detail},
        )
