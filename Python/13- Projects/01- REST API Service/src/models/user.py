"""Domain models for the REST API service."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class User:
    """Represent a user in the REST API domain."""

    id: UUID
    email: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

"""Domain models for the REST API service."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class User:
    """Represent a user in the REST API domain."""

    id: UUID
    email: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime