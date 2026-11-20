"""Pydantic schemas for S3 object metadata and API responses.

This module defines response models representing stored objects and their
metadata. Request validation and upload-specific schemas are maintained
separately in upload.py.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ObjectMetadataResponse(BaseModel):
    """Metadata returned when retrieving information about a stored object."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    object_id: str = Field(
        description="Application-level identifier assigned to the stored object.",
    )
    filename: str = Field(
        min_length=1,
        description="Sanitized original filename.",
    )
    content_type: str = Field(
        min_length=1,
        description="MIME content type associated with the stored object.",
    )
    size_bytes: int = Field(
        ge=0,
        description="Stored object size in bytes.",
    )
    last_modified: datetime | None = Field(
        default=None,
        description="Timestamp of the last S3 object modification.",
    )
    etag: str | None = Field(
        default=None,
        description="S3 entity tag returned for the stored object.",
    )


class ObjectDeletionResponse(BaseModel):
    """Response model for an object deletion operation."""

    model_config = ConfigDict(extra="forbid")

    object_id: str = Field(
        description="Application-level identifier of the deleted object.",
    )
    deleted: bool = Field(
        description="Indicates whether the deletion operation completed.",
    )