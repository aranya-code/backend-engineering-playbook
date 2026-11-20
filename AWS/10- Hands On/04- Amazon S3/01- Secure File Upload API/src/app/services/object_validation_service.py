"""Validation service for uploaded S3 objects.

This module centralizes application-level validation for upload metadata.
It validates filenames, content types, and declared file sizes before an
object is uploaded directly or through a presigned S3 request.

Content-type validation checks the client-declared MIME type against the
configured allowlist. It does not inspect file contents or establish that
the uploaded bytes match the declared type.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import PurePath

from app.config import Settings


_INVALID_FILENAME_CHARACTERS = re.compile(r"[^A-Za-z0-9._-]+")
_MAX_FILENAME_LENGTH = 255


class ObjectValidationError(ValueError):
    """Raised when uploaded object metadata violates application rules."""


@dataclass(frozen=True, slots=True)
class ValidatedUpload:
    """Normalized upload metadata accepted by the validation service."""

    filename: str
    content_type: str
    size_bytes: int


class ObjectValidationService:
    """Validate and normalize metadata for objects stored in Amazon S3.

    The service applies application-level restrictions configured through
    ``Settings``. It does not perform S3 operations, inspect file contents,
    or replace authorization checks.

    Args:
        settings: Validated application settings containing upload limits
            and the allowed MIME type configuration.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

        self._allowed_content_types = frozenset(
            content_type.strip().lower()
            for content_type in settings.allowed_content_types
        )

    def validate_upload(
        self,
        filename: str,
        content_type: str,
        size_bytes: int | None,
    ) -> ValidatedUpload:
        """Validate upload metadata and return its normalized representation.

        Args:
            filename: Original client-provided filename.
            content_type: Client-declared MIME content type.
            size_bytes: Known upload size in bytes.

        Returns:
            ValidatedUpload containing a sanitized filename, normalized
            content type, and validated file size.

        Raises:
            ObjectValidationError: If any upload attribute is invalid.
        """
        sanitized_filename = self.sanitize_filename(filename)
        normalized_content_type = self.normalize_content_type(content_type)
        self.validate_content_type(normalized_content_type)
        self.validate_size(size_bytes)

        if size_bytes is None:
            raise ObjectValidationError(
                "The upload size must be known before accepting the file."
            )

        return ValidatedUpload(
            filename=sanitized_filename,
            content_type=normalized_content_type,
            size_bytes=size_bytes,
        )

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Normalize a client-provided filename for safe metadata storage.

        Path components are discarded, Unicode compatibility normalization
        is applied, and unsupported characters are replaced with underscores.

        The sanitized filename is metadata only. It must not be used as the
        S3 object key or as an authorization boundary.
        """
        if not isinstance(filename, str) or not filename.strip():
            raise ObjectValidationError("A valid filename is required.")

        normalized = unicodedata.normalize("NFKC", filename.strip())
        normalized = normalized.replace("\\", "/")
        normalized = PurePath(normalized).name

        normalized = "".join(
            character
            for character in normalized
            if unicodedata.category(character)[0] != "C"
        )

        sanitized = _INVALID_FILENAME_CHARACTERS.sub("_", normalized)
        sanitized = sanitized.strip("._-")

        if not sanitized:
            raise ObjectValidationError(
                "The filename does not contain any usable characters."
            )

        if len(sanitized) > _MAX_FILENAME_LENGTH:
            raise ObjectValidationError(
                f"The filename must not exceed {_MAX_FILENAME_LENGTH} characters."
            )

        return sanitized

    @staticmethod
    def normalize_content_type(content_type: str) -> str:
        """Normalize a declared MIME type by removing optional parameters."""
        if not isinstance(content_type, str) or not content_type.strip():
            raise ObjectValidationError("A content type is required.")

        normalized = content_type.partition(";")[0].strip().lower()

        if not normalized or "/" not in normalized:
            raise ObjectValidationError("A valid MIME content type is required.")

        return normalized

    def validate_content_type(self, content_type: str) -> None:
        """Ensure the normalized MIME type is present in the configured allowlist."""
        if content_type not in self._allowed_content_types:
            raise ObjectValidationError(
                f"Content type '{content_type}' is not allowed."
            )

    def validate_size(self, size_bytes: int | None) -> None:
        """Enforce the configured maximum upload size."""
        if size_bytes is None:
            raise ObjectValidationError(
                "The upload size must be known before accepting the file."
            )

        if isinstance(size_bytes, bool) or not isinstance(size_bytes, int):
            raise ObjectValidationError("The upload size must be an integer.")

        if size_bytes <= 0:
            raise ObjectValidationError("The uploaded file must not be empty.")

        if size_bytes > self.settings.max_upload_size_bytes:
            raise ObjectValidationError(
                "The uploaded file exceeds the maximum allowed size of "
                f"{self.settings.max_upload_size_bytes} bytes."
            )