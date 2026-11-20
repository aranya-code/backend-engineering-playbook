"""S3 storage operations for the document ingestion pipeline.

Provides a reusable Boto3 service for retrieving document metadata and
document content from Amazon S3.

The service accepts an injectable S3 client to support unit testing with
Moto or a mocked Boto3 client.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import boto3
from botocore.client import BaseClient
from botocore.config import Config

logger = logging.getLogger(__name__)

DEFAULT_AWS_REGION = "ap-south-1"
DEFAULT_MAX_POOL_CONNECTIONS = 50

S3_CLIENT_CONFIG = Config(
    retries={
        "max_attempts": 3,
        "mode": "standard",
    },
    max_pool_connections=DEFAULT_MAX_POOL_CONNECTIONS,
    connect_timeout=5,
    read_timeout=60,
)


class S3Storage:
    """Encapsulate S3 object retrieval operations."""

    def __init__(
        self,
        s3_client: BaseClient | None = None,
        *,
        region_name: str | None = None,
    ) -> None:
        """Initialize the S3 storage service.

        Args:
            s3_client: Optional preconfigured Boto3 S3 client.
            region_name: AWS Region used when creating a client.
                Defaults to the AWS_REGION environment variable or
                ap-south-1.
        """
        self.region_name = (
            region_name
            or os.getenv("AWS_REGION")
            or DEFAULT_AWS_REGION
        )

        self.client = s3_client or boto3.client(
            "s3",
            region_name=self.region_name,
            config=S3_CLIENT_CONFIG,
        )

    @staticmethod
    def _validate_bucket_name(bucket_name: str) -> None:
        """Validate the bucket name supplied to an operation."""
        if not isinstance(bucket_name, str) or not bucket_name.strip():
            raise ValueError("S3 bucket name must be a non-empty string.")

        if bucket_name != bucket_name.strip():
            raise ValueError("S3 bucket name cannot contain surrounding whitespace.")

    @staticmethod
    def _validate_object_key(object_key: str) -> None:
        """Validate the object key supplied to an operation."""
        if not isinstance(object_key, str) or not object_key:
            raise ValueError("S3 object key must be a non-empty string.")

        if object_key != object_key.strip():
            raise ValueError("S3 object key cannot contain surrounding whitespace.")

        if len(object_key.encode("utf-8")) > 1024:
            raise ValueError(
                "S3 object key cannot exceed 1,024 UTF-8 bytes."
            )

        if any(
            ord(character) < 32 or ord(character) == 127
            for character in object_key
        ):
            raise ValueError(
                "S3 object key cannot contain control characters."
            )

    @classmethod
    def _validate_object_location(
        cls,
        bucket_name: str,
        object_key: str,
    ) -> None:
        """Validate the bucket and object key together."""
        cls._validate_bucket_name(bucket_name)
        cls._validate_object_key(object_key)

    def head_object(
        self,
        *,
        bucket_name: str,
        object_key: str,
    ) -> dict[str, Any]:
        """Retrieve S3 object metadata without downloading its content.

        Args:
            bucket_name: S3 bucket containing the document.
            object_key: Complete S3 object key.

        Returns:
            The raw Boto3 HeadObject response. This includes fields such as
            ContentLength, ContentType, ETag, LastModified, VersionId,
            Metadata, and ServerSideEncryption when available.

        Raises:
            ValueError: If the bucket name or object key is invalid.
            botocore.exceptions.ClientError: If S3 rejects the request.
            botocore.exceptions.BotoCoreError: If the SDK encounters an
                underlying transport or client error.
        """
        self._validate_object_location(bucket_name, object_key)

        logger.debug(
            "Retrieving S3 object metadata.",
            extra={
                "bucket_name": bucket_name,
                "object_key": object_key,
            },
        )

        response = self.client.head_object(
            Bucket=bucket_name,
            Key=object_key,
        )

        logger.info(
            "Retrieved S3 object metadata.",
            extra={
                "bucket_name": bucket_name,
                "object_key": object_key,
                "size_bytes": response.get("ContentLength"),
                "etag": response.get("ETag"),
            },
        )

        return response

    def get_object(
        self,
        *,
        bucket_name: str,
        object_key: str,
    ) -> bytes:
        """Download an S3 object and return its content as bytes.

        The response streaming body is always closed, including when reading
        fails. Returning bytes gives metadata extractors a predictable input
        type without exposing an unmanaged streaming response.

        Args:
            bucket_name: S3 bucket containing the document.
            object_key: Complete S3 object key.

        Returns:
            Complete document content as bytes.

        Raises:
            ValueError: If the bucket name or object key is invalid.
            botocore.exceptions.ClientError: If S3 rejects the request.
            botocore.exceptions.BotoCoreError: If the SDK encounters an
                underlying transport or client error.
            OSError: If reading the streaming response fails.
        """
        self._validate_object_location(bucket_name, object_key)

        logger.debug(
            "Downloading S3 object.",
            extra={
                "bucket_name": bucket_name,
                "object_key": object_key,
            },
        )

        response = self.client.get_object(
            Bucket=bucket_name,
            Key=object_key,
        )

        body = response.get("Body")

        if body is None:
            raise ValueError(
                f"S3 returned no response body for object {object_key!r}."
            )

        try:
            document_content = body.read()
        finally:
            body.close()

        if not isinstance(document_content, bytes):
            raise ValueError(
                f"S3 returned an invalid response body for object {object_key!r}."
            )

        if not document_content:
            raise ValueError(
                f"S3 object {object_key!r} contains no document content."
            )

        logger.info(
            "Downloaded S3 object.",
            extra={
                "bucket_name": bucket_name,
                "object_key": object_key,
                "size_bytes": len(document_content),
            },
        )

        return document_content