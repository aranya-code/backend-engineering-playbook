"""Document content processing for the S3 ingestion pipeline.

Extracts text and document-level information from supported PDF, DOCX,
XLSX, TXT, and CSV documents.

The processor is independent of AWS services. It accepts document bytes
and ingestion metadata, making it suitable for Lambda execution and
unit testing.
"""

from __future__ import annotations

import csv
import io
import logging
import zipfile
from collections.abc import Mapping
from typing import Any

from docx import Document
from openpyxl import load_workbook
from pypdf import PdfReader

from ingestion.document_validator import (
    DocumentValidationError,
    DocumentValidator,
)

logger = logging.getLogger(__name__)

DEFAULT_MAX_EXTRACTED_TEXT_CHARACTERS = 1_000_000
DEFAULT_MAX_CSV_ROWS = 100_000
DEFAULT_MAX_WORKSHEET_ROWS = 100_000
DEFAULT_MAX_WORKSHEET_COLUMNS = 1_000

PDF_CONTENT_TYPE = "application/pdf"
WORD_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument."
    "wordprocessingml.document"
)
EXCEL_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument."
    "spreadsheetml.sheet"
)
TEXT_CONTENT_TYPE = "text/plain"
CSV_CONTENT_TYPE = "text/csv"

LEGACY_WORD_CONTENT_TYPE = "application/msword"

SUPPORTED_CONTENT_TYPES = frozenset(
    {
        PDF_CONTENT_TYPE,
        WORD_CONTENT_TYPE,
        EXCEL_CONTENT_TYPE,
        TEXT_CONTENT_TYPE,
        CSV_CONTENT_TYPE,
    }
)


class DocumentProcessingError(RuntimeError):
    """Raised when document content cannot be processed."""


class UnsupportedDocumentFormatError(DocumentProcessingError):
    """Raised when a document format has no available extractor."""


class DocumentProcessor:
    """Extract content and structural information from uploaded documents.

    Supported formats:
        - PDF: Text extraction using pypdf.
        - DOCX: Paragraph and table text extraction using python-docx.
        - XLSX: Worksheet names, dimensions, and cell values using openpyxl.
        - TXT: UTF-8 text extraction.
        - CSV: UTF-8 CSV parsing and row statistics.

    Legacy binary DOC files are accepted by the ingestion validator but
    cannot be text-extracted with the dependencies currently declared by
    this project.
    """

    def __init__(
        self,
        *,
        validator: DocumentValidator | None = None,
        max_extracted_text_characters: int = (
            DEFAULT_MAX_EXTRACTED_TEXT_CHARACTERS
        ),
        max_csv_rows: int = DEFAULT_MAX_CSV_ROWS,
        max_worksheet_rows: int = DEFAULT_MAX_WORKSHEET_ROWS,
        max_worksheet_columns: int = DEFAULT_MAX_WORKSHEET_COLUMNS,
    ) -> None:
        """Initialize the processor and its extraction limits."""
        if max_extracted_text_characters <= 0:
            raise ValueError(
                "max_extracted_text_characters must be greater than zero."
            )

        if max_csv_rows <= 0:
            raise ValueError("max_csv_rows must be greater than zero.")

        if max_worksheet_rows <= 0:
            raise ValueError(
                "max_worksheet_rows must be greater than zero."
            )

        if max_worksheet_columns <= 0:
            raise ValueError(
                "max_worksheet_columns must be greater than zero."
            )

        self.validator = (
            validator if validator is not None else DocumentValidator()
        )
        self.max_extracted_text_characters = (
            max_extracted_text_characters
        )
        self.max_csv_rows = max_csv_rows
        self.max_worksheet_rows = max_worksheet_rows
        self.max_worksheet_columns = max_worksheet_columns

    @staticmethod
    def _normalize_content_type(content_type: str) -> str:
        """Normalize a MIME type by removing optional parameters."""
        if not isinstance(content_type, str) or not content_type.strip():
            raise DocumentProcessingError(
                "Document content type must be a non-empty string."
            )

        return content_type.split(";", maxsplit=1)[0].strip().lower()

    @staticmethod
    def _validate_metadata(metadata: Mapping[str, Any]) -> dict[str, Any]:
        """Return a shallow copy of the ingestion metadata."""
        if not isinstance(metadata, Mapping):
            raise DocumentProcessingError(
                "Document metadata must be a mapping."
            )

        return dict(metadata)

    @staticmethod
    def _decode_text(document: bytes, *, filename: str) -> str:
        """Decode a text document using UTF-8 with BOM support."""
        try:
            return document.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise DocumentProcessingError(
                f"Document {filename!r} is not valid UTF-8 text."
            ) from exc

    def _limit_text(self, text: str) -> tuple[str, bool]:
        """Limit extracted text to the configured character count."""
        if len(text) <= self.max_extracted_text_characters:
            return text, False

        return (
            text[: self.max_extracted_text_characters],
            True,
        )

    def _validate_document(
        self,
        *,
        document: bytes,
        filename: str,
        content_type: str,
    ) -> str:
        """Validate document type and file signature before extraction."""
        if not isinstance(document, bytes):
            raise DocumentProcessingError(
                "Document content must be supplied as bytes."
            )

        if not document:
            raise DocumentProcessingError(
                "Document content cannot be empty."
            )

        normalized_content_type = self._normalize_content_type(
            content_type
        )

        if normalized_content_type == LEGACY_WORD_CONTENT_TYPE:
            raise UnsupportedDocumentFormatError(
                "Legacy .doc files are accepted during ingestion, but "
                "text extraction is not supported by the configured "
                "dependencies. Convert the document to .docx or add a "
                "dedicated legacy Word extraction dependency."
            )

        if normalized_content_type not in SUPPORTED_CONTENT_TYPES:
            raise UnsupportedDocumentFormatError(
                f"No content extractor is configured for "
                f"{normalized_content_type!r}."
            )

        self.validator.validate_file_signature(
            filename=filename,
            content_type=normalized_content_type,
            file_header=document[:8192],
        )

        return normalized_content_type

    def _extract_pdf(self, document: bytes) -> dict[str, Any]:
        """Extract text and page information from a PDF document."""
        try:
            reader = PdfReader(io.BytesIO(document), strict=True)

            if reader.is_encrypted:
                raise DocumentProcessingError(
                    "Encrypted PDF documents are not supported."
                )

            page_text: list[str] = []
            page_count = len(reader.pages)

            for page_number, page in enumerate(reader.pages, start=1):
                try:
                    extracted_text = page.extract_text() or ""
                except Exception as exc:
                    raise DocumentProcessingError(
                        f"Failed to extract text from PDF page "
                        f"{page_number}."
                    ) from exc

                page_text.append(extracted_text)

            complete_text = "\n".join(page_text)
            extracted_text, truncated = self._limit_text(complete_text)

            metadata = reader.metadata or {}

            return {
                "extracted_text": extracted_text,
                "page_count": page_count,
                "metadata": {
                    "title": metadata.title,
                    "author": metadata.author,
                    "subject": metadata.subject,
                    "creator": metadata.creator,
                    "producer": metadata.producer,
                },
                "extraction": {
                    "format": "pdf",
                    "text_truncated": truncated,
                    "extracted_text_characters": len(extracted_text),
                },
            }

        except DocumentProcessingError:
            raise
        except Exception as exc:
            raise DocumentProcessingError(
                "Failed to parse PDF document."
            ) from exc

    def _extract_docx(self, document: bytes) -> dict[str, Any]:
        """Extract paragraphs and table content from a DOCX document."""
        try:
            docx_file = io.BytesIO(document)

            if not zipfile.is_zipfile(docx_file):
                raise DocumentProcessingError(
                    "DOCX document is not a valid ZIP-based Office file."
                )

            docx_file.seek(0)
            word_document = Document(docx_file)

            text_parts: list[str] = []

            for paragraph in word_document.paragraphs:
                if paragraph.text:
                    text_parts.append(paragraph.text)

            table_count = 0
            row_count = 0

            for table in word_document.tables:
                table_count += 1

                for row in table.rows:
                    row_count += 1
                    cells = [
                        cell.text.strip()
                        for cell in row.cells
                    ]
                    text_parts.append("\t".join(cells))

            complete_text = "\n".join(text_parts)
            extracted_text, truncated = self._limit_text(complete_text)

            core_properties = word_document.core_properties

            return {
                "extracted_text": extracted_text,
                "paragraph_count": len(word_document.paragraphs),
                "table_count": table_count,
                "table_row_count": row_count,
                "metadata": {
                    "title": core_properties.title,
                    "subject": core_properties.subject,
                    "author": core_properties.author,
                    "keywords": core_properties.keywords,
                    "category": core_properties.category,
                },
                "extraction": {
                    "format": "docx",
                    "text_truncated": truncated,
                    "extracted_text_characters": len(extracted_text),
                },
            }

        except DocumentProcessingError:
            raise
        except Exception as exc:
            raise DocumentProcessingError(
                "Failed to parse DOCX document."
            ) from exc

    def _extract_xlsx(self, document: bytes) -> dict[str, Any]:
        """Extract worksheet data and structural information from XLSX."""
        workbook = None

        try:
            workbook = load_workbook(
                filename=io.BytesIO(document),
                read_only=True,
                data_only=True,
            )

            worksheets: list[dict[str, Any]] = []
            text_parts: list[str] = []
            total_rows = 0
            total_non_empty_cells = 0
            truncated = False

            for worksheet in workbook.worksheets:
                worksheet_rows = 0
                worksheet_non_empty_cells = 0
                worksheet_text_parts: list[str] = []

                for row_number, row in enumerate(
                    worksheet.iter_rows(
                        max_row=self.max_worksheet_rows,
                        max_col=self.max_worksheet_columns,
                        values_only=True,
                    ),
                    start=1,
                ):
                    worksheet_rows += 1
                    total_rows += 1

                    values = [
                        self._format_cell_value(value)
                        for value in row
                    ]

                    non_empty_values = [
                        value for value in values if value != ""
                    ]

                    worksheet_non_empty_cells += len(non_empty_values)
                    total_non_empty_cells += len(non_empty_values)

                    if non_empty_values:
                        worksheet_text_parts.append(
                            "\t".join(values)
                        )

                worksheet_text = "\n".join(worksheet_text_parts)
                worksheets.append(
                    {
                        "name": worksheet.title,
                        "row_count": worksheet_rows,
                        "non_empty_cell_count": (
                            worksheet_non_empty_cells
                        ),
                        "text": worksheet_text,
                    }
                )

                text_parts.append(
                    f"Worksheet: {worksheet.title}\n{worksheet_text}"
                )

            complete_text = "\n\n".join(text_parts)
            extracted_text, truncated = self._limit_text(complete_text)

            for worksheet in worksheets:
                worksheet.pop("text", None)

            return {
                "extracted_text": extracted_text,
                "worksheet_count": len(worksheets),
                "worksheets": worksheets,
                "row_count": total_rows,
                "non_empty_cell_count": total_non_empty_cells,
                "extraction": {
                    "format": "xlsx",
                    "text_truncated": truncated,
                    "extracted_text_characters": len(extracted_text),
                    "worksheet_row_limit": (
                        self.max_worksheet_rows
                    ),
                    "worksheet_column_limit": (
                        self.max_worksheet_columns
                    ),
                },
            }

        except DocumentProcessingError:
            raise
        except Exception as exc:
            raise DocumentProcessingError(
                "Failed to parse XLSX document."
            ) from exc
        finally:
            if workbook is not None:
                workbook.close()

    @staticmethod
    def _format_cell_value(value: Any) -> str:
        """Convert a spreadsheet cell value into readable text."""
        if value is None:
            return ""

        if isinstance(value, bool):
            return str(value)

        return str(value).replace("\r", " ").replace("\n", " ")

    def _extract_text_file(
        self,
        document: bytes,
        *,
        filename: str,
    ) -> dict[str, Any]:
        """Extract text from a UTF-8 plain-text document."""
        extracted_text = self._decode_text(
            document,
            filename=filename,
        )

        extracted_text, truncated = self._limit_text(extracted_text)

        return {
            "extracted_text": extracted_text,
            "character_count": len(extracted_text),
            "line_count": (
                len(extracted_text.splitlines())
                if extracted_text
                else 0
            ),
            "extraction": {
                "format": "txt",
                "text_truncated": truncated,
                "extracted_text_characters": len(extracted_text),
            },
        }

    def _extract_csv(
        self,
        document: bytes,
        *,
        filename: str,
    ) -> dict[str, Any]:
        """Extract CSV headers, row counts, and a bounded text preview."""
        decoded_content = self._decode_text(
            document,
            filename=filename,
        )

        text_stream = io.StringIO(
            decoded_content,
            newline="",
        )

        try:
            sample = decoded_content[:8192]

            try:
                dialect = csv.Sniffer().sniff(sample)
            except csv.Error:
                dialect = csv.excel

            reader = csv.reader(
                text_stream,
                dialect=dialect,
                strict=True,
            )

            headers: list[str] = []
            row_count = 0
            preview_rows: list[list[str]] = []
            preview_text_parts: list[str] = []
            preview_truncated = False

            for row in reader:
                if row_count == 0:
                    headers = row

                row_count += 1

                if row_count > self.max_csv_rows:
                    raise DocumentProcessingError(
                        f"CSV document exceeds the configured limit "
                        f"of {self.max_csv_rows} rows."
                    )

                if len(preview_rows) < 100:
                    preview_rows.append(row)
                    preview_text_parts.append("\t".join(row))

            complete_text = "\n".join(preview_text_parts)
            extracted_text, text_truncated = self._limit_text(
                complete_text
            )

            if row_count > len(preview_rows):
                preview_truncated = True

            return {
                "extracted_text": extracted_text,
                "headers": headers,
                "row_count": max(row_count - 1, 0),
                "column_count": len(headers),
                "preview_rows": preview_rows,
                "extraction": {
                    "format": "csv",
                    "preview_truncated": (
                        preview_truncated or text_truncated
                    ),
                    "extracted_text_characters": len(extracted_text),
                    "maximum_rows": self.max_csv_rows,
                },
            }

        except DocumentProcessingError:
            raise
        except (csv.Error, UnicodeError) as exc:
            raise DocumentProcessingError(
                "Failed to parse CSV document."
            ) from exc

    def process_document(
        self,
        *,
        document: bytes,
        metadata: Mapping[str, Any],
        filename: str,
        content_type: str,
    ) -> dict[str, Any]:
        """Validate and extract content from an uploaded document.

        Args:
            document: Complete document content as bytes.
            metadata: Metadata extracted during the ingestion stage.
            filename: Original document filename.
            content_type: Declared MIME content type.

        Returns:
            A JSON-serializable dictionary containing extracted content,
            document statistics, and processing metadata.

        Raises:
            DocumentProcessingError: If extraction or processing fails.
            DocumentValidationError: If document validation fails.
            UnsupportedDocumentFormatError: If no extractor is available.
        """
        if not isinstance(filename, str) or not filename.strip():
            raise DocumentProcessingError(
                "Document filename must be a non-empty string."
            )

        normalized_metadata = self._validate_metadata(metadata)

        normalized_content_type = self._validate_document(
            document=document,
            filename=filename,
            content_type=content_type,
        )

        extractors = {
            PDF_CONTENT_TYPE: self._extract_pdf,
            WORD_CONTENT_TYPE: self._extract_docx,
            EXCEL_CONTENT_TYPE: self._extract_xlsx,
            TEXT_CONTENT_TYPE: lambda content: self._extract_text_file(
                content,
                filename=filename,
            ),
            CSV_CONTENT_TYPE: lambda content: self._extract_csv(
                content,
                filename=filename,
            ),
        }

        extractor = extractors.get(normalized_content_type)

        if extractor is None:
            raise UnsupportedDocumentFormatError(
                f"No extractor is configured for "
                f"{normalized_content_type!r}."
            )

        try:
            extraction_result = extractor(document)
        except (
            DocumentProcessingError,
            DocumentValidationError,
        ):
            raise
        except Exception as exc:
            logger.exception(
                "Unexpected document extraction failure.",
                extra={
                    "filename": filename,
                    "content_type": normalized_content_type,
                },
            )
            raise DocumentProcessingError(
                f"Failed to process document {filename!r}."
            ) from exc

        result = {
            "filename": filename,
            "content_type": normalized_content_type,
            "size_bytes": len(document),
            "source_metadata": normalized_metadata,
            **extraction_result,
        }

        logger.info(
            "Document content extraction completed.",
            extra={
                "filename": filename,
                "content_type": normalized_content_type,
                "size_bytes": len(document),
                "extracted_text_characters": len(
                    result.get("extracted_text", "")
                ),
            },
        )

        return result