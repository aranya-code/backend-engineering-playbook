"""Unit tests for document metadata extraction."""

from __future__ import annotations

from io import BytesIO
from unittest.mock import MagicMock

import pytest
from docx import Document
from openpyxl import Workbook
from pypdf import PdfReader, PdfWriter

from ingestion.metadata_extractor import MetadataExtractor


PDF_CONTENT_TYPE = "application/pdf"
DOCX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument."
    "wordprocessingml.document"
)
XLSX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument."
    "spreadsheetml.sheet"
)
TEXT_CONTENT_TYPE = "text/plain"
CSV_CONTENT_TYPE = "text/csv"


@pytest.fixture
def extractor() -> MetadataExtractor:
    """Return a fresh metadata extractor for each test."""
    return MetadataExtractor()


@pytest.fixture
def sample_pdf() -> bytes:
    """Build a minimal valid PDF document in memory."""
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)

    metadata = {
        "/Title": "Sample PDF",
        "/Author": "Test Author",
        "/Subject": "Metadata extraction test",
        "/Creator": "pytest",
    }
    writer.add_metadata(metadata)

    buffer = BytesIO()
    writer.write(buffer)

    return buffer.getvalue()


@pytest.fixture
def sample_docx() -> bytes:
    """Build a DOCX document with representative core properties."""
    document = Document()
    document.add_heading("Sample Document", level=1)
    document.add_paragraph("Document metadata extraction test.")

    document.core_properties.title = "Sample DOCX"
    document.core_properties.author = "Test Author"
    document.core_properties.subject = "Metadata extraction test"
    document.core_properties.keywords = "pytest, metadata, document"

    buffer = BytesIO()
    document.save(buffer)

    return buffer.getvalue()


@pytest.fixture
def sample_xlsx() -> bytes:
    """Build an XLSX workbook with worksheet and workbook metadata."""
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Employees"

    worksheet.append(["employee_id", "name", "department"])
    worksheet.append([1, "Alice", "Engineering"])
    worksheet.append([2, "Bob", "Finance"])

    workbook.properties.title = "Sample Workbook"
    workbook.properties.creator = "Test Author"
    workbook.properties.subject = "Metadata extraction test"
    workbook.properties.keywords = "pytest, spreadsheet"

    buffer = BytesIO()
    workbook.save(buffer)

    return buffer.getvalue()


@pytest.fixture
def sample_text() -> bytes:
    """Return representative UTF-8 text content."""
    return (
        "Document ingestion pipeline\n"
        "Metadata extraction test.\n"
        "Unicode content: café, résumé, 東京.\n"
    ).encode("utf-8")


@pytest.fixture
def sample_csv() -> bytes:
    """Return representative CSV content."""
    return (
        "employee_id,name,department\n"
        "1,Alice,Engineering\n"
        "2,Bob,Finance\n"
    ).encode("utf-8")


class TestMetadataExtractorInitialization:
    """Tests for metadata extractor construction."""

    def test_can_create_extractor(self) -> None:
        extractor = MetadataExtractor()

        assert isinstance(extractor, MetadataExtractor)


class TestPDFMetadataExtraction:
    """Tests for PDF metadata extraction."""

    def test_extracts_metadata_from_valid_pdf(
        self,
        extractor: MetadataExtractor,
        sample_pdf: bytes,
    ) -> None:
        result = extractor.extract_metadata(
            document=sample_pdf,
            filename="report.pdf",
            content_type=PDF_CONTENT_TYPE,
        )

        assert isinstance(result, dict)
        assert result

    def test_extracts_pdf_document_information(
        self,
        extractor: MetadataExtractor,
        sample_pdf: bytes,
    ) -> None:
        result = extractor.extract_metadata(
            document=sample_pdf,
            filename="report.pdf",
            content_type=PDF_CONTENT_TYPE,
        )

        serialized_metadata = str(result).lower()

        assert "sample pdf" in serialized_metadata
        assert "test author" in serialized_metadata

    def test_extracts_pdf_page_count(
        self,
        extractor: MetadataExtractor,
        sample_pdf: bytes,
    ) -> None:
        result = extractor.extract_metadata(
            document=sample_pdf,
            filename="report.pdf",
            content_type=PDF_CONTENT_TYPE,
        )

        serialized_metadata = str(result).lower()

        assert "page" in serialized_metadata

    def test_handles_pdf_without_document_metadata(
        self,
        extractor: MetadataExtractor,
    ) -> None:
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)

        buffer = BytesIO()
        writer.write(buffer)

        result = extractor.extract_metadata(
            document=buffer.getvalue(),
            filename="minimal.pdf",
            content_type=PDF_CONTENT_TYPE,
        )

        assert isinstance(result, dict)

    def test_rejects_invalid_pdf_content(
        self,
        extractor: MetadataExtractor,
    ) -> None:
        with pytest.raises((ValueError, RuntimeError)):
            extractor.extract_metadata(
                document=b"This is not a PDF document.",
                filename="invalid.pdf",
                content_type=PDF_CONTENT_TYPE,
            )


class TestDOCXMetadataExtraction:
    """Tests for Microsoft Word DOCX metadata extraction."""

    def test_extracts_metadata_from_valid_docx(
        self,
        extractor: MetadataExtractor,
        sample_docx: bytes,
    ) -> None:
        result = extractor.extract_metadata(
            document=sample_docx,
            filename="report.docx",
            content_type=DOCX_CONTENT_TYPE,
        )

        assert isinstance(result, dict)
        assert result

    def test_extracts_docx_core_properties(
        self,
        extractor: MetadataExtractor,
        sample_docx: bytes,
    ) -> None:
        result = extractor.extract_metadata(
            document=sample_docx,
            filename="report.docx",
            content_type=DOCX_CONTENT_TYPE,
        )

        serialized_metadata = str(result).lower()

        assert "sample docx" in serialized_metadata
        assert "test author" in serialized_metadata

    def test_handles_docx_without_document_properties(
        self,
        extractor: MetadataExtractor,
    ) -> None:
        document = Document()
        document.add_paragraph("Document without custom properties.")

        buffer = BytesIO()
        document.save(buffer)

        result = extractor.extract_metadata(
            document=buffer.getvalue(),
            filename="minimal.docx",
            content_type=DOCX_CONTENT_TYPE,
        )

        assert isinstance(result, dict)

    def test_rejects_invalid_docx_content(
        self,
        extractor: MetadataExtractor,
    ) -> None:
        with pytest.raises((ValueError, RuntimeError)):
            extractor.extract_metadata(
                document=b"This is not a DOCX document.",
                filename="invalid.docx",
                content_type=DOCX_CONTENT_TYPE,
            )


class TestXLSXMetadataExtraction:
    """Tests for Microsoft Excel XLSX metadata extraction."""

    def test_extracts_metadata_from_valid_xlsx(
        self,
        extractor: MetadataExtractor,
        sample_xlsx: bytes,
    ) -> None:
        result = extractor.extract_metadata(
            document=sample_xlsx,
            filename="employees.xlsx",
            content_type=XLSX_CONTENT_TYPE,
        )

        assert isinstance(result, dict)
        assert result

    def test_extracts_xlsx_workbook_properties(
        self,
        extractor: MetadataExtractor,
        sample_xlsx: bytes,
    ) -> None:
        result = extractor.extract_metadata(
            document=sample_xlsx,
            filename="employees.xlsx",
            content_type=XLSX_CONTENT_TYPE,
        )

        serialized_metadata = str(result).lower()

        assert "sample workbook" in serialized_metadata
        assert "test author" in serialized_metadata

    def test_extracts_xlsx_worksheet_information(
        self,
        extractor: MetadataExtractor,
        sample_xlsx: bytes,
    ) -> None:
        result = extractor.extract_metadata(
            document=sample_xlsx,
            filename="employees.xlsx",
            content_type=XLSX_CONTENT_TYPE,
        )

        serialized_metadata = str(result).lower()

        assert "employees" in serialized_metadata

    def test_handles_xlsx_with_multiple_worksheets(
        self,
        extractor: MetadataExtractor,
    ) -> None:
        workbook = Workbook()
        first_sheet = workbook.active
        first_sheet.title = "Employees"
        first_sheet.append(["id", "name"])

        second_sheet = workbook.create_sheet("Departments")
        second_sheet.append(["id", "department"])

        buffer = BytesIO()
        workbook.save(buffer)

        result = extractor.extract_metadata(
            document=buffer.getvalue(),
            filename="multiple-sheets.xlsx",
            content_type=XLSX_CONTENT_TYPE,
        )

        serialized_metadata = str(result).lower()

        assert "employees" in serialized_metadata
        assert "departments" in serialized_metadata

    def test_rejects_invalid_xlsx_content(
        self,
        extractor: MetadataExtractor,
    ) -> None:
        with pytest.raises((ValueError, RuntimeError)):
            extractor.extract_metadata(
                document=b"This is not an XLSX document.",
                filename="invalid.xlsx",
                content_type=XLSX_CONTENT_TYPE,
            )


class TestTextMetadataExtraction:
    """Tests for plain-text document metadata extraction."""

    def test_extracts_metadata_from_text_document(
        self,
        extractor: MetadataExtractor,
        sample_text: bytes,
    ) -> None:
        result = extractor.extract_metadata(
            document=sample_text,
            filename="notes.txt",
            content_type=TEXT_CONTENT_TYPE,
        )

        assert isinstance(result, dict)
        assert result

    def test_preserves_text_document_content_information(
        self,
        extractor: MetadataExtractor,
        sample_text: bytes,
    ) -> None:
        result = extractor.extract_metadata(
            document=sample_text,
            filename="notes.txt",
            content_type=TEXT_CONTENT_TYPE,
        )

        serialized_metadata = str(result)

        assert "Document ingestion pipeline" in serialized_metadata

    def test_handles_unicode_text(
        self,
        extractor: MetadataExtractor,
        sample_text: bytes,
    ) -> None:
        result = extractor.extract_metadata(
            document=sample_text,
            filename="unicode.txt",
            content_type=TEXT_CONTENT_TYPE,
        )

        serialized_metadata = str(result)

        assert "café" in serialized_metadata
        assert "東京" in serialized_metadata

    def test_handles_empty_text_content(
        self,
        extractor: MetadataExtractor,
    ) -> None:
        result = extractor.extract_metadata(
            document=b"",
            filename="empty.txt",
            content_type=TEXT_CONTENT_TYPE,
        )

        assert isinstance(result, dict)


class TestCSVMetadataExtraction:
    """Tests for CSV document metadata extraction."""

    def test_extracts_metadata_from_csv_document(
        self,
        extractor: MetadataExtractor,
        sample_csv: bytes,
    ) -> None:
        result = extractor.extract_metadata(
            document=sample_csv,
            filename="employees.csv",
            content_type=CSV_CONTENT_TYPE,
        )

        assert isinstance(result, dict)
        assert result

    def test_extracts_csv_column_information(
        self,
        extractor: MetadataExtractor,
        sample_csv: bytes,
    ) -> None:
        result = extractor.extract_metadata(
            document=sample_csv,
            filename="employees.csv",
            content_type=CSV_CONTENT_TYPE,
        )

        serialized_metadata = str(result).lower()

        assert "employee_id" in serialized_metadata
        assert "name" in serialized_metadata
        assert "department" in serialized_metadata

    def test_handles_csv_with_quoted_values(
        self,
        extractor: MetadataExtractor,
    ) -> None:
        document = (
            'id,name,description\n'
            '1,Alice,"Backend engineer, platform team"\n'
            '2,Bob,"Finance, operations"\n'
        ).encode("utf-8")

        result = extractor.extract_metadata(
            document=document,
            filename="quoted.csv",
            content_type=CSV_CONTENT_TYPE,
        )

        assert isinstance(result, dict)

    def test_handles_csv_with_bom(
        self,
        extractor: MetadataExtractor,
    ) -> None:
        document = (
            "\ufeffemployee_id,name\n"
            "1,Alice\n"
        ).encode("utf-8")

        result = extractor.extract_metadata(
            document=document,
            filename="bom.csv",
            content_type=CSV_CONTENT_TYPE,
        )

        assert isinstance(result, dict)

    def test_handles_csv_with_header_only(
        self,
        extractor: MetadataExtractor,
    ) -> None:
        document = b"employee_id,name,department\n"

        result = extractor.extract_metadata(
            document=document,
            filename="header-only.csv",
            content_type=CSV_CONTENT_TYPE,
        )

        assert isinstance(result, dict)


class TestMetadataExtractorInputValidation:
    """Tests for invalid inputs and unsupported document formats."""

    @pytest.mark.parametrize(
        ("filename", "content_type"),
        [
            ("report.exe", "application/octet-stream"),
            ("report.json", "application/json"),
            ("report.doc", "application/msword"),
        ],
    )
    def test_rejects_unsupported_document_formats(
        self,
        extractor: MetadataExtractor,
        filename: str,
        content_type: str,
    ) -> None:
        with pytest.raises((ValueError, RuntimeError)):
            extractor.extract_metadata(
                document=b"Some document content.",
                filename=filename,
                content_type=content_type,
            )

    def test_rejects_filename_content_type_mismatch(
        self,
        extractor: MetadataExtractor,
    ) -> None:
        with pytest.raises((ValueError, RuntimeError)):
            extractor.extract_metadata(
                document=b"%PDF-1.7",
                filename="report.txt",
                content_type=PDF_CONTENT_TYPE,
            )

    @pytest.mark.parametrize(
        "document",
        [
            None,
            "document content",
            123,
            bytearray(b"document content"),
        ],
    )
    def test_rejects_non_bytes_document(
        self,
        extractor: MetadataExtractor,
        document: object,
    ) -> None:
        with pytest.raises((TypeError, ValueError, RuntimeError)):
            extractor.extract_metadata(
                document=document,  # type: ignore[arg-type]
                filename="notes.txt",
                content_type=TEXT_CONTENT_TYPE,
            )

    def test_rejects_non_string_filename(
        self,
        extractor: MetadataExtractor,
    ) -> None:
        with pytest.raises((TypeError, ValueError, RuntimeError)):
            extractor.extract_metadata(
                document=b"Document content",
                filename=None,  # type: ignore[arg-type]
                content_type=TEXT_CONTENT_TYPE,
            )

    def test_rejects_non_string_content_type(
        self,
        extractor: MetadataExtractor,
    ) -> None:
        with pytest.raises((TypeError, ValueError, RuntimeError)):
            extractor.extract_metadata(
                document=b"Document content",
                filename="notes.txt",
                content_type=None,  # type: ignore[arg-type]
            )

    def test_rejects_legacy_doc_format(
        self,
        extractor: MetadataExtractor,
    ) -> None:
        with pytest.raises((ValueError, RuntimeError)):
            extractor.extract_metadata(
                document=b"Legacy Word document content",
                filename="legacy.doc",
                content_type=(
                    "application/msword"
                ),
            )

    def test_does_not_modify_input_document(
        self,
        extractor: MetadataExtractor,
        sample_text: bytes,
    ) -> None:
        original_document = sample_text

        extractor.extract_metadata(
            document=sample_text,
            filename="notes.txt",
            content_type=TEXT_CONTENT_TYPE,
        )

        assert sample_text == original_document


class TestMetadataExtractorFailureHandling:
    """Tests for parser failures and malformed document payloads."""

    @pytest.mark.parametrize(
        ("filename", "content_type", "document"),
        [
            (
                "invalid.pdf",
                PDF_CONTENT_TYPE,
                b"%PDF-invalid-content",
            ),
            (
                "invalid.docx",
                DOCX_CONTENT_TYPE,
                ZIP_HEADER := b"PK\x03\x04invalid",
            ),
            (
                "invalid.xlsx",
                XLSX_CONTENT_TYPE,
                b"PK\x03\x04invalid",
            ),
        ],
    )
    def test_handles_malformed_binary_documents(
        self,
        extractor: MetadataExtractor,
        filename: str,
        content_type: str,
        document: bytes,
    ) -> None:
        with pytest.raises((ValueError, RuntimeError, OSError)):
            extractor.extract_metadata(
                document=document,
                filename=filename,
                content_type=content_type,
            )

    def test_does_not_return_partial_metadata_for_invalid_pdf(
        self,
        extractor: MetadataExtractor,
    ) -> None:
        with pytest.raises((ValueError, RuntimeError)):
            extractor.extract_metadata(
                document=b"not-a-pdf",
                filename="invalid.pdf",
                content_type=PDF_CONTENT_TYPE,
            )