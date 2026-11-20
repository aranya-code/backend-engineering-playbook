"""FastAPI application entry point for the S3 document ingestion pipeline.

The API layer exposes document submission and processing-status endpoints.
AWS operations and document-processing logic remain in dedicated service and
route modules rather than being implemented in this module.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes.documents import router as documents_router
from api.routes.processing_status import router as processing_status_router


def _configure_logging() -> None:
    """Configure application logging for local and Lambda environments."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    if log_level not in logging.getLevelNamesMapping():
        log_level = "INFO"

    logging.basicConfig(
        level=log_level,
        format=(
            "%(asctime)s %(levelname)s "
            "%(name)s %(message)s"
        ),
        force=True,
    )


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown.

    AWS clients are intentionally not initialized here. Route and service
    modules should manage their own dependencies so that application startup
    does not require an active AWS connection.
    """
    logger = logging.getLogger(__name__)
    logger.info("Document ingestion API starting.")

    try:
        yield
    finally:
        logger.info("Document ingestion API shutting down.")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    _configure_logging()

    application = FastAPI(
        title=os.getenv(
            "API_TITLE",
            "S3 Document Ingestion API",
        ),
        description=(
            "API for submitting documents to Amazon S3 and retrieving "
            "their ingestion metadata and processing status."
        ),
        version=os.getenv("API_VERSION", "1.0.0"),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    allowed_origins = [
        origin.strip()
        for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
        if origin.strip()
    ]

    if allowed_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type"],
        )

    @application.get(
        "/health",
        tags=["Health"],
        summary="Check API liveness",
        response_class=JSONResponse,
    )
    async def health_check() -> JSONResponse:
        """Return the API process health status.

        This endpoint confirms that the application process is responsive.
        It does not verify connectivity to S3, DynamoDB, or SQS.
        """
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "service": "document-ingestion-api",
            },
        )

    application.include_router(documents_router)
    application.include_router(processing_status_router)

    return application


app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
        reload=os.getenv("API_RELOAD", "false").lower() == "true",
    )