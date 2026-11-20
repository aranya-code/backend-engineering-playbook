"""S3 object storage operations for the Secure File Upload API.

This service encapsulates Boto3 interactions for uploading, inspecting,
downloading, and deleting objects in the configured S3 bucket.

Application-level authorization, filename validation, object-key generation,
and upload metadata validation belong in their respective layers. This service
accepts server-generated object keys and validated metadata.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any, BinaryIO

import boto3
import structlog
from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.config import Settings


class S3OperationError(RuntimeError):
    """Raised when an S3 object operation fails."""

    def __init__(
        self,
        message: str,
        *,
        operation: str,
        object_key: str,
        error_code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.operation = operation
        self.object_key = object_key
        self.error_code = error_code


class S3ObjectNotFoundError(S3OperationError):
    """Raised when an S3 object does not exist."""


class S3Service:
    """Perform object operations against the application's configured bucket.

    The service uses the standard AWS credential provider chain when creating
    its own client. In production, prefer IAM roles and temporary credentials
    instead of static access keys.

    Args:
        settings: Application settings containing the bucket and AWS Region.
        s3_client: Optional Boto3 S3 client for dependency injection and tests.
    """

    def __init__(
        self,
        settings: Settings,
        s3_client: BaseClient | None = None,
    ) -> None:
        self.settings = settings
        self.logger = structlog.get_logger(__name__)

        self._s3_client = s3_client or boto3.client(
            "s3",
            region_name=settings.aws_region,
            config=Config(
                signature_version="s3v4",
                retries={
                    "max_attempts": 3,
                    "mode": "standard",
                },
            ),
        )

    def upload_fileobj(
        self,
        fileobj: BinaryIO,
        object_key: str,
        content_type: str,
        metadata: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Upload a file-like object to the configured S3 bucket.

        Args:
            fileobj: Binary file-like object positioned at the beginning of
                the content.
            object_key: Server-generated S3 object key.
            content_type: Validated MIME content type.
            metadata: Optional custom S3 object metadata.

        Returns:
            A normalized result containing the object key, ETag, and version
            identifier when returned by S3.

        Raises:
            ValueError: If the object key, content type, metadata, or file
                object is invalid.
            S3OperationError: If the S3 upload fails.

        Notes:
            The caller is responsible for enforcing upload-size limits and
            validating file contents. This method does not buffer the entire
            file in application memory.
        """
        self._validate_object_key(object_key)
        normalized_content_type = self._validate_content_type(content_type)
        normalized_metadata = self._normalize_metadata(metadata)

        if not hasattr(fileobj, "read") or not callable(fileobj.read):
            raise ValueError("A readable binary file object is required.")

        if hasattr(fileobj, "seekable") and fileobj.seekable():
            try:
                fileobj.seek(0)
            except (OSError, ValueError) as exc:
                raise ValueError(
                    "The file object could not be positioned for upload."
                ) from exc

        extra_args: dict[str, Any] = {
            "ContentType": normalized_content_type,
        }

        if normalized_metadata:
            extra_args["Metadata"] = normalized_metadata

        kms_key_id = self.settings.s3_kms_key_id

        if kms_key_id:
            extra_args["ServerSideEncryption"] = "aws:kms"
            extra_args["SSEKMSKeyId"] = kms_key_id

        try:
            self._s3_client.upload_fileobj(
                Fileobj=fileobj,
                Bucket=self.settings.s3_bucket_name,
                Key=object_key,
                ExtraArgs=extra_args,
            )
        except (BotoCoreError, ClientError) as exc:
            raise self._build_operation_error(
                exc,
                operation="upload",
                object_key=object_key,
                message="Unable to upload the object to S3.",
            ) from exc

        try:
            metadata_result = self.head_object(object_key)
        except S3OperationError:
            self.logger.exception(
                "s3_upload_post_verification_failed",
                object_key=object_key,
                bucket=self.settings.s3_bucket_name,
            )
            raise

        self.logger.info(
            "s3_object_uploaded",
            object_key=object_key,
            bucket=self.settings.s3_bucket_name,
            size_bytes=metadata_result["size_bytes"],
        )

        return {
            "object_key": object_key,
            "etag": metadata_result["etag"],
            "version_id": metadata_result.get("version_id"),
        }

    def head_object(self, object_key: str) -> dict[str, Any]:
        """Retrieve metadata for an existing S3 object.

        Args:
            object_key: S3 object key to inspect.

        Returns:
            Normalized object metadata containing size, content type,
            modification time, ETag, custom metadata, and version identifier
            when available.

        Raises:
            ValueError: If the object key is invalid.
            S3ObjectNotFoundError: If S3 reports that the object does not exist.
            S3OperationError: If the metadata request fails.
        """
        self._validate_object_key(object_key)

        try:
            response = self._s3_client.head_object(
                Bucket=self.settings.s3_bucket_name,
                Key=object_key,
            )
        except (BotoCoreError, ClientError) as exc:
            error_code = self._get_error_code(exc)

            if error_code in {"404", "NoSuchKey", "NotFound"}:
                raise S3ObjectNotFoundError(
                    "The requested S3 object does not exist.",
                    operation="head_object",
                    object_key=object_key,
                    error_code=error_code,
                ) from exc

            raise self._build_operation_error(
                exc,
                operation="head_object",
                object_key=object_key,
                message="Unable to retrieve S3 object metadata.",
            ) from exc

        return {
            "object_key": object_key,
            "size_bytes": response.get("ContentLength", 0),
            "content_type": response.get("ContentType"),
            "last_modified": response.get("LastModified"),
            "etag": response.get("ETag"),
            "metadata": response.get("Metadata", {}),
            "version_id": response.get("VersionId"),
            "server_side_encryption": response.get("ServerSideEncryption"),
            "ssekms_key_id": response.get("SSEKMSKeyId"),
        }

    def get_object(self, object_key: str) -> dict[str, Any]:
        """Retrieve an S3 object response.

        The returned response contains a streaming body. The caller must
        consume or close that body to release the underlying HTTP connection.

        Args:
            object_key: S3 object key to download.

        Returns:
            The Boto3 GetObject response, including its streaming ``Body``.

        Raises:
            ValueError: If the object key is invalid.
            S3ObjectNotFoundError: If S3 reports that the object does not exist.
            S3OperationError: If the download request fails.
        """
        self._validate_object_key(object_key)

        try:
            response = self._s3_client.get_object(
                Bucket=self.settings.s3_bucket_name,
                Key=object_key,
            )
        except (BotoCoreError, ClientError) as exc:
            error_code = self._get_error_code(exc)

            if error_code in {"404", "NoSuchKey", "NotFound"}:
                raise S3ObjectNotFoundError(
                    "The requested S3 object does not exist.",
                    operation="get_object",
                    object_key=object_key,
                    error_code=error_code,
                ) from exc

            raise self._build_operation_error(
                exc,
                operation="get_object",
                object_key=object_key,
                message="Unable to download the S3 object.",
            ) from exc

        self.logger.info(
            "s3_object_download_requested",
            object_key=object_key,
            bucket=self.settings.s3_bucket_name,
            size_bytes=response.get("ContentLength"),
        )

        return response

    def delete_object(self, object_key: str) -> dict[str, Any]:
        """Delete an object from the configured S3 bucket.

        S3 DeleteObject is idempotent for an unversioned bucket. When bucket
        versioning is enabled, this operation normally creates a delete marker
        instead of permanently deleting existing object versions.

        Args:
            object_key: S3 object key to delete.

        Returns:
            A normalized result containing deletion status and version
            information when returned by S3.

        Raises:
            ValueError: If the object key is invalid.
            S3OperationError: If the deletion request fails.

        Notes:
            A successful DeleteObject response does not prove that all
            historical versions have been permanently removed.
        """
        self._validate_object_key(object_key)

        try:
            response = self._s3_client.delete_object(
                Bucket=self.settings.s3_bucket_name,
                Key=object_key,
            )
        except (BotoCoreError, ClientError) as exc:
            raise self._build_operation_error(
                exc,
                operation="delete_object",
                object_key=object_key,
                message="Unable to delete the S3 object.",
            ) from exc

        self.logger.info(
            "s3_object_deleted",
            object_key=object_key,
            bucket=self.settings.s3_bucket_name,
            version_id=response.get("VersionId"),
            delete_marker=response.get("DeleteMarker", False),
        )

        return {
            "object_key": object_key,
            "deleted": True,
            "version_id": response.get("VersionId"),
            "delete_marker": response.get("DeleteMarker", False),
        }

    def _build_operation_error(
        self,
        exc: BotoCoreError | ClientError,
        *,
        operation: str,
        object_key: str,
        message: str,
    ) -> S3OperationError:
        """Create a consistent application exception from an AWS SDK error."""
        error_code = self._get_error_code(exc)

        self.logger.exception(
            "s3_object_operation_failed",
            operation=operation,
            object_key=object_key,
            bucket=self.settings.s3_bucket_name,
            error_code=error_code,
        )

        return S3OperationError(
            message,
            operation=operation,
            object_key=object_key,
            error_code=error_code,
        )

    @staticmethod
    def _get_error_code(exc: BotoCoreError | ClientError) -> str | None:
        """Extract the AWS error code without exposing response details."""
        if isinstance(exc, ClientError):
            error = exc.response.get("Error", {})
            code = error.get("Code")

            return str(code) if code is not None else None

        return type(exc).__name__

    @staticmethod
    def _validate_object_key(object_key: str) -> None:
        """Reject empty or unsafe S3 object keys."""
        if not isinstance(object_key, str) or not object_key.strip():
            raise ValueError("A valid S3 object key is required.")

        if object_key.startswith("/"):
            raise ValueError("S3 object keys must not start with a slash.")

        if "\\" in object_key:
            raise ValueError("S3 object keys must not contain backslashes.")

        if any(
            ord(character) < 32 or ord(character) == 127
            for character in object_key
        ):
            raise ValueError("S3 object keys must not contain control characters.")

        if len(object_key.encode("utf-8")) > 1024:
            raise ValueError("S3 object keys must not exceed 1024 UTF-8 bytes.")

    @staticmethod
    def _validate_content_type(content_type: str) -> str:
        """Normalize and validate a MIME content type."""
        if not isinstance(content_type, str) or not content_type.strip():
            raise ValueError("A valid content type is required.")

        normalized = content_type.partition(";")[0].strip().lower()

        if not normalized or "/" not in normalized:
            raise ValueError("A valid MIME content type is required.")

        return normalized

    @staticmethod
    def _normalize_metadata(
        metadata: Mapping[str, str] | None,
    ) -> dict[str, str]:
        """Normalize custom S3 metadata and reject invalid header values."""
        if metadata is None:
            return {}

        if not isinstance(metadata, Mapping):
            raise ValueError("S3 metadata must be a mapping of strings.")

        normalized: dict[str, str] = {}

        for key, value in metadata.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError("S3 metadata keys and values must be strings.")

            normalized_key = key.strip().lower()

            if normalized_key.startswith("x-amz-meta-"):
                normalized_key = normalized_key.removeprefix("x-amz-meta-")

            if not normalized_key:
                raise ValueError("S3 metadata keys must not be empty.")

            if any(
                character in normalized_key
                for character in ("\r", "\n", ":", "/", "\\")
            ):
                raise ValueError("S3 metadata keys contain unsupported characters.")

            if any(
                ord(character) < 32 or ord(character) == 127
                for character in value
            ):
                raise ValueError(
                    "S3 metadata values must not contain control characters."
                )

            normalized[normalized_key] = value

        return normalized