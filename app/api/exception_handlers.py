import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError, UnauthorizedError

logger = logging.getLogger(__name__)


def register_exception_handlers(app) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        headers: dict[str, str] = {}
        if isinstance(exc, UnauthorizedError):
            headers["WWW-Authenticate"] = "Bearer"
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=headers,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc.__class__.__name__)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
