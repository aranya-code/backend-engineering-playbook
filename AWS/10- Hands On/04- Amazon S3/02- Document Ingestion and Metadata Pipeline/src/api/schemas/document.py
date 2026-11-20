"""Pydantic schemas for document ingestion API requests and responses.

These schemas define the public API contract for document submission and
processing metadata. They intentionally avoid exposing internal AWS SDK
responses or DynamoDB implementation details.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProcessingStatus(str, Enum):
    """Supported document-processing lifecycle states."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DocumentUploadResponse(BaseModel):
    """Response returned after a document has been accepted for ingestion."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    object_id: str = Field(
        ...,
        min_length=1,
        max_length=1024,
        description="Application-level identifier for the uploaded document.",
        examples=["documents-bucket/incoming/7f3a9c2d.pdf"],
    )
    bucket_name: str = Field(
        ...,
        min_length=3,
        max_length=63,
        description="S3 bucket containing the uploaded document.",
    )
    object_key: str = Field(
        ...,
        min_length=1,
        max_length=1024,
        description="S3 object key assigned to the uploaded document.",
    )
    filename: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Original filename supplied by the client.",
    )
    content_type: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Declared media type of the uploaded document.",
    )
    size_bytes: int = Field(
        ...,
        gt=0,
        description="Size of the uploaded document in bytes.",
    )
    processing_status: ProcessingStatus = Field(
        default=ProcessingStatus.PENDING,
        description="Initial processing state assigned to the document.",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Human-readable upload acceptance message.",
    )


class DocumentMetadataResponse(BaseModel):
    """Document metadata extracted and persisted by the ingestion workflow."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    object_id: str = Field(
        ...,
        min_length=1,
        max_length=1024,
        description="Application-level identifier for the document.",
    )
    bucket_name: str = Field(
        ...,
        min_length=3,
        max_length=63,
        description="S3 bucket containing the document.",
    )
    object_key: str = Field(
        ...,
        min_length=1,
        max_length=1024,
        description="S3 object key.",
    )
    filename: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Original document filename.",
    )
    content_type: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Document media type.",
    )
    size_bytes: int = Field(
        ...,
        gt=0,
        description="Document size in bytes.",
    )
    etag: str | None = Field(
        default=None,
        description="S3 entity tag associated with the stored object.",
    )
    version_id: str | None = Field(
        default=None,
        description="S3 version identifier when bucket versioning is enabled.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted document metadata.",
    )
    processing_status: ProcessingStatus = Field(
        default=ProcessingStatus.PENDING,
        description="Current document-processing state.",
    )
    created_at: datetime | None = Field(
        default=None,
        description="Timestamp when the metadata record was created.",
    )
    updated_at: datetime | None = Field(
        default=None,
        description="Timestamp when the metadata record was last updated.",
    )


class ProcessingStatusResponse(BaseModel):
    """Response returned when a client requests document processing status."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    object_id: str = Field(
        ...,
        min_length=1,
        max_length=1024,
        description="Application-level identifier for the document.",
    )
    processing_status: ProcessingStatus = Field(
        ...,
        description="Latest document-processing state.",
    )
    status_message: str | None = Field(
        default=None,
        max_length=4000,
        description="Latest processing status message, when available.",
    )
    created_at: datetime | None = Field(
        default=None,
        description="Timestamp when the status record was created.",
    )
    updated_at: datetime | None = Field(
        default=None,
        description="Timestamp when the status record was last updated.",
    )
    started_at: datetime | None = Field(
        default=None,
        description="Timestamp when document processing started.",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="Timestamp when document processing completed.",
    )
    failed_at: datetime | None = Field(
        default=None,
        description="Timestamp when document processing failed.",
    )


class APIErrorResponse(BaseModel):
    """Consistent error response schema for API documentation."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    detail: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Human-readable description of the API error.",
    )