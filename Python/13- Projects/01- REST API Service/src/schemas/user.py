"""Request and response schemas for user API operations."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Validate input required to create a user."""

    email: EmailStr
    name: str = Field(min_length=1, max_length=255)


class UserResponse(BaseModel):
    """Represent a user returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

"""Request and response schemas for user API operations."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Validate input required to create a user."""

    email: EmailStr
    name: str = Field(min_length=1, max_length=255)


class UserResponse(BaseModel):
    """Represent a user returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime