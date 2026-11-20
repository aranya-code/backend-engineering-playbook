"""Document validation for the S3 ingestion pipeline.

Validates document names, declared content types, file sizes, and file
signatures before metadata extraction or downstream processing.

Validation is intentionally independent of AWS clients so it can be used
by API handlers, Lambda functions, and unit tests.
"""

from __future__ import annotations

import logging
import mimetypes
import os
from pathlib import PurePosixPath
from typing import Final

logger = logging.getLogger(__name__)

DEFAULT_MAX_DOCUMENT_SIZE_BYTES: Final[int] = 50 * 1024 * 1024

ALLOWED_CONTENT_TYPES: Final[frozenset[str]] = frozenset(
    {
        "application/pdf",
        "application/msword",
        (
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/plain",
        "text/csv",
    }
)

ALLOWED_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {
        ".pdf",
        ".doc",
        ".docx",
        ".xlsx",
        ".txt",
        ".csv",
    }
)

# Signatures are used as an additional content check, not as a replacement
# for parsing the document with a format-specific library.
FILE_SIGNATURES: Final[dict[str, tuple[bytes, ...]]] = {
    "application/pdf": (b"%PDF-",),
    "application/msword": (
        b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",
    ),
    (
        "application/vnd.openxmlformats-officedocument."
        "wordprocessingml.document"
    ): (
        b"PK\x03\x04",
    ),
    (
        "application/vnd.openxmlformats-officedocument."
        "spreadsheetml.sheet"
    ): (
        b"PK\x03\x04",
    ),
}

MAX_FILENAME_LENGTH: Final[int] = 255


class DocumentValidationError(ValueError):
    """Raised when an uploaded document violates ingestion requirements."""


class DocumentValidator:
    """Validate document properties before ingestion.

    The validator checks:
    - Filename presence, length, and path safety.
    - Allowed file extensions.
    - Allowed declared MIME types.
    - Filename-to-content-type consistency.
    - File size limits.
    - File signatures when a supported signature is defined.

    Signature validation is performed separately through
    ``validate_file_signature`` because the ingestion handler may validate
    object metadata before downloading the object body.
    """

    def __init__(
        self,
        *,
        max_size_bytes: int | None = None,
        allowed_content_types: frozenset[str] | None = None,
        allowed_extensions: frozenset[str] | None = None,
    ) -> None:
        configured_max_size = os.getenv("MAX_DOCUMENT_SIZE_BYTES")

        if max_size_bytes is None and configured_max_size:
            try:
                max_size_bytes = int(configured_max_size)
            except ValueError as exc:
                raise ValueError(
                    "MAX_DOCUMENT_SIZE_BYTES must be a positive integer."
                ) from exc

        self.max_size_bytes = (
            max_size_bytes
            if max_size_bytes is not None
            else DEFAULT_MAX_DOCUMENT_SIZE_BYTES
        )

        if self.max_size_bytes <= 0:
            raise ValueError("max_size_bytes must be greater than zero.")

        self.allowed_content_types = (
            allowed_content_types
            if allowed_content_types is not None
            else ALLOWED_CONTENT_TYPES
        )

        self.allowed_extensions = (
            allowed_extensions
            if allowed_extensions is not None
            else ALLOWED_EXTENSIONS
        )

        if not self.allowed_content_types:
            raise ValueError("At least one content type must be allowed.")

        if not self.allowed_extensions:
            raise ValueError("At least one file extension must be allowed.")

    @staticmethod
    def _validate_filename(filename: str) -> str:
        """Validate a filename and return its normalized representation."""
        if not isinstance(filename, str) or not filename:
            raise DocumentValidationError(
                "Document filename must be a non-empty string."
            )

        if len(filename) > MAX_FILENAME_LENGTH:
            raise DocumentValidationError(
                f"Document filename exceeds {MAX_FILENAME_LENGTH} characters."
            )

        if filename in {".", ".."}:
            raise DocumentValidationError("Invalid document filename.")

        if filename != filename.strip():
            raise DocumentValidationError(
                "Document filename cannot start or end with whitespace."
            )

        if any(
            ord(character) < 32 or ord(character) == 127
            for character in filename
        ):
            raise DocumentValidationError(
                "Document filename contains control characters."
            )

        if "/" in filename or "\\" in filename:
            raise DocumentValidationError(
                "Document filename must not contain path separators."
            )

        path = PurePosixPath(filename)

        if path.name != filename:
            raise DocumentValidationError(
                "Document filename must not contain path components."
            )

        return filename

    def _validate_extension(self, filename: str) -> str:
        """Validate and return the lowercase filename extension."""
        extension = PurePosixPath(filename).suffix.lower()

        if not extension:
            raise DocumentValidationError(
                "Document filename must have a file extension."
            )

        if extension not in self.allowed_extensions:
            raise DocumentValidationError(
                f"Unsupported document extension: {extension!r}."
            )

        return extension

    def _validate_content_type(self, content_type: str) -> str:
        """Validate and normalize a declared MIME content type."""
        if not isinstance(content_type, str) or not content_type.strip():
            raise DocumentValidationError(
                "Document content type must be a non-empty string."
            )

        normalized_content_type = (
            content_type.split(";", maxsplit=1)[0].strip().lower()
        )

        if normalized_content_type not in self.allowed_content_types:
            raise DocumentValidationError(
                f"Unsupported document content type: "
                f"{normalized_content_type!r}."
            )

        return normalized_content_type

    @staticmethod
    def _validate_size(size_bytes: int, max_size_bytes: int) -> None:
        """Validate the document size."""
        if isinstance(size_bytes, bool) or not isinstance(size_bytes, int):
            raise DocumentValidationError(
                "Document size must be an integer."
            )

        if size_bytes < 0:
            raise DocumentValidationError(
                "Document size cannot be negative."
            )

        if size_bytes == 0:
            raise DocumentValidationError(
                "Empty documents are not allowed."
            )

        if size_bytes > max_size_bytes:
            raise DocumentValidationError(
                f"Document exceeds the maximum allowed size of "
                f"{max_size_bytes} bytes."
            )

    @staticmethod
    def _validate_extension_content_type(
        extension: str,
        content_type: str,
    ) -> None:
        """Check whether the filename extension matches the declared type."""
        detected_content_type, _ = mimetypes.guess_type(
            f"document{extension}",
            strict=False,
        )

        if (
            detected_content_type is not None
            and detected_content_type != content_type
        ):
            raise DocumentValidationError(
                f"File extension {extension!r} does not match declared "
                f"content type {content_type!r}."
            )

    def validate_document(
        self,
        *,
        filename: str,
        content_type: str,
        size_bytes: int,
    ) -> dict[str, str | int]:
        """Validate document metadata before downloading or processing it.

        Args:
            filename: Original filename without an S3 prefix.
            content_type: Content-Type returned by S3 or supplied by the
                upload client.
            size_bytes: Authoritative object size obtained from S3.

        Returns:
            Normalized document properties.

        Raises:
            DocumentValidationError: If any document property is invalid.
        """
        normalized_filename = self._validate_filename(filename)
        extension = self._validate_extension(normalized_filename)
        normalized_content_type = self._validate_content_type(content_type)

        self._validate_size(
            size_bytes=size_bytes,
            max_size_bytes=self.max_size_bytes,
        )

        self._validate_extension_content_type(
            extension=extension,
            content_type=normalized_content_type,
        )

        result: dict[str, str | int] = {
            "filename": normalized_filename,
            "extension": extension,
            "content_type": normalized_content_type,
            "size_bytes": size_bytes,
        }

        logger.info(
            "Document metadata validation succeeded.",
            extra={
                "filename": normalized_filename,
                "content_type": normalized_content_type,
                "size_bytes": size_bytes,
            },
        )

        return result

    def validate_file_signature(
        self,
        *,
        filename: str,
        content_type: str,
        file_header: bytes,
    ) -> None:
        """Validate the file signature against its declared content type.

        The caller must supply bytes read from the beginning of the actual
        document. For formats without a configured signature, this method
        does not claim that the document is structurally valid.

        Args:
            filename: Original filename.
            content_type: Declared MIME content type.
            file_header: Initial bytes from the document.

        Raises:
            DocumentValidationError: If the signature is inconsistent or
                the supplied header is invalid.
        """
        normalized_filename = self._validate_filename(filename)
        extension = self._validate_extension(normalized_filename)
        normalized_content_type = self._validate_content_type(content_type)

        if not isinstance(file_header, bytes):
            raise DocumentValidationError(
                "File header must be supplied as bytes."
            )

        if not file_header:
            raise DocumentValidationError(
                "Document content cannot be empty."
            )

        self._validate_extension_content_type(
            extension=extension,
            content_type=normalized_content_type,
        )

        expected_signatures = FILE_SIGNATURES.get(
            normalized_content_type
        )

        if expected_signatures is None:
            return

        if not any(
            file_header.startswith(signature)
            for signature in expected_signatures
        ):
            raise DocumentValidationError(
                f"Document content does not match declared content type "
                f"{normalized_content_type!r}."
            )

        logger.info(
            "Document file signature validation succeeded.",
            extra={
                "filename": normalized_filename,
                "content_type": normalized_content_type,
            },
        )