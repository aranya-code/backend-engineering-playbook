"""CLI entry point for the MongoDB data import and processing pipeline."""

from __future__ import annotations

import argparse
import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from config.settings import IMPORT_BATCH_SIZE, LOG_LEVEL, PROCESS_BATCH_SIZE
from database.connection import get_database, ping_database
from pipeline.load import load_documents_in_batches
from pipeline.transform import transform_documents
from pipeline.validate import validate_document
from processors.csv_processor import iter_csv_rows
from processors.json_processor import iter_json_objects


logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    """Configure application-wide logging."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def _iter_source_documents(
    input_path: Path,
    input_format: str,
) -> Iterator[dict[str, Any]]:
    """Yield documents from the configured source format."""
    if input_format == "json":
        yield from iter_json_objects(input_path)
        return

    if input_format == "csv":
        yield from iter_csv_rows(input_path)
        return

    raise ValueError(f"unsupported input format: {input_format}")


def _iter_validated_batches(
    documents: Iterator[dict[str, Any]],
    batch_size: int,
) -> Iterator[list[dict[str, Any]]]:
    """Transform and validate source documents in bounded batches."""
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    batch: list[dict[str, Any]] = []

    for transformed in transform_documents(documents):
        result = validate_document(transformed)

        if not result.valid:
            logger.warning(
                "Skipping invalid document: %s",
                ", ".join(result.errors),
            )
            continue

        batch.append(transformed)

        if len(batch) >= batch_size:
            yield batch
            batch = []

    if batch:
        yield batch


def process_import(
    input_path: Path,
    input_format: str,
    collection_name: str,
) -> int:
    """Import, transform, validate, and load source documents.

    The pipeline streams source records and writes them in bounded MongoDB
    bulk-write operations. Invalid records are logged and excluded from the
    destination collection rather than terminating the complete import.

    Args:
        input_path: Source JSON or CSV file.
        input_format: Source format.
        collection_name: MongoDB destination collection.

    Returns:
        Number of successfully inserted documents.
    """
    ping_database()

    database = get_database()
    collection = database[collection_name]

    source_documents = _iter_source_documents(
        input_path,
        input_format,
    )

    inserted_count = 0

    for batch in _iter_validated_batches(
        source_documents,
        PROCESS_BATCH_SIZE,
    ):
        inserted_count += load_documents_in_batches(
            collection,
            batch,
            batch_size=IMPORT_BATCH_SIZE,
            ordered=False,
        )

        logger.info(
            "Processed batch: inserted=%d total_inserted=%d",
            len(batch),
            inserted_count,
        )

    return inserted_count


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Import CSV or JSON data into MongoDB.",
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Path to the source CSV or JSON file.",
    )

    parser.add_argument(
        "--format",
        choices=("csv", "json"),
        required=True,
        dest="input_format",
        help="Input document format.",
    )

    parser.add_argument(
        "--collection",
        required=True,
        help="MongoDB destination collection.",
    )

    return parser


def main() -> int:
    """Run the MongoDB data import pipeline."""
    _configure_logging()

    parser = build_parser()
    args = parser.parse_args()

    try:
        inserted_count = process_import(
            input_path=args.input,
            input_format=args.input_format,
            collection_name=args.collection,
        )
    except Exception:
        logger.exception("MongoDB data import failed")
        return 1

    logger.info(
        "MongoDB data import completed successfully: inserted=%d",
        inserted_count,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""CLI entry point for the MongoDB data import and processing pipeline."""

from __future__ import annotations

import argparse
import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from config.settings import IMPORT_BATCH_SIZE, LOG_LEVEL, PROCESS_BATCH_SIZE
from database.connection import get_database, ping_database
from pipeline.load import load_documents_in_batches
from pipeline.transform import transform_documents
from pipeline.validate import validate_document
from processors.csv_processor import iter_csv_rows
from processors.json_processor import iter_json_objects


logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    """Configure application-wide logging."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def _iter_source_documents(
    input_path: Path,
    input_format: str,
) -> Iterator[dict[str, Any]]:
    """Yield documents from the configured source format."""
    if input_format == "json":
        yield from iter_json_objects(input_path)
        return

    if input_format == "csv":
        yield from iter_csv_rows(input_path)
        return

    raise ValueError(f"unsupported input format: {input_format}")


def _iter_validated_batches(
    documents: Iterator[dict[str, Any]],
    batch_size: int,
) -> Iterator[list[dict[str, Any]]]:
    """Transform and validate source documents in bounded batches."""
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    batch: list[dict[str, Any]] = []

    for transformed in transform_documents(documents):
        result = validate_document(transformed)

        if not result.valid:
            logger.warning(
                "Skipping invalid document: %s",
                ", ".join(result.errors),
            )
            continue

        batch.append(transformed)

        if len(batch) >= batch_size:
            yield batch
            batch = []

    if batch:
        yield batch


def process_import(
    input_path: Path,
    input_format: str,
    collection_name: str,
) -> int:
    """Import, transform, validate, and load source documents.

    The pipeline streams source records and writes them in bounded MongoDB
    bulk-write operations. Invalid records are logged and excluded from the
    destination collection rather than terminating the complete import.

    Args:
        input_path: Source JSON or CSV file.
        input_format: Source format.
        collection_name: MongoDB destination collection.

    Returns:
        Number of successfully inserted documents.
    """
    ping_database()

    database = get_database()
    collection = database[collection_name]

    source_documents = _iter_source_documents(
        input_path,
        input_format,
    )

    inserted_count = 0

    for batch in _iter_validated_batches(
        source_documents,
        PROCESS_BATCH_SIZE,
    ):
        inserted_count += load_documents_in_batches(
            collection,
            batch,
            batch_size=IMPORT_BATCH_SIZE,
            ordered=False,
        )

        logger.info(
            "Processed batch: inserted=%d total_inserted=%d",
            len(batch),
            inserted_count,
        )

    return inserted_count


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Import CSV or JSON data into MongoDB.",
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Path to the source CSV or JSON file.",
    )

    parser.add_argument(
        "--format",
        choices=("csv", "json"),
        required=True,
        dest="input_format",
        help="Input document format.",
    )

    parser.add_argument(
        "--collection",
        required=True,
        help="MongoDB destination collection.",
    )

    return parser


def main() -> int:
    """Run the MongoDB data import pipeline."""
    _configure_logging()

    parser = build_parser()
    args = parser.parse_args()

    try:
        inserted_count = process_import(
            input_path=args.input,
            input_format=args.input_format,
            collection_name=args.collection,
        )
    except Exception:
        logger.exception("MongoDB data import failed")
        return 1

    logger.info(
        "MongoDB data import completed successfully: inserted=%d",
        inserted_count,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())