"""Data models for requests and responses handled by the async API client."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class APIResponse:
    """Represent a normalized successful API response."""

    status_code: int
    data: Any
    request_id: str | None = None
    received_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class User:
    """Represent a user returned by the external API."""

    id: UUID
    email: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class APIError:
    """Represent structured error information returned by an API."""

    status_code: int
    message: str
    code: str | None = None
    details: Any = None
    request_id: str | None = None

"""Data models for requests and responses handled by the async API client."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class APIResponse:
    """Represent a normalized successful API response."""

    status_code: int
    data: Any
    request_id: str | None = None
    received_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class User:
    """Represent a user returned by the external API."""

    id: UUID
    email: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class APIError:
    """Represent structured error information returned by an API."""

    status_code: int
    message: str
    code: str | None = None
    details: Any = None
    request_id: str | None = None