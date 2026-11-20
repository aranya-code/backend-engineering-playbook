"""Unit tests for document content processing."""

from __future__ import annotations

from io import BytesIO

import pytest
from docx import Document
from openpyxl import Workbook
from pypdf import PdfWriter

from processing.document_processor import DocumentProcessor


PDF_CONTENT_TYPE = "application/pdf"
DOCX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument."
    "wordprocessingml.document"
)
XLSX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
TEXT_CONTENT_TYPE = "text/plain"
CSV_CONTENT_TYPE = "text/csv"


@pytest.fixture
def processor() -> DocumentProcessor:
    """Return a fresh document processor for each test."""
    return DocumentProcessor()


@pytest.fixture
def sample_pdf() -> bytes:
    """Create a minimal valid PDF document."""
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)

    buffer = BytesIO()
    writer.write(buffer)

    return buffer.getvalue()


@pytest.fixture
def sample_docx() -> bytes:
    """Create a DOCX document containing representative text."""
    document = Document()
    document.add_heading("Document Processing Test", level=1)
    document.add_paragraph(
        "This document verifies text extraction from a DOCX file."
    )
    document.add_paragraph("The processing pipeline must preserve this text.")

    buffer = BytesIO()
    document.save(buffer)

    return buffer.getvalue()


@pytest.fixture
def sample_xlsx() -> bytes:
    """Create an XLSX workbook containing representative tabular data."""
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Employees"

    worksheet.append(["employee_id", "name", "department"])
    worksheet.append([1, "Alice", "Engineering"])
    worksheet.append([2, "Bob", "Finance"])

    buffer = BytesIO()
    workbook.save(buffer)

    return buffer.getvalue()


@pytest.fixture
def sample_text() -> bytes:
    """Return representative UTF-8 text content."""
    return (
        "Document Processing Test\n"
        "The pipeline extracts text from plain-text documents.\n"
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


@pytest.fixture
def sample_metadata() -> dict[str, object]:
    """Return representative metadata supplied by the ingestion pipeline."""
    return {
        "object_id": "documents/incoming/sample-document.pdf",
        "bucket_name": "documents",
        "object_key": "incoming/sample-document.pdf",
        "content_type": PDF_CONTENT_TYPE,
        "size_bytes": 1024,
        "etag": "sample-etag",
    }


def process_document(
    processor: DocumentProcessor,
    *,
    document: bytes,
    metadata: dict[str, object],
    filename: str,
    content_type: str,
) -> dict[str, object]:
    """Invoke the public document-processing interface."""
    return processor.process_document(
        document=document,
        metadata=metadata,
        filename=filename,
        content_type=content_type,
    )


class TestDocumentProcessorInitialization:
    """Tests for processor construction."""

    def test_can_create_processor(self) -> None:
        processor = DocumentProcessor()

        assert isinstance(processor, DocumentProcessor)


class TestPDFProcessing:
    """Tests for PDF document processing."""

    def test_processes_valid_pdf(
        self,
        processor: DocumentProcessor,
        sample_pdf: bytes,
        sample_metadata: dict[str, object],
    ) -> None:
        result = process_document(
            processor,
            document=sample_pdf,
            metadata=sample_metadata,
            filename="report.pdf",
            content_type=PDF_CONTENT_TYPE,
        )

        assert isinstance(result, dict)

    def test_returns_processing_result(
        self,
        processor: DocumentProcessor,
        sample_pdf: bytes,
        sample_metadata: dict[str, object],
    ) -> None:
        result = process_document(
            processor,
            document=sample_pdf,
            metadata=sample_metadata,
            filename="report.pdf",
            content_type=PDF_CONTENT_TYPE,
        )

        assert result

    def test_handles_pdf_without_extractable_text(
        self,
        processor: DocumentProcessor,
        sample_pdf: bytes,
        sample_metadata: dict[str, object],
    ) -> None:
        result = process_document(
            processor,
            document=sample_pdf,
            metadata=sample_metadata,
            filename="blank.pdf",
            content_type=PDF_CONTENT_TYPE,
        )

        assert isinstance(result, dict)

    def test_rejects_invalid_pdf(
        self,
        processor: DocumentProcessor,
        sample_metadata: dict[str, object],
    ) -> None:
        with pytest.raises((ValueError, RuntimeError)):
            process_document(
                processor,
                document=b"This is not a valid PDF.",
                metadata=sample_metadata,
                filename="invalid.pdf",
                content_type=PDF_CONTENT_TYPE,
            )


class TestDOCXProcessing:
    """Tests for Microsoft Word DOCX processing."""

    def test_processes_valid_docx(
        self,
        processor: DocumentProcessor,
        sample_docx: bytes,
        sample_metadata: dict[str, object],
    ) -> None:
        result = process_document(
            processor,
            document=sample_docx,
            metadata=sample_metadata,
            filename="report.docx",
            content_type=DOCX_CONTENT_TYPE,
        )

        assert isinstance(result, dict)

    def test_extracts_docx_text(
        self,
        processor: DocumentProcessor,
        sample_docx: bytes,
        sample_metadata: dict[str, object],
    ) -> None:
        result = process_document(
            processor,
            document=sample_docx,
            metadata=sample_metadata,
            filename="report.docx",
            content_type=DOCX_CONTENT_TYPE,
        )

        assert "Document Processing Test" in str(result)
        assert "preserve this text" in str(result)

    def test_rejects_invalid_docx(
        self,
        processor: DocumentProcessor,
        sample_metadata: dict[str, object],
    ) -> None:
        with pytest.raises((ValueError, RuntimeError)):
            process_document(
                processor,
                document=b"Not a valid DOCX document.",
                metadata=sample_metadata,
                filename="invalid.docx",
                content_type=DOCX_CONTENT_TYPE,
            )


class TestXLSXProcessing:
    """Tests for Microsoft Excel XLSX processing."""

    def test_processes_valid_xlsx(
        self,
        processor: DocumentProcessor,
        sample_xlsx: bytes,
        sample_metadata: dict[str, object],
    ) -> None:
        result = process_document(
            processor,
            document=sample_xlsx,
            metadata=sample_metadata,
            filename="employees.xlsx",
            content_type=XLSX_CONTENT_TYPE,
        )

        assert isinstance(result, dict)

    def test_extracts_xlsx_worksheet_content(
        self,
        processor: DocumentProcessor,
        sample_xlsx: bytes,
        sample_metadata: dict[str, object],
    ) -> None:
        result = process_document(
            processor,
            document=sample_xlsx,
            metadata=sample_metadata,
            filename="employees.xlsx",
            content_type=XLSX_CONTENT_TYPE,
        )

        serialized_result = str(result)

        assert "Employees" in serialized_result
        assert "Alice" in serialized_result
        assert "Engineering" in serialized_result

    def test_handles_multiple_worksheets(
        self,
        processor: DocumentProcessor,
        sample_metadata: dict[str, object],
    ) -> None:
        workbook = Workbook()
        first_sheet = workbook.active
        first_sheet.title = "Employees"
        first_sheet.append(["id", "name"])
        first_sheet.append([1, "Alice"])

        second_sheet = workbook.create_sheet("Departments")
        second_sheet.append(["id", "department"])
        second_sheet.append([1, "Engineering"])

        buffer = BytesIO()
        workbook.save(buffer)

        result = process_document(
            processor,
            document=buffer.getvalue(),
            metadata=sample_metadata,
            filename="multiple-sheets.xlsx",
            content_type=XLSX_CONTENT_TYPE,
        )

        serialized_result = str(result)

        assert "Employees" in serialized_result
        assert "Departments" in serialized_result

    def test_rejects_invalid_xlsx(
        self,
        processor: DocumentProcessor,
        sample_metadata: dict[str, object],
    ) -> None:
        with pytest.raises((ValueError, RuntimeError)):
            process_document(
                processor,
                document=b"Not a valid XLSX document.",
                metadata=sample_metadata,
                filename="invalid.xlsx",
                content_type=XLSX_CONTENT_TYPE,
            )


class TestPlainTextProcessing:
    """Tests for plain-text document processing."""

    def test_processes_valid_text(
        self,
        processor: DocumentProcessor,
        sample_text: bytes,
        sample_metadata: dict[str, object],
    ) -> None:
        result = process_document(
            processor,
            document=sample_text,
            metadata=sample_metadata,
            filename="notes.txt",
            content_type=TEXT_CONTENT_TYPE,
        )

        assert isinstance(result, dict)

    def test_extracts_text_content(
        self,
        processor: DocumentProcessor,
        sample_text: bytes,
        sample_metadata: dict[str, object],
    ) -> None:
        result = process_document(
            processor,
            document=sample_text,
            metadata=sample_metadata,
            filename="notes.txt",
            content_type=TEXT_CONTENT_TYPE,
        )

        assert "Document Processing Test" in str(result)

    def test_preserves_unicode_content(
        self,
        processor: DocumentProcessor,
        sample_text: bytes,
        sample_metadata: dict[str, object],
    ) -> None:
        result = process_document(
            processor,
            document=sample_text,
            metadata=sample_metadata,
            filename="unicode.txt",
            content_type=TEXT_CONTENT_TYPE,
        )

        serialized_result = str(result)

        assert "café" in serialized_result
        assert "東京" in serialized_result

    def test_handles_empty_text_document(
        self,
        processor: DocumentProcessor,
        sample_metadata: dict[str, object],
    ) -> None:
        result = process_document(
            processor,
            document=b"",
            metadata=sample_metadata,
            filename="empty.txt",
            content_type=TEXT_CONTENT_TYPE,
        )

        assert isinstance(result, dict)


class TestCSVProcessing:
    """Tests for CSV document processing."""

    def test_processes_valid_csv(
        self,
        processor: DocumentProcessor,
        sample_csv: bytes,
        sample_metadata: dict[str, object],
    ) -> None:
        result = process_document(
            processor,
            document=sample_csv,
            metadata=sample_metadata,
            filename="employees.csv",
            content_type=CSV_CONTENT_TYPE,
        )

        assert isinstance(result, dict)

    def test_extracts_csv_rows_and_columns(
        self,
        processor: DocumentProcessor,
        sample_csv: bytes,
        sample_metadata: dict[str, object],
    ) -> None:
        result = process_document(
            processor,
            document=sample_csv,
            metadata=sample_metadata,
            filename="employees.csv",
            content_type=CSV_CONTENT_TYPE,
        )

        serialized_result = str(result)

        assert "employee_id" in serialized_result
        assert "Alice" in serialized_result
        assert "Engineering" in serialized_result

    def test_handles_quoted_csv_values(
        self,
        processor: DocumentProcessor,
        sample_metadata: dict[str, object],
    ) -> None:
        document = (
            b'id,name,description\n'
            b'1,Alice,"Backend engineer, platform team"\n'
            b'2,Bob,"Finance, operations"\n'
        )

        result = process_document(
            processor,
            document=document,
            metadata=sample_metadata,
            filename="quoted.csv",
            content_type=CSV_CONTENT_TYPE,
        )

        assert isinstance(result, dict)

    def test_handles_header_only_csv(
        self,
        processor: DocumentProcessor,
        sample_metadata: dict[str, object],
    ) -> None:
        result = process_document(
            processor,
            document=b"employee_id,name,department\n",
            metadata=sample_metadata,
            filename="header-only.csv",
            content_type=CSV_CONTENT_TYPE,
        )

        assert isinstance(result, dict)


class TestDocumentProcessorInputValidation:
    """Tests for invalid inputs and unsupported document formats."""

    @pytest.mark.parametrize(
        ("filename", "content_type"),
        [
            ("report.exe", "application/octet-stream"),
            ("report.json", "application/json"),
            ("report.doc", "application/msword"),
        ],
    )
    def test_rejects_unsupported_formats(
        self,
        processor: DocumentProcessor,
        sample_metadata: dict[str, object],
        filename: str,
        content_type: str,
    ) -> None:
        with pytest.raises((ValueError, RuntimeError)):
            process_document(
                processor,
                document=b"Document content",
                metadata=sample_metadata,
                filename=filename,
                content_type=content_type,
            )

    def test_rejects_filename_content_type_mismatch(
        self,
        processor: DocumentProcessor,
        sample_metadata: dict[str, object],
    ) -> None:
        with pytest.raises((ValueError, RuntimeError)):
            process_document(
                processor,
                document=b"Document content",
                metadata=sample_metadata,
                filename="report.txt",
                content_type=PDF_CONTENT_TYPE,
            )

    def test_rejects_empty_filename(
        self,
        processor: DocumentProcessor,
        sample_metadata: dict[str, object],
    ) -> None:
        with pytest.raises((TypeError, ValueError, RuntimeError)):
            process_document(
                processor,
                document=b"Document content",
                metadata=sample_metadata,
                filename="",
                content_type=TEXT_CONTENT_TYPE,
            )

    def test_rejects_empty_content_type(
        self,
        processor: DocumentProcessor,
        sample_metadata: dict[str, object],
    ) -> None:
        with pytest.raises((TypeError, ValueError, RuntimeError)):
            process_document(
                processor,
                document=b"Document content",
                metadata=sample_metadata,
                filename="notes.txt",
                content_type="",
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
        processor: DocumentProcessor,
        sample_metadata: dict[str, object],
        document: object,
    ) -> None:
        with pytest.raises((TypeError, ValueError, RuntimeError)):
            process_document(
                processor,
                document=document,  # type: ignore[arg-type]
                metadata=sample_metadata,
                filename="notes.txt",
                content_type=TEXT_CONTENT_TYPE,
            )

    def test_rejects_non_mapping_metadata(
        self,
        processor: DocumentProcessor,
    ) -> None:
        with pytest.raises((TypeError, ValueError, RuntimeError)):
            processor.process_document(
                document=b"Document content",
                metadata=None,  # type: ignore[arg-type]
                filename="notes.txt",
                content_type=TEXT_CONTENT_TYPE,
            )

    def test_rejects_invalid_metadata_values(
        self,
        processor: DocumentProcessor,
    ) -> None:
        with pytest.raises((TypeError, ValueError, RuntimeError)):
            processor.process_document(
                document=b"Document content",
                metadata={"object_id": None},
                filename="notes.txt",
                content_type=TEXT_CONTENT_TYPE,
            )


class TestDocumentProcessorMetadataHandling:
    """Tests for metadata propagation and input isolation."""

    def test_accepts_metadata_mapping(
        self,
        processor: DocumentProcessor,
        sample_text: bytes,
        sample_metadata: dict[str, object],
    ) -> None:
        result = process_document(
            processor,
            document=sample_text,
            metadata=sample_metadata,
            filename="notes.txt",
            content_type=TEXT_CONTENT_TYPE,
        )

        assert isinstance(result, dict)

    def test_does_not_modify_input_document(
        self,
        processor: DocumentProcessor,
        sample_text: bytes,
        sample_metadata: dict[str, object],
    ) -> None:
        original_document = sample_text

        process_document(
            processor,
            document=sample_text,
            metadata=sample_metadata,
            filename="notes.txt",
            content_type=TEXT_CONTENT_TYPE,
        )

        assert sample_text == original_document

    def test_does_not_modify_input_metadata(
        self,
        processor: DocumentProcessor,
        sample_text: bytes,
        sample_metadata: dict[str, object],
    ) -> None:
        original_metadata = sample_metadata.copy()

        process_document(
            processor,
            document=sample_text,
            metadata=sample_metadata,
            filename="notes.txt",
            content_type=TEXT_CONTENT_TYPE,
        )

        assert sample_metadata == original_metadata


class TestDocumentProcessorFailureHandling:
    """Tests for malformed documents and parser failures."""

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
                b"PK\x03\x04invalid",
            ),
            (
                "invalid.xlsx",
                XLSX_CONTENT_TYPE,
                b"PK\x03\x04invalid",
            ),
        ],
    )
    def test_rejects_malformed_binary_documents(
        self,
        processor: DocumentProcessor,
        sample_metadata: dict[str, object],
        filename: str,
        content_type: str,
        document: bytes,
    ) -> None:
        with pytest.raises((ValueError, RuntimeError, OSError)):
            process_document(
                processor,
                document=document,
                metadata=sample_metadata,
                filename=filename,
                content_type=content_type,
            )