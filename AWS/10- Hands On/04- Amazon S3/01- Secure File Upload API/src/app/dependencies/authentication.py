"""Authentication and authorization dependencies for the Secure File Upload API.

JWT bearer tokens are validated using the application's configured signing
algorithm and secret. The authenticated principal is returned as a dictionary
so API routes can consistently resolve its subject identifier.
"""

from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import Settings, get_settings

bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="JWT Bearer Authentication",
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Validate the bearer token and return the authenticated principal.

    Args:
        credentials: Bearer credentials extracted from the Authorization header.
        settings: Application settings containing JWT validation configuration.

    Returns:
        Decoded JWT claims for the authenticated user.

    Raises:
        HTTPException: If credentials are missing, invalid, expired, or lack
            a usable subject identifier.
    """
    unauthorized_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized_exception

    if credentials.scheme.lower() != "bearer":
        raise unauthorized_exception

    if settings.jwt_secret_key is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured.",
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iat": True,
                "require_exp": True,
                "require_sub": True,
            },
        )
    except JWTError:
        raise unauthorized_exception from None

    subject = payload.get("sub")

    if not isinstance(subject, str) or not subject.strip():
        raise unauthorized_exception

    return payload