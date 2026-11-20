"""Unit tests for document validation in the S3 ingestion pipeline."""

from __future__ import annotations

import pytest

from ingestion.document_validator import (
    DEFAULT_MAX_DOCUMENT_SIZE_BYTES,
    DocumentValidationError,
    DocumentValidator,
)


PDF_CONTENT_TYPE = "application/pdf"
TEXT_CONTENT_TYPE = "text/plain"
CSV_CONTENT_TYPE = "text/csv"
DOC_CONTENT_TYPE = "application/msword"

PDF_HEADER = b"%PDF-1.7"
DOC_HEADER = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
ZIP_HEADER = b"PK\x03\x04"

VALID_PDF_FILENAME = "report.pdf"
VALID_TEXT_FILENAME = "notes.txt"
VALID_CSV_FILENAME = "records.csv"

DEFAULT_VALIDATOR = DocumentValidator()


class TestDocumentValidatorInitialization:
    """Tests for validator configuration and initialization."""

    def test_uses_default_maximum_document_size(self) -> None:
        validator = DocumentValidator()

        assert (
            validator.max_size_bytes
            == DEFAULT_MAX_DOCUMENT_SIZE_BYTES
        )

    def test_accepts_custom_maximum_document_size(self) -> None:
        validator = DocumentValidator(max_size_bytes=1024)

        assert validator.max_size_bytes == 1024

    def test_reads_maximum_size_from_environment(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("MAX_DOCUMENT_SIZE_BYTES", "2048")

        validator = DocumentValidator()

        assert validator.max_size_bytes == 2048

    def test_explicit_maximum_size_overrides_environment(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("MAX_DOCUMENT_SIZE_BYTES", "2048")

        validator = DocumentValidator(max_size_bytes=4096)

        assert validator.max_size_bytes == 4096

    def test_rejects_non_integer_environment_size(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("MAX_DOCUMENT_SIZE_BYTES", "invalid")

        with pytest.raises(
            ValueError,
            match="MAX_DOCUMENT_SIZE_BYTES must be a positive integer",
        ):
            DocumentValidator()

    @pytest.mark.parametrize("max_size_bytes", [0, -1])
    def test_rejects_non_positive_maximum_size(
        self,
        max_size_bytes: int,
    ) -> None:
        with pytest.raises(
            ValueError,
            match="max_size_bytes must be greater than zero",
        ):
            DocumentValidator(max_size_bytes=max_size_bytes)

    def test_rejects_empty_allowed_content_types(self) -> None:
        with pytest.raises(
            ValueError,
            match="At least one content type must be allowed",
        ):
            DocumentValidator(allowed_content_types=frozenset())

    def test_rejects_empty_allowed_extensions(self) -> None:
        with pytest.raises(
            ValueError,
            match="At least one file extension must be allowed",
        ):
            DocumentValidator(allowed_extensions=frozenset())

    def test_accepts_custom_allowlists(self) -> None:
        validator = DocumentValidator(
            max_size_bytes=4096,
            allowed_content_types=frozenset({PDF_CONTENT_TYPE}),
            allowed_extensions=frozenset({".pdf"}),
        )

        assert validator.max_size_bytes == 4096
        assert validator.allowed_content_types == frozenset(
            {PDF_CONTENT_TYPE}
        )
        assert validator.allowed_extensions == frozenset({".pdf"})


class TestFilenameValidation:
    """Tests for filename presence, length, and path safety."""

    @pytest.mark.parametrize(
        ("filename", "content_type"),
        [
            (VALID_PDF_FILENAME, PDF_CONTENT_TYPE),
            (VALID_TEXT_FILENAME, TEXT_CONTENT_TYPE),
            (VALID_CSV_FILENAME, CSV_CONTENT_TYPE),
        ],
    )
    def test_accepts_supported_filenames(
        self,
        filename: str,
        content_type: str,
    ) -> None:
        result = DEFAULT_VALIDATOR.validate_document(
            filename=filename,
            content_type=content_type,
            size_bytes=1024,
        )

        assert result["filename"] == filename

    @pytest.mark.parametrize(
        "filename",
        [
            "",
            ".",
            "..",
            " report.pdf",
            "report.pdf ",
            "report\n.pdf",
            "report\x00.pdf",
            "folder/report.pdf",
            r"folder\report.pdf",
            "/etc/passwd.pdf",
            r"..\report.pdf",
        ],
    )
    def test_rejects_invalid_filenames(
        self,
        filename: str,
    ) -> None:
        with pytest.raises(DocumentValidationError):
            DEFAULT_VALIDATOR.validate_document(
                filename=filename,
                content_type=PDF_CONTENT_TYPE,
                size_bytes=1024,
            )

    def test_rejects_non_string_filename(self) -> None:
        with pytest.raises(
            DocumentValidationError,
            match="Document filename must be a non-empty string",
        ):
            DEFAULT_VALIDATOR.validate_document(
                filename=None,  # type: ignore[arg-type]
                content_type=PDF_CONTENT_TYPE,
                size_bytes=1024,
            )

    def test_rejects_filename_exceeding_maximum_length(self) -> None:
        filename = f"{'a' * 251}.pdf"

        with pytest.raises(
            DocumentValidationError,
            match="Document filename exceeds 255 characters",
        ):
            DEFAULT_VALIDATOR.validate_document(
                filename=filename,
                content_type=PDF_CONTENT_TYPE,
                size_bytes=1024,
            )

    def test_accepts_filename_at_maximum_length(self) -> None:
        filename = f"{'a' * 251}.pdf"

        result = DEFAULT_VALIDATOR.validate_document(
            filename=filename,
            content_type=PDF_CONTENT_TYPE,
            size_bytes=1024,
        )

        assert result["filename"] == filename

    def test_rejects_filename_without_extension(self) -> None:
        with pytest.raises(
            DocumentValidationError,
            match="Document filename must have a file extension",
        ):
            DEFAULT_VALIDATOR.validate_document(
                filename="report",
                content_type=PDF_CONTENT_TYPE,
                size_bytes=1024,
            )

    @pytest.mark.parametrize(
        "filename",
        [
            "report.exe",
            "report.zip",
            "report.json",
            "report.pdf.exe",
        ],
    )
    def test_rejects_unsupported_extensions(
        self,
        filename: str,
    ) -> None:
        with pytest.raises(
            DocumentValidationError,
            match="Unsupported document extension",
        ):
            DEFAULT_VALIDATOR.validate_document(
                filename=filename,
                content_type=PDF_CONTENT_TYPE,
                size_bytes=1024,
            )

    def test_normalizes_extension_to_lowercase(self) -> None:
        result = DEFAULT_VALIDATOR.validate_document(
            filename="REPORT.PDF",
            content_type=PDF_CONTENT_TYPE,
            size_bytes=1024,
        )

        assert result["extension"] == ".pdf"


class TestContentTypeValidation:
    """Tests for MIME type validation and normalization."""

    @pytest.mark.parametrize(
        ("filename", "content_type"),
        [
            (VALID_PDF_FILENAME, PDF_CONTENT_TYPE),
            (VALID_TEXT_FILENAME, TEXT_CONTENT_TYPE),
            (VALID_CSV_FILENAME, CSV_CONTENT_TYPE),
            ("report.doc", DOC_CONTENT_TYPE),
            (
                "report.docx",
                (
                    "application/vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                ),
            ),
            (
                "report.xlsx",
                (
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
            ),
        ],
    )
    def test_accepts_supported_content_types(
        self,
        filename: str,
        content_type: str,
    ) -> None:
        result = DEFAULT_VALIDATOR.validate_document(
            filename=filename,
            content_type=content_type,
            size_bytes=1024,
        )

        assert result["content_type"] == content_type

    def test_normalizes_content_type_case(self) -> None:
        result = DEFAULT_VALIDATOR.validate_document(
            filename=VALID_PDF_FILENAME,
            content_type="APPLICATION/PDF",
            size_bytes=1024,
        )

        assert result["content_type"] == PDF_CONTENT_TYPE

    def test_removes_content_type_parameters(self) -> None:
        result = DEFAULT_VALIDATOR.validate_document(
            filename=VALID_PDF_FILENAME,
            content_type="application/pdf; charset=binary",
            size_bytes=1024,
        )

        assert result["content_type"] == PDF_CONTENT_TYPE

    @pytest.mark.parametrize(
        "content_type",
        [
            "",
            " ",
            "application/octet-stream",
            "image/png",
            "application/json",
        ],
    )
    def test_rejects_unsupported_content_types(
        self,
        content_type: str,
    ) -> None:
        with pytest.raises(
            DocumentValidationError,
            match="Unsupported document content type",
        ):
            DEFAULT_VALIDATOR.validate_document(
                filename=VALID_PDF_FILENAME,
                content_type=content_type,
                size_bytes=1024,
            )

    def test_rejects_non_string_content_type(self) -> None:
        with pytest.raises(
            DocumentValidationError,
            match="Document content type must be a non-empty string",
        ):
            DEFAULT_VALIDATOR.validate_document(
                filename=VALID_PDF_FILENAME,
                content_type=None,  # type: ignore[arg-type]
                size_bytes=1024,
            )

    def test_rejects_extension_content_type_mismatch(self) -> None:
        with pytest.raises(
            DocumentValidationError,
            match="does not match declared content type",
        ):
            DEFAULT_VALIDATOR.validate_document(
                filename=VALID_PDF_FILENAME,
                content_type="image/png",
                size_bytes=1024,
            )

    def test_accepts_custom_content_type_and_extension_allowlists(
        self,
    ) -> None:
        validator = DocumentValidator(
            allowed_content_types=frozenset({"application/x-custom"}),
            allowed_extensions=frozenset({".custom"}),
        )

        result = validator.validate_document(
            filename="document.custom",
            content_type="application/x-custom",
            size_bytes=1024,
        )

        assert result["extension"] == ".custom"
        assert result["content_type"] == "application/x-custom"


class TestDocumentSizeValidation:
    """Tests for document size constraints."""

    def test_accepts_positive_document_size(self) -> None:
        result = DEFAULT_VALIDATOR.validate_document(
            filename=VALID_PDF_FILENAME,
            content_type=PDF_CONTENT_TYPE,
            size_bytes=1024,
        )

        assert result["size_bytes"] == 1024

    def test_accepts_document_at_maximum_size(self) -> None:
        validator = DocumentValidator(max_size_bytes=1024)

        result = validator.validate_document(
            filename=VALID_PDF_FILENAME,
            content_type=PDF_CONTENT_TYPE,
            size_bytes=1024,
        )

        assert result["size_bytes"] == 1024

    def test_rejects_document_exceeding_maximum_size(self) -> None:
        validator = DocumentValidator(max_size_bytes=1024)

        with pytest.raises(
            DocumentValidationError,
            match="exceeds the maximum allowed size",
        ):
            validator.validate_document(
                filename=VALID_PDF_FILENAME,
                content_type=PDF_CONTENT_TYPE,
                size_bytes=1025,
            )

    def test_rejects_empty_document(self) -> None:
        with pytest.raises(
            DocumentValidationError,
            match="Empty documents are not allowed",
        ):
            DEFAULT_VALIDATOR.validate_document(
                filename=VALID_PDF_FILENAME,
                content_type=PDF_CONTENT_TYPE,
                size_bytes=0,
            )

    def test_rejects_negative_document_size(self) -> None:
        with pytest.raises(
            DocumentValidationError,
            match="Document size cannot be negative",
        ):
            DEFAULT_VALIDATOR.validate_document(
                filename=VALID_PDF_FILENAME,
                content_type=PDF_CONTENT_TYPE,
                size_bytes=-1,
            )

    @pytest.mark.parametrize(
        "size_bytes",
        [
            True,
            False,
            1.5,
            "1024",
            None,
        ],
    )
    def test_rejects_non_integer_document_size(
        self,
        size_bytes: object,
    ) -> None:
        with pytest.raises(
            DocumentValidationError,
            match="Document size must be an integer",
        ):
            DEFAULT_VALIDATOR.validate_document(
                filename=VALID_PDF_FILENAME,
                content_type=PDF_CONTENT_TYPE,
                size_bytes=size_bytes,  # type: ignore[arg-type]
            )


class TestValidateDocument:
    """Tests for the complete document metadata validation operation."""

    def test_returns_normalized_document_properties(self) -> None:
        result = DEFAULT_VALIDATOR.validate_document(
            filename=VALID_PDF_FILENAME,
            content_type="application/pdf; charset=binary",
            size_bytes=2048,
        )

        assert result == {
            "filename": VALID_PDF_FILENAME,
            "extension": ".pdf",
            "content_type": PDF_CONTENT_TYPE,
            "size_bytes": 2048,
        }

    def test_does_not_modify_input_values(self) -> None:
        filename = VALID_PDF_FILENAME
        content_type = "APPLICATION/PDF; charset=binary"

        DEFAULT_VALIDATOR.validate_document(
            filename=filename,
            content_type=content_type,
            size_bytes=1024,
        )

        assert filename == VALID_PDF_FILENAME
        assert content_type == "APPLICATION/PDF; charset=binary"


class TestFileSignatureValidation:
    """Tests for file-header and declared MIME type consistency."""

    def test_accepts_valid_pdf_signature(self) -> None:
        DEFAULT_VALIDATOR.validate_file_signature(
            filename=VALID_PDF_FILENAME,
            content_type=PDF_CONTENT_TYPE,
            file_header=PDF_HEADER,
        )

    def test_rejects_invalid_pdf_signature(self) -> None:
        with pytest.raises(
            DocumentValidationError,
            match="Document content does not match declared content type",
        ):
            DEFAULT_VALIDATOR.validate_file_signature(
                filename=VALID_PDF_FILENAME,
                content_type=PDF_CONTENT_TYPE,
                file_header=b"not a PDF document",
            )

    def test_accepts_valid_legacy_word_signature(self) -> None:
        DEFAULT_VALIDATOR.validate_file_signature(
            filename="report.doc",
            content_type=DOC_CONTENT_TYPE,
            file_header=DOC_HEADER,
        )

    def test_rejects_invalid_legacy_word_signature(self) -> None:
        with pytest.raises(
            DocumentValidationError,
            match="Document content does not match declared content type",
        ):
            DEFAULT_VALIDATOR.validate_file_signature(
                filename="report.doc",
                content_type=DOC_CONTENT_TYPE,
                file_header=PDF_HEADER,
            )

    def test_accepts_valid_docx_signature(self) -> None:
        content_type = (
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        )

        DEFAULT_VALIDATOR.validate_file_signature(
            filename="report.docx",
            content_type=content_type,
            file_header=ZIP_HEADER,
        )

    def test_accepts_valid_xlsx_signature(self) -> None:
        content_type = (
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )

        DEFAULT_VALIDATOR.validate_file_signature(
            filename="report.xlsx",
            content_type=content_type,
            file_header=ZIP_HEADER,
        )

    def test_rejects_empty_file_header(self) -> None:
        with pytest.raises(
            DocumentValidationError,
            match="Document content cannot be empty",
        ):
            DEFAULT_VALIDATOR.validate_file_signature(
                filename=VALID_PDF_FILENAME,
                content_type=PDF_CONTENT_TYPE,
                file_header=b"",
            )

    def test_rejects_non_bytes_file_header(self) -> None:
        with pytest.raises(
            DocumentValidationError,
            match="File header must be supplied as bytes",
        ):
            DEFAULT_VALIDATOR.validate_file_signature(
                filename=VALID_PDF_FILENAME,
                content_type=PDF_CONTENT_TYPE,
                file_header="not bytes",  # type: ignore[arg-type]
            )

    def test_rejects_signature_extension_content_type_mismatch(
        self,
    ) -> None:
        with pytest.raises(
            DocumentValidationError,
            match="does not match declared content type",
        ):
            DEFAULT_VALIDATOR.validate_file_signature(
                filename=VALID_PDF_FILENAME,
                content_type=TEXT_CONTENT_TYPE,
                file_header=PDF_HEADER,
            )

    def test_accepts_non_empty_header_for_format_without_signature(
        self,
    ) -> None:
        DEFAULT_VALIDATOR.validate_file_signature(
            filename=VALID_TEXT_FILENAME,
            content_type=TEXT_CONTENT_TYPE,
            file_header=b"Document contents",
        )

    def test_does_not_claim_structural_validation_for_text_files(
        self,
    ) -> None:
        DEFAULT_VALIDATOR.validate_file_signature(
            filename=VALID_CSV_FILENAME,
            content_type=CSV_CONTENT_TYPE,
            file_header=b"column_a,column_b\n1,2",
        )

    def test_rejects_invalid_filename_before_signature_check(self) -> None:
        with pytest.raises(
            DocumentValidationError,
            match="Document filename must not contain path separators",
        ):
            DEFAULT_VALIDATOR.validate_file_signature(
                filename="../report.pdf",
                content_type=PDF_CONTENT_TYPE,
                file_header=PDF_HEADER,
            )