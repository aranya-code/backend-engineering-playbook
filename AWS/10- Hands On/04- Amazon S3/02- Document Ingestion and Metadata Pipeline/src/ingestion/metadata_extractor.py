"""Extract structured metadata from supported documents.

The extractor processes PDF, Microsoft Word, Excel, plain-text, and CSV
documents. It returns normalized metadata suitable for persistence in
DynamoDB and downstream document-processing workflows.

Extraction is performed in memory. The caller is responsible for enforcing
document size limits and validating file signatures before invoking this
module.
"""

from __future__ import annotations

import csv
import io
import logging
import re
from collections.abc import Callable
from typing import Any

from docx import Document
from openpyxl import load_workbook
from pypdf import PdfReader

logger = logging.getLogger(__name__)

MAX_EXTRACTED_TEXT_LENGTH = 100_000
MAX_METADATA_ITEMS = 100
MAX_METADATA_VALUE_LENGTH = 10_000
MAX_EXCEL_SHEETS = 50
MAX_EXCEL_ROWS = 100_000
MAX_EXCEL_COLUMNS = 500

PDF_CONTENT_TYPE = "application/pdf"
DOCX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)
XLSX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
DOC_CONTENT_TYPE = "application/msword"
TEXT_CONTENT_TYPE = "text/plain"
CSV_CONTENT_TYPE = "text/csv"


class MetadataExtractionError(RuntimeError):
    """Raised when document metadata extraction fails."""


class MetadataExtractor:
    """Extract normalized metadata from supported document formats."""

    def __init__(
        self,
        *,
        max_text_length: int = MAX_EXTRACTED_TEXT_LENGTH,
        max_metadata_items: int = MAX_METADATA_ITEMS,
    ) -> None:
        """Initialize the metadata extractor.

        Args:
            max_text_length: Maximum number of characters retained in
                extracted text.
            max_metadata_items: Maximum number of extracted metadata entries.

        Raises:
            ValueError: If either configured limit is invalid.
        """
        if max_text_length <= 0:
            raise ValueError("max_text_length must be greater than zero.")

        if max_metadata_items <= 0:
            raise ValueError("max_metadata_items must be greater than zero.")

        self.max_text_length = max_text_length
        self.max_metadata_items = max_metadata_items

        self._extractors: dict[str, Callable[[bytes], dict[str, Any]]] = {
            PDF_CONTENT_TYPE: self._extract_pdf_metadata,
            DOCX_CONTENT_TYPE: self._extract_docx_metadata,
            XLSX_CONTENT_TYPE: self._extract_xlsx_metadata,
            TEXT_CONTENT_TYPE: self._extract_text_metadata,
            CSV_CONTENT_TYPE: self._extract_csv_metadata,
        }

    @staticmethod
    def _validate_document(
        document: bytes,
        filename: str,
        content_type: str,
    ) -> tuple[bytes, str, str]:
        """Validate and normalize extraction inputs."""
        if not isinstance(document, bytes):
            raise MetadataExtractionError(
                "Document content must be supplied as bytes."
            )

        if not document:
            raise MetadataExtractionError(
                "Cannot extract metadata from an empty document."
            )

        if not isinstance(filename, str) or not filename.strip():
            raise MetadataExtractionError(
                "Document filename must be a non-empty string."
            )

        if not isinstance(content_type, str) or not content_type.strip():
            raise MetadataExtractionError(
                "Document content type must be a non-empty string."
            )

        normalized_filename = filename.strip()
        normalized_content_type = (
            content_type.split(";", maxsplit=1)[0].strip().lower()
        )

        return (
            document,
            normalized_filename,
            normalized_content_type,
        )

    @staticmethod
    def _normalize_text(value: str | None) -> str:
        """Normalize extracted text without changing its semantic content."""
        if not value:
            return ""

        normalized = value.replace("\x00", "")
        normalized = re.sub(r"[ \t]+", " ", normalized)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)

        return normalized.strip()

    def _truncate_text(self, value: str) -> str:
        """Limit extracted text to the configured character count."""
        if len(value) <= self.max_text_length:
            return value

        logger.warning(
            "Extracted document text exceeded configured limit.",
            extra={
                "configured_limit": self.max_text_length,
                "actual_length": len(value),
            },
        )

        return value[: self.max_text_length]

    def _normalize_metadata(
        self,
        metadata: dict[str, Any],
    ) -> dict[str, str | int | float | bool | None]:
        """Normalize metadata values for JSON and DynamoDB compatibility."""
        normalized: dict[str, str | int | float | bool | None] = {}

        for index, (key, value) in enumerate(metadata.items()):
            if index >= self.max_metadata_items:
                logger.warning(
                    "Metadata item limit reached; remaining entries omitted.",
                    extra={"max_metadata_items": self.max_metadata_items},
                )
                break

            if not isinstance(key, str) or not key.strip():
                continue

            normalized_key = key.strip()[:255]

            if isinstance(value, (str, int, float, bool)) or value is None:
                normalized_value = value
            else:
                normalized_value = str(value)

            if isinstance(normalized_value, str):
                normalized_value = normalized_value[
                    :MAX_METADATA_VALUE_LENGTH
                ]

            if isinstance(normalized_value, float):
                if normalized_value != normalized_value:
                    normalized_value = None
                elif normalized_value in (float("inf"), float("-inf")):
                    normalized_value = None

            normalized[normalized_key] = normalized_value

        return normalized

    def _extract_pdf_metadata(self, document: bytes) -> dict[str, Any]:
        """Extract metadata and text from a PDF document."""
        try:
            reader = PdfReader(io.BytesIO(document), strict=False)

            if reader.is_encrypted:
                raise MetadataExtractionError(
                    "Encrypted PDF documents are not supported."
                )

            page_count = len(reader.pages)
            extracted_pages: list[str] = []

            for page_number, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text() or ""
                except Exception as exc:
                    raise MetadataExtractionError(
                        f"Failed to extract text from PDF page "
                        f"{page_number + 1}."
                    ) from exc

                if page_text:
                    extracted_pages.append(page_text)

            metadata = reader.metadata or {}

            return {
                "document_type": "pdf",
                "page_count": page_count,
                "title": metadata.get("/Title"),
                "author": metadata.get("/Author"),
                "subject": metadata.get("/Subject"),
                "creator": metadata.get("/Creator"),
                "producer": metadata.get("/Producer"),
                "creation_date": str(metadata.get("/CreationDate") or ""),
                "modification_date": str(
                    metadata.get("/ModDate") or ""
                ),
                "extracted_text": self._normalize_text(
                    "\n\n".join(extracted_pages)
                ),
            }

        except MetadataExtractionError:
            raise
        except Exception as exc:
            raise MetadataExtractionError(
                "Failed to extract metadata from PDF document."
            ) from exc

    def _extract_docx_metadata(self, document: bytes) -> dict[str, Any]:
        """Extract metadata and text from a DOCX document."""
        try:
            word_document = Document(io.BytesIO(document))

            properties = word_document.core_properties

            paragraphs = [
                paragraph.text
                for paragraph in word_document.paragraphs
                if paragraph.text.strip()
            ]

            table_count = len(word_document.tables)

            for table in word_document.tables:
                for row in table.rows:
                    row_text = " | ".join(
                        cell.text.strip()
                        for cell in row.cells
                        if cell.text.strip()
                    )

                    if row_text:
                        paragraphs.append(row_text)

            extracted_text = self._normalize_text(
                "\n\n".join(paragraphs)
            )

            return {
                "document_type": "docx",
                "paragraph_count": len(word_document.paragraphs),
                "table_count": table_count,
                "title": properties.title or None,
                "author": properties.author or None,
                "subject": properties.subject or None,
                "keywords": properties.keywords or None,
                "category": properties.category or None,
                "created": (
                    properties.created.isoformat()
                    if properties.created
                    else None
                ),
                "modified": (
                    properties.modified.isoformat()
                    if properties.modified
                    else None
                ),
                "extracted_text": extracted_text,
            }

        except Exception as exc:
            raise MetadataExtractionError(
                "Failed to extract metadata from DOCX document."
            ) from exc

    def _extract_xlsx_metadata(self, document: bytes) -> dict[str, Any]:
        """Extract workbook properties and worksheet information."""
        workbook = None

        try:
            workbook = load_workbook(
                io.BytesIO(document),
                read_only=True,
                data_only=True,
            )

            properties = workbook.properties
            sheet_metadata: list[dict[str, Any]] = []
            extracted_rows: list[str] = []

            worksheets = workbook.worksheets[:MAX_EXCEL_SHEETS]

            for worksheet in worksheets:
                non_empty_rows = 0
                non_empty_cells = 0

                for row_index, row in enumerate(
                    worksheet.iter_rows(
                        max_row=MAX_EXCEL_ROWS,
                        max_col=MAX_EXCEL_COLUMNS,
                        values_only=True,
                    ),
                    start=1,
                ):
                    if not any(value is not None for value in row):
                        continue

                    non_empty_rows += 1

                    values = [
                        str(value).strip()
                        for value in row
                        if value is not None and str(value).strip()
                    ]

                    non_empty_cells += len(values)

                    if values:
                        extracted_rows.append(
                            f"[{worksheet.title}] "
                            + " | ".join(values)
                        )

                    if row_index >= MAX_EXCEL_ROWS:
                        logger.warning(
                            "Excel worksheet row limit reached.",
                            extra={
                                "worksheet": worksheet.title,
                                "max_rows": MAX_EXCEL_ROWS,
                            },
                        )
                        break

                sheet_metadata.append(
                    {
                        "name": worksheet.title,
                        "max_row": worksheet.max_row,
                        "max_column": worksheet.max_column,
                        "non_empty_rows": non_empty_rows,
                        "non_empty_cells": non_empty_cells,
                    }
                )

            return {
                "document_type": "xlsx",
                "sheet_count": len(workbook.sheetnames),
                "sheets": sheet_metadata,
                "title": properties.title or None,
                "creator": properties.creator or None,
                "subject": properties.subject or None,
                "description": properties.description or None,
                "created": (
                    properties.created.isoformat()
                    if properties.created
                    else None
                ),
                "modified": (
                    properties.modified.isoformat()
                    if properties.modified
                    else None
                ),
                "extracted_text": self._normalize_text(
                    "\n".join(extracted_rows)
                ),
            }

        except Exception as exc:
            if isinstance(exc, MetadataExtractionError):
                raise

            raise MetadataExtractionError(
                "Failed to extract metadata from XLSX document."
            ) from exc

        finally:
            if workbook is not None:
                workbook.close()

    def _extract_text_metadata(self, document: bytes) -> dict[str, Any]:
        """Extract metadata from a UTF-8 plain-text document."""
        try:
            extracted_text = document.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise MetadataExtractionError(
                "Plain-text document must use UTF-8 encoding."
            ) from exc

        normalized_text = self._normalize_text(extracted_text)

        return {
            "document_type": "text",
            "character_count": len(normalized_text),
            "line_count": len(normalized_text.splitlines()),
            "word_count": len(normalized_text.split()),
            "extracted_text": normalized_text,
        }

    def _extract_csv_metadata(self, document: bytes) -> dict[str, Any]:
        """Extract CSV structure, headers, and bounded row information."""
        try:
            csv_text = document.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise MetadataExtractionError(
                "CSV document must use UTF-8 encoding."
            ) from exc

        try:
            reader = csv.reader(io.StringIO(csv_text, newline=""))

            headers = next(reader, [])
            headers = [
                header.strip()
                for header in headers
            ]

            row_count = 0
            extracted_rows: list[str] = []

            for row in reader:
                if not any(value.strip() for value in row):
                    continue

                row_count += 1

                if len(extracted_rows) < MAX_EXCEL_ROWS:
                    extracted_rows.append(" | ".join(row))

            return {
                "document_type": "csv",
                "column_count": len(headers),
                "row_count": row_count,
                "headers": headers[: self.max_metadata_items],
                "extracted_text": self._normalize_text(
                    "\n".join(
                        [
                            " | ".join(headers),
                            *extracted_rows,
                        ]
                    )
                ),
            }

        except csv.Error as exc:
            raise MetadataExtractionError(
                "Failed to parse CSV document."
            ) from exc

    def extract_metadata(
        self,
        *,
        document: bytes,
        filename: str,
        content_type: str,
    ) -> dict[str, Any]:
        """Extract document metadata using its declared MIME content type.

        Args:
            document: Complete document content as bytes.
            filename: Original document filename.
            content_type: MIME content type returned by S3.

        Returns:
            A normalized dictionary containing document identity,
            document-specific metadata, and bounded extracted text.

        Raises:
            MetadataExtractionError: If the input is invalid, the format is
                unsupported, or document parsing fails.
        """
        (
            validated_document,
            normalized_filename,
            normalized_content_type,
        ) = self._validate_document(
            document=document,
            filename=filename,
            content_type=content_type,
        )

        extractor = self._extractors.get(normalized_content_type)

        if extractor is None:
            raise MetadataExtractionError(
                f"Unsupported document content type: "
                f"{normalized_content_type!r}."
            )

        logger.info(
            "Starting document metadata extraction.",
            extra={
                "filename": normalized_filename,
                "content_type": normalized_content_type,
                "size_bytes": len(validated_document),
            },
        )

        try:
            extracted_metadata = extractor(validated_document)

            extracted_metadata = self._normalize_metadata(
                extracted_metadata
            )

            extracted_text = extracted_metadata.get("extracted_text")

            if isinstance(extracted_text, str):
                extracted_metadata["extracted_text"] = (
                    self._truncate_text(extracted_text)
                )

            result: dict[str, Any] = {
                "filename": normalized_filename,
                "content_type": normalized_content_type,
                "size_bytes": len(validated_document),
                **extracted_metadata,
            }

            logger.info(
                "Document metadata extraction completed.",
                extra={
                    "filename": normalized_filename,
                    "content_type": normalized_content_type,
                    "metadata_fields": len(result),
                    "extracted_text_length": len(
                        result.get("extracted_text", "")
                    ),
                },
            )

            return result

        except MetadataExtractionError:
            logger.exception(
                "Document metadata extraction failed.",
                extra={
                    "filename": normalized_filename,
                    "content_type": normalized_content_type,
                },
            )
            raise
        except Exception as exc:
            logger.exception(
                "Unexpected document metadata extraction failure.",
                extra={
                    "filename": normalized_filename,
                    "content_type": normalized_content_type,
                },
            )
            raise MetadataExtractionError(
                f"Metadata extraction failed for {normalized_filename!r}."
            ) from exc