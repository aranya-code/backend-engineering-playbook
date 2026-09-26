"""CSV document processing utilities for the MongoDB data import pipeline."""

from __future__ import annotations

import csv
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any


class CSVProcessingError(ValueError):
    """Raised when CSV input cannot be processed."""


def _normalize_row(row: Mapping[str | None, str | None]) -> dict[str, Any]:
    """Convert a CSV row into a MongoDB-ready document.

    Empty field names are rejected because MongoDB field names must be valid
    application-level schema fields. CSV values remain strings because
    automatic type inference can silently corrupt identifiers, leading zeros,
    dates, and business-specific values.
    """
    document: dict[str, Any] = {}

    for key, value in row.items():
        if key is None or not key.strip():
            raise CSVProcessingError("CSV contains an empty column name")

        document[key.strip()] = value.strip() if value is not None else None

    return document


def read_csv_file(
    path: str | Path,
    *,
    delimiter: str = ",",
    encoding: str = "utf-8",
) -> list[dict[str, Any]]:
    """Read a CSV file into MongoDB-compatible documents.

    The complete file is loaded into memory. Use ``iter_csv_rows`` when
    processing large imports through bounded batches.

    Args:
        path: Path to the CSV file.
        delimiter: CSV field delimiter.
        encoding: File encoding.

    Returns:
        A list of normalized documents.

    Raises:
        CSVProcessingError: If the CSV structure is invalid.
        OSError: If the file cannot be read.
    """
    return list(
        iter_csv_rows(
            path,
            delimiter=delimiter,
            encoding=encoding,
        )
    )


def iter_csv_rows(
    path: str | Path,
    *,
    delimiter: str = ",",
    encoding: str = "utf-8",
) -> Iterator[dict[str, Any]]:
    """Yield CSV rows as MongoDB-ready documents.

    Rows are processed incrementally, avoiding an application-level list
    containing the entire input file. This is the preferred interface for
    large ETL and MongoDB import workloads.

    Args:
        path: Path to the CSV file.
        delimiter: CSV field delimiter.
        encoding: File encoding.

    Yields:
        Normalized CSV rows.

    Raises:
        CSVProcessingError: If the CSV has no header or invalid structure.
        OSError: If the file cannot be read.
    """
    if len(delimiter) != 1:
        raise CSVProcessingError("delimiter must contain exactly one character")

    file_path = Path(path)

    with file_path.open(
        "r",
        encoding=encoding,
        newline="",
    ) as file:
        reader = csv.DictReader(
            file,
            delimiter=delimiter,
        )

        if not reader.fieldnames:
            raise CSVProcessingError(
                f"CSV file {file_path} does not contain a header"
            )

        fieldnames = [
            field.strip()
            for field in reader.fieldnames
            if field is not None
        ]

        if len(fieldnames) != len(set(fieldnames)):
            raise CSVProcessingError(
                f"CSV file {file_path} contains duplicate column names"
            )

        if any(not field for field in fieldnames):
            raise CSVProcessingError(
                f"CSV file {file_path} contains an empty column name"
            )

        reader.fieldnames = fieldnames

        for row_number, row in enumerate(reader, start=2):
            if None in row and row[None]:
                raise CSVProcessingError(
                    f"CSV row {row_number} contains more fields than the header"
                )

            yield _normalize_row(row)


def write_csv_file(
    path: str | Path,
    documents: list[Mapping[str, Any]],
    *,
    fieldnames: list[str] | None = None,
    delimiter: str = ",",
    encoding: str = "utf-8",
) -> None:
    """Write MongoDB documents to a CSV file.

    CSV is a flat format, so nested MongoDB values should be serialized by
    the caller when their representation needs to be preserved. This
    function converts scalar values to their string representation.

    Args:
        path: Destination CSV file.
        documents: Documents to serialize.
        fieldnames: Optional explicit column order. When omitted, fields are
            collected from the supplied documents in encounter order.
        delimiter: CSV field delimiter.
        encoding: File encoding.

    Raises:
        CSVProcessingError: If documents are empty or fieldnames are invalid.
        OSError: If the destination cannot be written.
    """
    if len(delimiter) != 1:
        raise CSVProcessingError("delimiter must contain exactly one character")

    if not documents:
        raise CSVProcessingError("documents must contain at least one document")

    if fieldnames is None:
        discovered_fields: dict[str, None] = {}

        for document in documents:
            for field in document:
                discovered_fields.setdefault(field, None)

        fieldnames = list(discovered_fields)

    if not fieldnames or any(not field.strip() for field in fieldnames):
        raise CSVProcessingError(
            "fieldnames must contain at least one non-empty field"
        )

    if len(fieldnames) != len(set(fieldnames)):
        raise CSVProcessingError("fieldnames must not contain duplicates")

    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open(
        "w",
        encoding=encoding,
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            delimiter=delimiter,
            extrasaction="ignore",
        )
        writer.writeheader()

        for document in documents:
            writer.writerow(
                {
                    field: document.get(field)
                    for field in fieldnames
                }
            )

"""CSV document processing utilities for the MongoDB data import pipeline."""

from __future__ import annotations

import csv
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any


class CSVProcessingError(ValueError):
    """Raised when CSV input cannot be processed."""


def _normalize_row(row: Mapping[str | None, str | None]) -> dict[str, Any]:
    """Convert a CSV row into a MongoDB-ready document.

    Empty field names are rejected because MongoDB field names must be valid
    application-level schema fields. CSV values remain strings because
    automatic type inference can silently corrupt identifiers, leading zeros,
    dates, and business-specific values.
    """
    document: dict[str, Any] = {}

    for key, value in row.items():
        if key is None or not key.strip():
            raise CSVProcessingError("CSV contains an empty column name")

        document[key.strip()] = value.strip() if value is not None else None

    return document


def read_csv_file(
    path: str | Path,
    *,
    delimiter: str = ",",
    encoding: str = "utf-8",
) -> list[dict[str, Any]]:
    """Read a CSV file into MongoDB-compatible documents.

    The complete file is loaded into memory. Use ``iter_csv_rows`` when
    processing large imports through bounded batches.

    Args:
        path: Path to the CSV file.
        delimiter: CSV field delimiter.
        encoding: File encoding.

    Returns:
        A list of normalized documents.

    Raises:
        CSVProcessingError: If the CSV structure is invalid.
        OSError: If the file cannot be read.
    """
    return list(
        iter_csv_rows(
            path,
            delimiter=delimiter,
            encoding=encoding,
        )
    )


def iter_csv_rows(
    path: str | Path,
    *,
    delimiter: str = ",",
    encoding: str = "utf-8",
) -> Iterator[dict[str, Any]]:
    """Yield CSV rows as MongoDB-ready documents.

    Rows are processed incrementally, avoiding an application-level list
    containing the entire input file. This is the preferred interface for
    large ETL and MongoDB import workloads.

    Args:
        path: Path to the CSV file.
        delimiter: CSV field delimiter.
        encoding: File encoding.

    Yields:
        Normalized CSV rows.

    Raises:
        CSVProcessingError: If the CSV has no header or invalid structure.
        OSError: If the file cannot be read.
    """
    if len(delimiter) != 1:
        raise CSVProcessingError("delimiter must contain exactly one character")

    file_path = Path(path)

    with file_path.open(
        "r",
        encoding=encoding,
        newline="",
    ) as file:
        reader = csv.DictReader(
            file,
            delimiter=delimiter,
        )

        if not reader.fieldnames:
            raise CSVProcessingError(
                f"CSV file {file_path} does not contain a header"
            )

        fieldnames = [
            field.strip()
            for field in reader.fieldnames
            if field is not None
        ]

        if len(fieldnames) != len(set(fieldnames)):
            raise CSVProcessingError(
                f"CSV file {file_path} contains duplicate column names"
            )

        if any(not field for field in fieldnames):
            raise CSVProcessingError(
                f"CSV file {file_path} contains an empty column name"
            )

        reader.fieldnames = fieldnames

        for row_number, row in enumerate(reader, start=2):
            if None in row and row[None]:
                raise CSVProcessingError(
                    f"CSV row {row_number} contains more fields than the header"
                )

            yield _normalize_row(row)


def write_csv_file(
    path: str | Path,
    documents: list[Mapping[str, Any]],
    *,
    fieldnames: list[str] | None = None,
    delimiter: str = ",",
    encoding: str = "utf-8",
) -> None:
    """Write MongoDB documents to a CSV file.

    CSV is a flat format, so nested MongoDB values should be serialized by
    the caller when their representation needs to be preserved. This
    function converts scalar values to their string representation.

    Args:
        path: Destination CSV file.
        documents: Documents to serialize.
        fieldnames: Optional explicit column order. When omitted, fields are
            collected from the supplied documents in encounter order.
        delimiter: CSV field delimiter.
        encoding: File encoding.

    Raises:
        CSVProcessingError: If documents are empty or fieldnames are invalid.
        OSError: If the destination cannot be written.
    """
    if len(delimiter) != 1:
        raise CSVProcessingError("delimiter must contain exactly one character")

    if not documents:
        raise CSVProcessingError("documents must contain at least one document")

    if fieldnames is None:
        discovered_fields: dict[str, None] = {}

        for document in documents:
            for field in document:
                discovered_fields.setdefault(field, None)

        fieldnames = list(discovered_fields)

    if not fieldnames or any(not field.strip() for field in fieldnames):
        raise CSVProcessingError(
            "fieldnames must contain at least one non-empty field"
        )

    if len(fieldnames) != len(set(fieldnames)):
        raise CSVProcessingError("fieldnames must not contain duplicates")

    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open(
        "w",
        encoding=encoding,
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            delimiter=delimiter,
            extrasaction="ignore",
        )
        writer.writeheader()

        for document in documents:
            writer.writerow(
                {
                    field: document.get(field)
                    for field in fieldnames
                }
            )