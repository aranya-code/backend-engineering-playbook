"""Health-check endpoints for the Secure File Upload API.

The liveness endpoint reports whether the application process is responsive.
The readiness endpoint verifies that the application has the configuration
required to serve requests without making an S3 network call.
"""

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

router = APIRouter(
    tags=["Health"],
)


@router.get(
    "/health",
    summary="Application liveness check",
    description=(
        "Confirms that the API process is running and can respond to HTTP requests. "
        "This endpoint does not verify connectivity to external dependencies."
    ),
    status_code=status.HTTP_200_OK,
)
async def health_check() -> dict[str, str]:
    """Return the application liveness status."""
    return {
        "status": "healthy",
    }


@router.get(
    "/ready",
    summary="Application readiness check",
    description=(
        "Checks whether the application has loaded its required configuration. "
        "It does not perform an S3 operation or guarantee that AWS credentials "
        "and bucket permissions are currently valid."
    ),
    status_code=status.HTTP_200_OK,
)
async def readiness_check(request: Request) -> JSONResponse:
    """Report whether the application is configured to accept requests."""
    settings = getattr(request.app.state, "settings", None)

    if settings is None:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "reason": "Application configuration has not been initialized.",
            },
        )

    if not settings.s3_bucket_name:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "reason": "The S3 bucket configuration is missing.",
            },
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "ready",
        },
    )