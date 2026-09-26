"""Load MongoDB seed data for query performance experiments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from pymongo import MongoClient
from pymongo.collection import Collection

from config.settings import MONGODB_DATABASE, MONGODB_URI

DEFAULT_BATCH_SIZE = 1_000


def load_json_documents(path: Path) -> list[dict[str, Any]]:
    """Load a JSON array containing MongoDB documents."""
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("The JSON file must contain an array of documents.")

    if not all(isinstance(document, dict) for document in data):
        raise ValueError("Every item in the JSON file must be a JSON object.")

    return data


def insert_batches(
    collection: Collection[dict[str, Any]],
    documents: Iterable[dict[str, Any]],
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> int:
    """Insert documents in bounded batches to avoid excessive memory usage."""
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    batch: list[dict[str, Any]] = []
    inserted = 0

    for document in documents:
        batch.append(document)

        if len(batch) >= batch_size:
            result = collection.insert_many(batch, ordered=False)
            inserted += len(result.inserted_ids)
            batch.clear()

    if batch:
        result = collection.insert_many(batch, ordered=False)
        inserted += len(result.inserted_ids)

    return inserted


def load_data(
    collection: Collection[dict[str, Any]],
    source: Path,
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    drop_existing: bool = False,
) -> int:
    """Load documents from a JSON file into the target collection."""
    if not source.exists():
        raise FileNotFoundError(f"Data file does not exist: {source}")

    if not source.is_file():
        raise ValueError(f"Data source is not a file: {source}")

    documents = load_json_documents(source)

    if drop_existing:
        collection.drop()

    return insert_batches(
        collection,
        documents,
        batch_size=batch_size,
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line options for loading seed data."""
    parser = argparse.ArgumentParser(
        description="Load MongoDB seed data from a JSON file.",
    )
    parser.add_argument(
        "source",
        type=Path,
        help="Path to a JSON file containing an array of MongoDB documents.",
    )
    parser.add_argument(
        "--collection",
        default="orders",
        help="Target MongoDB collection.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Number of documents inserted per batch.",
    )
    parser.add_argument(
        "--drop-existing",
        action="store_true",
        help="Drop the target collection before loading data.",
    )
    return parser.parse_args()


def main() -> None:
    """Load the configured seed dataset into MongoDB."""
    args = parse_args()

    client = MongoClient(MONGODB_URI)

    try:
        collection = client[MONGODB_DATABASE][args.collection]

        inserted = load_data(
            collection,
            args.source,
            batch_size=args.batch_size,
            drop_existing=args.drop_existing,
        )

        print(
            f"Loaded {inserted:,} documents into "
            f"'{MONGODB_DATABASE}.{args.collection}'."
        )
    finally:
        client.close()


if __name__ == "__main__":
    main()

"""Load MongoDB seed data for query performance experiments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from pymongo import MongoClient
from pymongo.collection import Collection

from config.settings import MONGODB_DATABASE, MONGODB_URI

DEFAULT_BATCH_SIZE = 1_000


def load_json_documents(path: Path) -> list[dict[str, Any]]:
    """Load a JSON array containing MongoDB documents."""
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("The JSON file must contain an array of documents.")

    if not all(isinstance(document, dict) for document in data):
        raise ValueError("Every item in the JSON file must be a JSON object.")

    return data


def insert_batches(
    collection: Collection[dict[str, Any]],
    documents: Iterable[dict[str, Any]],
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> int:
    """Insert documents in bounded batches to avoid excessive memory usage."""
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    batch: list[dict[str, Any]] = []
    inserted = 0

    for document in documents:
        batch.append(document)

        if len(batch) >= batch_size:
            result = collection.insert_many(batch, ordered=False)
            inserted += len(result.inserted_ids)
            batch.clear()

    if batch:
        result = collection.insert_many(batch, ordered=False)
        inserted += len(result.inserted_ids)

    return inserted


def load_data(
    collection: Collection[dict[str, Any]],
    source: Path,
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    drop_existing: bool = False,
) -> int:
    """Load documents from a JSON file into the target collection."""
    if not source.exists():
        raise FileNotFoundError(f"Data file does not exist: {source}")

    if not source.is_file():
        raise ValueError(f"Data source is not a file: {source}")

    documents = load_json_documents(source)

    if drop_existing:
        collection.drop()

    return insert_batches(
        collection,
        documents,
        batch_size=batch_size,
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line options for loading seed data."""
    parser = argparse.ArgumentParser(
        description="Load MongoDB seed data from a JSON file.",
    )
    parser.add_argument(
        "source",
        type=Path,
        help="Path to a JSON file containing an array of MongoDB documents.",
    )
    parser.add_argument(
        "--collection",
        default="orders",
        help="Target MongoDB collection.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Number of documents inserted per batch.",
    )
    parser.add_argument(
        "--drop-existing",
        action="store_true",
        help="Drop the target collection before loading data.",
    )
    return parser.parse_args()


def main() -> None:
    """Load the configured seed dataset into MongoDB."""
    args = parse_args()

    client = MongoClient(MONGODB_URI)

    try:
        collection = client[MONGODB_DATABASE][args.collection]

        inserted = load_data(
            collection,
            args.source,
            batch_size=args.batch_size,
            drop_existing=args.drop_existing,
        )

        print(
            f"Loaded {inserted:,} documents into "
            f"'{MONGODB_DATABASE}.{args.collection}'."
        )
    finally:
        client.close()


if __name__ == "__main__":
    main()