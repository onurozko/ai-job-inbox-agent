import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.exception_handlers import register_exception_handlers
from app.api.routes import (
    analytics,
    applications,
    assistant,
    auth,
    dashboard,
    emails,
    health,
    profile,
)
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.scheduler import (
    shutdown_background_sync_scheduler,
    start_background_sync_scheduler,
)
from app.db.session import close_db, init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    configure_logging(settings)
    await init_db()
    start_background_sync_scheduler(settings)
    yield
    shutdown_background_sync_scheduler()
    await close_db()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="AI Job Inbox Assistant",
        description="Backend API for AI-powered job application inbox tracking",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": jsonable_encoder(exc.errors()), "path": str(request.url.path)},
        )

    api_prefix = "/api/v1"
    app.include_router(health.router, prefix=api_prefix)
    app.include_router(auth.router, prefix=api_prefix)
    app.include_router(profile.router, prefix=api_prefix)
    app.include_router(dashboard.router, prefix=api_prefix)
    app.include_router(analytics.router, prefix=api_prefix)
    app.include_router(assistant.router, prefix=api_prefix)
    app.include_router(emails.router, prefix=api_prefix)
    app.include_router(applications.router, prefix=api_prefix)

    return app


app = create_app()
