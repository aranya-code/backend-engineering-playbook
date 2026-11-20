"""Generate secure presigned URLs for Amazon S3 object operations.

This service creates time-limited URLs for direct client-to-S3 uploads and
downloads. It uses the configured bucket and AWS Region, and relies on Boto3's
standard credential provider chain rather than accepting credentials from
application configuration.

Presigned URLs are bearer credentials. Anyone possessing a valid URL can
perform the signed operation until the URL expires or the underlying
authorization becomes invalid.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import boto3
import structlog
from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.config import Settings


class PresignedUrlGenerationError(RuntimeError):
    """Raised when an S3 presigned URL cannot be generated."""


class PresignedUrlService:
    """Generate presigned S3 upload and download URLs.

    The service signs requests for the configured S3 bucket. Upload URLs use
    the S3 PutObject operation and bind the declared content type and metadata
    to the signature. When a KMS key is configured, the upload request also
    includes explicit SSE-KMS parameters.

    Args:
        settings: Application settings containing the bucket, Region,
            encryption key, and maximum presigned URL lifetime.
        s3_client: Optional Boto3 S3 client. Supplying a client supports
            dependency injection and isolated tests.
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

    def generate_upload_url(
        self,
        object_key: str,
        content_type: str,
        metadata: Mapping[str, str] | None = None,
        expires_in: int | None = None,
    ) -> tuple[str, dict[str, str]]:
        """Generate a presigned URL for a direct S3 PutObject request.

        The returned headers describe the headers the client must send with
        its PUT request. The content type, metadata, and encryption parameters
        are included in the signed request.

        Args:
            object_key: Server-generated S3 object key.
            content_type: Validated MIME content type.
            metadata: Optional custom S3 object metadata.
            expires_in: URL lifetime in seconds. Defaults to the configured
                application value.

        Returns:
            A tuple containing the presigned URL and required HTTP headers.

        Raises:
            ValueError: If the object key, content type, metadata, or
                expiration value is invalid.
            PresignedUrlGenerationError: If Boto3 cannot generate the URL.

        Important:
            A presigned PUT URL does not independently enforce the
            application's declared maximum upload size. The API must not
            treat the declared size as proof of the uploaded object's size.
            Verify the resulting object with HeadObject or an upload
            completion workflow before marking an upload as complete.
        """
        self._validate_object_key(object_key)
        normalized_content_type = self._validate_content_type(content_type)
        normalized_metadata = self._normalize_metadata(metadata)
        expiration = self._resolve_expiration(expires_in)

        params: dict[str, Any] = {
            "Bucket": self.settings.s3_bucket_name,
            "Key": object_key,
            "ContentType": normalized_content_type,
        }

        required_headers = {
            "Content-Type": normalized_content_type,
        }

        if normalized_metadata:
            params["Metadata"] = normalized_metadata
            required_headers.update(
                {
                    f"x-amz-meta-{key}": value
                    for key, value in normalized_metadata.items()
                }
            )

        kms_key_id = self.settings.s3_kms_key_id

        if kms_key_id:
            params["ServerSideEncryption"] = "aws:kms"
            params["SSEKMSKeyId"] = kms_key_id

            required_headers["x-amz-server-side-encryption"] = "aws:kms"
            required_headers["x-amz-server-side-encryption-aws-kms-key-id"] = (
                kms_key_id
            )

        try:
            upload_url = self._s3_client.generate_presigned_url(
                ClientMethod="put_object",
                Params=params,
                ExpiresIn=expiration,
                HttpMethod="PUT",
            )
        except (BotoCoreError, ClientError) as exc:
            self.logger.exception(
                "s3_presigned_upload_url_generation_failed",
                object_key=object_key,
                bucket=self.settings.s3_bucket_name,
            )
            raise PresignedUrlGenerationError(
                "Unable to generate an S3 upload URL."
            ) from exc

        self.logger.info(
            "s3_presigned_upload_url_generated",
            object_key=object_key,
            bucket=self.settings.s3_bucket_name,
            expires_in=expiration,
        )

        return upload_url, required_headers

    def generate_download_url(
        self,
        object_key: str,
        expires_in: int | None = None,
    ) -> str:
        """Generate a presigned URL for downloading an existing S3 object.

        The URL authorizes a GetObject request using the application's AWS
        identity. The caller must still enforce application-level ownership
        and authorization before returning the URL.

        Args:
            object_key: S3 object key to download.
            expires_in: URL lifetime in seconds. Defaults to the configured
                application value.

        Returns:
            A presigned URL for an S3 GetObject request.

        Raises:
            ValueError: If the object key or expiration value is invalid.
            PresignedUrlGenerationError: If Boto3 cannot generate the URL.
        """
        self._validate_object_key(object_key)
        expiration = self._resolve_expiration(expires_in)

        try:
            download_url = self._s3_client.generate_presigned_url(
                ClientMethod="get_object",
                Params={
                    "Bucket": self.settings.s3_bucket_name,
                    "Key": object_key,
                },
                ExpiresIn=expiration,
                HttpMethod="GET",
            )
        except (BotoCoreError, ClientError) as exc:
            self.logger.exception(
                "s3_presigned_download_url_generation_failed",
                object_key=object_key,
                bucket=self.settings.s3_bucket_name,
            )
            raise PresignedUrlGenerationError(
                "Unable to generate an S3 download URL."
            ) from exc

        self.logger.info(
            "s3_presigned_download_url_generated",
            object_key=object_key,
            bucket=self.settings.s3_bucket_name,
            expires_in=expiration,
        )

        return download_url

    def _resolve_expiration(self, expires_in: int | None) -> int:
        """Resolve and validate the requested URL lifetime."""
        expiration = (
            self.settings.presigned_url_expiration_seconds
            if expires_in is None
            else expires_in
        )

        if isinstance(expiration, bool) or not isinstance(expiration, int):
            raise ValueError("Presigned URL expiration must be an integer.")

        if expiration < 1:
            raise ValueError("Presigned URL expiration must be at least one second.")

        if expiration > self.settings.presigned_url_expiration_seconds:
            raise ValueError(
                "Requested expiration exceeds the configured application limit "
                f"of {self.settings.presigned_url_expiration_seconds} seconds."
            )

        if expiration > 3600:
            raise ValueError(
                "Presigned URL expiration must not exceed 3600 seconds."
            )

        return expiration

    @staticmethod
    def _validate_object_key(object_key: str) -> None:
        """Reject empty or unsafe object keys."""
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

            if not normalized_key:
                raise ValueError("S3 metadata keys must not be empty.")

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