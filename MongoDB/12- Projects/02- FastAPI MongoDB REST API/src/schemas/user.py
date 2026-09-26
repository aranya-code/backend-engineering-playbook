"""User API schemas for the FastAPI MongoDB REST API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for creating a user."""

    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    active: bool = True


class UserUpdate(BaseModel):
    """Schema for partially updating a user."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    active: bool | None = None


class UserResponse(BaseModel):
    """Schema returned by user API endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: EmailStr
    active: bool
    created_at: datetime
    updated_at: datetime

"""User API schemas for the FastAPI MongoDB REST API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for creating a user."""

    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    active: bool = True


class UserUpdate(BaseModel):
    """Schema for partially updating a user."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    active: bool | None = None


class UserResponse(BaseModel):
    """Schema returned by user API endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: EmailStr
    active: bool
    created_at: datetime
    updated_at: datetime