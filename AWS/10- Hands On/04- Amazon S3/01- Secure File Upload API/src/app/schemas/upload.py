"""Pydantic schemas for upload requests and upload API responses.

These models define the request and response contracts for direct API uploads
and presigned S3 uploads. They validate API data only; file inspection,
content-type enforcement, authorization, and storage operations belong in
their respective application layers.
"""

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class PresignedUploadRequest(BaseModel):
    """Request data required to initiate a presigned S3 upload."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    filename: str = Field(
        min_length=1,
        max_length=255,
        description="Original filename supplied by the client.",
    )
    content_type: str = Field(
        min_length=1,
        max_length=255,
        description="Declared MIME content type of the file.",
    )
    size_bytes: int = Field(
        gt=0,
        description="Expected file size in bytes.",
    )


class PresignedUploadResponse(BaseModel):
    """Response containing a URL for direct client-to-S3 upload."""

    model_config = ConfigDict(extra="forbid")

    object_id: str = Field(
        description="Application-level identifier assigned to the object.",
    )
    upload_url: HttpUrl = Field(
        description="Presigned URL used by the client to upload the object.",
    )
    expires_in: int = Field(
        gt=0,
        description="Number of seconds for which the presigned URL is valid.",
    )
    required_headers: dict[str, str] = Field(
        default_factory=dict,
        description="Headers the client must include when using the presigned URL.",
    )


class ObjectUploadResponse(BaseModel):
    """Response returned after an object upload completes."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    object_id: str = Field(
        description="Application-level identifier assigned to the uploaded object.",
    )
    filename: str = Field(
        min_length=1,
        description="Sanitized original filename.",
    )
    content_type: str = Field(
        min_length=1,
        description="MIME content type associated with the uploaded object.",
    )
    size_bytes: int = Field(
        ge=0,
        description="Uploaded object size in bytes.",
    )