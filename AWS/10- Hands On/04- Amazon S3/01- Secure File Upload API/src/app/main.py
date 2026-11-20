"""FastAPI application entry point for the Secure File Upload API."""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.api.health import router as health_router
from app.api.objects import router as objects_router
from app.config import get_settings


def configure_logging(log_level: str) -> None:
    """Configure standard logging and structured application logging."""
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(message)s",
        force=True,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


class RequestContextMiddleware:
    """Attach a request identifier and log HTTP request lifecycle events.

    This pure ASGI middleware avoids the additional task and context behavior
    associated with BaseHTTPMiddleware. It does not log request bodies,
    authorization headers, cookies, or query-string values.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.logger = structlog.get_logger(__name__)

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid.uuid4())
        started_at = time.perf_counter()
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        state = scope.setdefault("state", {})
        state["request_id"] = request_id

        structlog.contextvars.bind_contextvars(request_id=request_id)

        async def send_with_context(message: Message) -> None:
            nonlocal status_code

            if message["type"] == "http.response.start":
                status_code = message["status"]

                headers = list(message.get("headers", []))
                headers.append(
                    (b"x-request-id", request_id.encode("ascii"))
                )

                message = {
                    **message,
                    "headers": headers,
                }

            await send(message)

        try:
            await self.app(scope, receive, send_with_context)
        except Exception:
            self.logger.exception(
                "http_request_failed",
                method=scope.get("method"),
                path=scope.get("path"),
                status_code=status_code,
            )
            raise
        finally:
            duration_ms = round(
                (time.perf_counter() - started_at) * 1000,
                2,
            )

            self.logger.info(
                "http_request_completed",
                method=scope.get("method"),
                path=scope.get("path"),
                status_code=status_code,
                duration_ms=duration_ms,
            )

            structlog.contextvars.clear_contextvars()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize application-level resources and validate configuration."""
    settings = get_settings()
    configure_logging(settings.log_level)

    logger = structlog.get_logger(__name__)

    logger.info(
        "application_starting",
        application=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        aws_region=settings.aws_region,
    )

    app.state.settings = settings

    yield

    logger.info(
        "application_stopping",
        application=settings.app_name,
        environment=settings.environment,
    )


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    is_production = settings.environment in {"production", "prod"}

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Secure API for uploading, retrieving, and managing files "
            "stored in Amazon S3."
        ),
        debug=settings.debug,
        docs_url=None if is_production else "/docs",
        redoc_url=None if is_production else "/redoc",
        openapi_url=None if is_production else "/openapi.json",
        lifespan=lifespan,
    )

    application.add_middleware(RequestContextMiddleware)

    application.include_router(health_router)
    application.include_router(objects_router)

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """Return a consistent response for invalid request data."""
        logger = structlog.get_logger(__name__)

        logger.warning(
            "request_validation_failed",
            request_id=getattr(request.state, "request_id", None),
            method=request.method,
            path=request.url.path,
            error_count=len(exc.errors()),
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "The request contains invalid data.",
                    "details": exc.errors(),
                }
            },
            headers={
                "X-Request-ID": getattr(request.state, "request_id", "")
            },
        )

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Handle unexpected application errors without exposing internals."""
        logger = structlog.get_logger(__name__)
        request_id = getattr(request.state, "request_id", None)

        logger.exception(
            "unhandled_application_exception",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred.",
                    "request_id": request_id,
                }
            },
            headers={
                "X-Request-ID": request_id or ""
            },
        )

    return application


app = create_application()