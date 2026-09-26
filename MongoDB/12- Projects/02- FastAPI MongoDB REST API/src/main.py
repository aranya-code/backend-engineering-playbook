"""FastAPI application entry point for the MongoDB REST API."""

from __future__ import annotations

from fastapi import FastAPI
from pymongo import MongoClient

from src.database.connection import get_client
from src.config.settings import get_settings


settings = get_settings()

app = FastAPI(
    title="FastAPI MongoDB REST API",
    version="1.0.0",
    description="Production-oriented REST API backed by MongoDB.",
)


@app.on_event("startup")
def startup() -> None:
    """Initialize the MongoDB connection during application startup."""
    client: MongoClient = get_client()
    client.admin.command("ping")


@app.on_event("shutdown")
def shutdown() -> None:
    """Close the MongoDB connection during application shutdown."""
    get_client().close()


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Return a basic application health response."""
    return {"status": "ok"}


@app.get("/health/database", tags=["Health"])
def database_health_check() -> dict[str, str]:
    """Verify that the API can communicate with MongoDB."""
    get_client().admin.command("ping")
    return {"status": "ok", "database": settings.mongodb_database}

"""FastAPI application entry point for the MongoDB REST API."""

from __future__ import annotations

from fastapi import FastAPI
from pymongo import MongoClient

from src.database.connection import get_client
from src.config.settings import get_settings


settings = get_settings()

app = FastAPI(
    title="FastAPI MongoDB REST API",
    version="1.0.0",
    description="Production-oriented REST API backed by MongoDB.",
)


@app.on_event("startup")
def startup() -> None:
    """Initialize the MongoDB connection during application startup."""
    client: MongoClient = get_client()
    client.admin.command("ping")


@app.on_event("shutdown")
def shutdown() -> None:
    """Close the MongoDB connection during application shutdown."""
    get_client().close()


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Return a basic application health response."""
    return {"status": "ok"}


@app.get("/health/database", tags=["Health"])
def database_health_check() -> dict[str, str]:
    """Verify that the API can communicate with MongoDB."""
    get_client().admin.command("ping")
    return {"status": "ok", "database": settings.mongodb_database}