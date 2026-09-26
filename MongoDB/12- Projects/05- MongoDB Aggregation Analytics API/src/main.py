"""MongoDB aggregation analytics API entry point."""

from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(
    title="MongoDB Aggregation Analytics API",
    version="1.0.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Return the application health status."""
    return {"status": "ok"}

"""MongoDB aggregation analytics API entry point."""

from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(
    title="MongoDB Aggregation Analytics API",
    version="1.0.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Return the application health status."""
    return {"status": "ok"}