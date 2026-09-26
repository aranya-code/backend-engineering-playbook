"""User request and response models for the FastAPI MongoDB REST API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Validate data required to create a user."""

    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    active: bool = True


class UserUpdate(BaseModel):
    """Validate mutable user fields."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    active: bool | None = None


class UserResponse(BaseModel):
    """Represent a user returned by the REST API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: EmailStr
    active: bool
    created_at: datetime
    updated_at: datetime

"""User request and response models for the FastAPI MongoDB REST API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Validate data required to create a user."""

    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    active: bool = True


class UserUpdate(BaseModel):
    """Validate mutable user fields."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    active: bool | None = None


class UserResponse(BaseModel):
    """Represent a user returned by the REST API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: EmailStr
    active: bool
    created_at: datetime
    updated_at: datetime