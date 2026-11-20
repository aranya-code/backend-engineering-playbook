"""Unit tests for upload metadata validation and normalization."""

from __future__ import annotations

import pytest

from app.config import Settings
from app.services.object_validation_service import (
    ObjectValidationError,
    ObjectValidationService,
    ValidatedUpload,
)


pytestmark = pytest.mark.unit


@pytest.fixture
def settings() -> Settings:
    """Provide isolated settings for upload validation tests."""
    return Settings(
        _env_file=None,
        S3_BUCKET_NAME="unit-test-uploads",
        MAX_UPLOAD_SIZE_BYTES=1024,
        ALLOWED_CONTENT_TYPES=(
            "text/plain",
            "application/pdf",
            "application/json",
            "image/png",
        ),
    )


@pytest.fixture
def validation_service(settings: Settings) -> ObjectValidationService:
    """Create the validation service with deterministic test settings."""
    return ObjectValidationService(settings)


class TestSanitizeFilename:
    """Tests for filename normalization and sanitization."""

    @pytest.mark.parametrize(
        ("filename", "expected"),
        [
            ("report.pdf", "report.pdf"),
            ("  report.pdf  ", "report.pdf"),
            ("my document.pdf", "my_document.pdf"),
            ("report@2026!.pdf", "report_2026_.pdf"),
            ("folder/report.pdf", "report.pdf"),
            (r"folder\report.pdf", "report.pdf"),
            ("../../report.pdf", "report.pdf"),
            ("résumé.pdf", "r_sum_.pdf"),
            ("Ｒｅｐｏｒｔ.pdf", "Report.pdf"),
            ("report\nfile.pdf", "reportfile.pdf"),
            ("report---.pdf", "report.pdf"),
        ],
    )
    def test_sanitizes_filename(
        self,
        validation_service: ObjectValidationService,
        filename: str,
        expected: str,
    ) -> None:
        """Normalize paths, Unicode, whitespace, and unsupported characters."""
        assert validation_service.sanitize_filename(filename) == expected

    @pytest.mark.parametrize(
        "filename",
        [
            "",
            "   ",
            ".",
            "...",
            "---",
            "___",
            "../",
            r"..\ ",
        ],
    )
    def test_rejects_filename_without_usable_characters(
        self,
        validation_service: ObjectValidationService,
        filename: str,
    ) -> None:
        """Reject empty filenames and names that sanitize to an empty value."""
        with pytest.raises(ObjectValidationError):
            validation_service.sanitize_filename(filename)

    @pytest.mark.parametrize(
        "filename",
        [
            None,
            123,
            b"report.pdf",
        ],
    )
    def test_rejects_non_string_filename(
        self,
        validation_service: ObjectValidationService,
        filename: object,
    ) -> None:
        """Reject values that are not strings."""
        with pytest.raises(ObjectValidationError):
            validation_service.sanitize_filename(filename)  # type: ignore[arg-type]

    def test_rejects_filename_exceeding_maximum_length(
        self,
        validation_service: ObjectValidationService,
    ) -> None:
        """Enforce the 255-character sanitized filename limit."""
        filename = f"{'a' * 252}.pdf"

        with pytest.raises(
            ObjectValidationError,
            match="must not exceed 255 characters",
        ):
            validation_service.sanitize_filename(filename)

    def test_accepts_filename_at_maximum_length(
        self,
        validation_service: ObjectValidationService,
    ) -> None:
        """Accept a sanitized filename containing exactly 255 characters."""
        filename = f"{'a' * 251}.pdf"

        assert len(filename) == 255
        assert validation_service.sanitize_filename(filename) == filename


class TestNormalizeContentType:
    """Tests for MIME content-type normalization."""

    @pytest.mark.parametrize(
        ("content_type", "expected"),
        [
            ("text/plain", "text/plain"),
            ("TEXT/PLAIN", "text/plain"),
            (" application/pdf ", "application/pdf"),
            ("application/json; charset=utf-8", "application/json"),
            ("IMAGE/PNG; boundary=something", "image/png"),
        ],
    )
    def test_normalizes_content_type(
        self,
        validation_service: ObjectValidationService,
        content_type: str,
        expected: str,
    ) -> None:
        """Normalize MIME types and remove optional parameters."""
        assert (
            validation_service.normalize_content_type(content_type)
            == expected
        )

    @pytest.mark.parametrize(
        "content_type",
        [
            "",
            "   ",
            "plain",
            "application",
            "/plain",
            "text/",
            "; charset=utf-8",
        ],
    )
    def test_rejects_invalid_content_type(
        self,
        validation_service: ObjectValidationService,
        content_type: str,
    ) -> None:
        """Reject missing or malformed MIME content types."""
        with pytest.raises(ObjectValidationError):
            validation_service.normalize_content_type(content_type)

    @pytest.mark.parametrize(
        "content_type",
        [
            None,
            123,
            b"text/plain",
        ],
    )
    def test_rejects_non_string_content_type(
        self,
        validation_service: ObjectValidationService,
        content_type: object,
    ) -> None:
        """Reject values that are not strings."""
        with pytest.raises(ObjectValidationError):
            validation_service.normalize_content_type(
                content_type  # type: ignore[arg-type]
            )


class TestValidateContentType:
    """Tests for the configured MIME type allowlist."""

    @pytest.mark.parametrize(
        "content_type",
        [
            "text/plain",
            "application/pdf",
            "application/json",
            "image/png",
        ],
    )
    def test_accepts_allowed_content_type(
        self,
        validation_service: ObjectValidationService,
        content_type: str,
    ) -> None:
        """Accept MIME types configured in the allowlist."""
        validation_service.validate_content_type(content_type)

    def test_normalizes_allowlist_entries_during_initialization(self) -> None:
        """Normalize configured MIME types before allowlist comparisons."""
        settings = Settings(
            _env_file=None,
            S3_BUCKET_NAME="unit-test-uploads",
            ALLOWED_CONTENT_TYPES=(" TEXT/PLAIN ", "APPLICATION/PDF"),
        )
        service = ObjectValidationService(settings)

        service.validate_content_type("text/plain")
        service.validate_content_type("application/pdf")

    @pytest.mark.parametrize(
        "content_type",
        [
            "application/x-executable",
            "image/gif",
            "text/html",
            "application/octet-stream",
        ],
    )
    def test_rejects_content_type_not_in_allowlist(
        self,
        validation_service: ObjectValidationService,
        content_type: str,
    ) -> None:
        """Reject syntactically valid MIME types that are not allowed."""
        with pytest.raises(
            ObjectValidationError,
            match="is not allowed",
        ):
            validation_service.validate_content_type(content_type)


class TestValidateSize:
    """Tests for upload size validation."""

    def test_accepts_size_within_configured_limit(
        self,
        validation_service: ObjectValidationService,
    ) -> None:
        """Accept a positive file size below the configured maximum."""
        validation_service.validate_size(512)

    def test_accepts_size_equal_to_configured_limit(
        self,
        validation_service: ObjectValidationService,
    ) -> None:
        """Accept a file whose size exactly matches the configured maximum."""
        validation_service.validate_size(1024)

    def test_rejects_size_exceeding_configured_limit(
        self,
        validation_service: ObjectValidationService,
    ) -> None:
        """Reject files larger than the configured maximum."""
        with pytest.raises(
            ObjectValidationError,
            match="exceeds the maximum allowed size",
        ):
            validation_service.validate_size(1025)

    def test_rejects_missing_size(
        self,
        validation_service: ObjectValidationService,
    ) -> None:
        """Require a known upload size before accepting the file."""
        with pytest.raises(
            ObjectValidationError,
            match="must be known",
        ):
            validation_service.validate_size(None)

    @pytest.mark.parametrize("size_bytes", [0, -1, -1024])
    def test_rejects_non_positive_size(
        self,
        validation_service: ObjectValidationService,
        size_bytes: int,
    ) -> None:
        """Reject empty files and negative sizes."""
        with pytest.raises(
            ObjectValidationError,
            match="must not be empty",
        ):
            validation_service.validate_size(size_bytes)

    @pytest.mark.parametrize(
        "size_bytes",
        [
            True,
            False,
            1.5,
            "512",
            b"512",
        ],
    )
    def test_rejects_non_integer_size(
        self,
        validation_service: ObjectValidationService,
        size_bytes: object,
    ) -> None:
        """Reject booleans and values that are not integers."""
        with pytest.raises(
            ObjectValidationError,
            match="must be an integer",
        ):
            validation_service.validate_size(
                size_bytes  # type: ignore[arg-type]
            )


class TestValidateUpload:
    """Tests for the complete upload metadata validation workflow."""

    def test_returns_validated_upload(
        self,
        validation_service: ObjectValidationService,
    ) -> None:
        """Return normalized metadata when every validation succeeds."""
        result = validation_service.validate_upload(
            filename="  quarterly report.pdf  ",
            content_type="APPLICATION/PDF; charset=binary",
            size_bytes=512,
        )

        assert result == ValidatedUpload(
            filename="quarterly_report.pdf",
            content_type="application/pdf",
            size_bytes=512,
        )

    def test_returns_immutable_validated_upload(
        self,
        validation_service: ObjectValidationService,
    ) -> None:
        """Ensure validated metadata cannot be modified after construction."""
        result = validation_service.validate_upload(
            filename="report.pdf",
            content_type="application/pdf",
            size_bytes=512,
        )

        with pytest.raises(AttributeError):
            result.filename = "modified.pdf"  # type: ignore[misc]

    def test_rejects_invalid_filename(
        self,
        validation_service: ObjectValidationService,
    ) -> None:
        """Reject invalid filenames before returning validated metadata."""
        with pytest.raises(ObjectValidationError):
            validation_service.validate_upload(
                filename="   ",
                content_type="text/plain",
                size_bytes=100,
            )

    def test_rejects_unsupported_content_type(
        self,
        validation_service: ObjectValidationService,
    ) -> None:
        """Reject uploads whose normalized MIME type is not allowed."""
        with pytest.raises(
            ObjectValidationError,
            match="is not allowed",
        ):
            validation_service.validate_upload(
                filename="payload.exe",
                content_type="application/x-executable",
                size_bytes=100,
            )

    def test_rejects_missing_size(
        self,
        validation_service: ObjectValidationService,
    ) -> None:
        """Reject upload metadata when the file size is unknown."""
        with pytest.raises(
            ObjectValidationError,
            match="must be known",
        ):
            validation_service.validate_upload(
                filename="report.pdf",
                content_type="application/pdf",
                size_bytes=None,
            )

    def test_rejects_oversized_upload(
        self,
        validation_service: ObjectValidationService,
    ) -> None:
        """Apply the configured maximum size during complete validation."""
        with pytest.raises(
            ObjectValidationError,
            match="exceeds the maximum allowed size",
        ):
            validation_service.validate_upload(
                filename="large-report.pdf",
                content_type="application/pdf",
                size_bytes=1025,
            )