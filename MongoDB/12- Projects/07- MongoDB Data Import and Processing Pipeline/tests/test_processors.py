"""Tests for CSV and JSON processors in the MongoDB import pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from processors.csv_processor import (
    CSVProcessingError,
    iter_csv_rows,
    read_csv_file,
    write_csv_file,
)
from processors.json_processor import (
    JSONProcessingError,
    iter_json_objects,
    read_json_file,
    write_json_file,
)


def test_read_json_file_returns_documents(tmp_path: Path) -> None:
    """JSON arrays are loaded as dictionaries."""
    source = tmp_path / "documents.json"
    source.write_text(
        json.dumps(
            [
                {"name": "Alice", "email": "alice@example.com"},
                {"name": "Bob", "email": "bob@example.com"},
            ]
        ),
        encoding="utf-8",
    )

    documents = read_json_file(source)

    assert documents == [
        {"name": "Alice", "email": "alice@example.com"},
        {"name": "Bob", "email": "bob@example.com"},
    ]


def test_read_json_file_rejects_non_array(tmp_path: Path) -> None:
    """JSON documents must be represented by a top-level array."""
    source = tmp_path / "document.json"
    source.write_text(
        json.dumps({"name": "Alice"}),
        encoding="utf-8",
    )

    with pytest.raises(JSONProcessingError, match="top-level JSON array"):
        read_json_file(source)


def test_read_json_file_rejects_invalid_json(tmp_path: Path) -> None:
    """Malformed JSON should raise a processing-specific exception."""
    source = tmp_path / "invalid.json"
    source.write_text(
        '{"name": "Alice"',
        encoding="utf-8",
    )

    with pytest.raises(JSONProcessingError, match="invalid JSON"):
        read_json_file(source)


def test_iter_json_objects_yields_documents(tmp_path: Path) -> None:
    """The iterator exposes each JSON object independently."""
    source = tmp_path / "documents.json"
    source.write_text(
        json.dumps([{"id": 1}, {"id": 2}]),
        encoding="utf-8",
    )

    assert list(iter_json_objects(source)) == [
        {"id": 1},
        {"id": 2},
    ]


def test_write_json_file_creates_parent_directory(tmp_path: Path) -> None:
    """JSON output creates missing parent directories."""
    destination = tmp_path / "output" / "documents.json"
    documents = [{"id": 1}, {"id": 2}]

    write_json_file(destination, documents)

    assert json.loads(
        destination.read_text(encoding="utf-8")
    ) == documents


def test_read_csv_file_returns_normalized_documents(tmp_path: Path) -> None:
    """CSV headers and string values are normalized."""
    source = tmp_path / "documents.csv"
    source.write_text(
        " name , email \n Alice , alice@example.com \n",
        encoding="utf-8",
    )

    documents = read_csv_file(source)

    assert documents == [
        {
            "name": "Alice",
            "email": "alice@example.com",
        }
    ]


def test_iter_csv_rows_yields_rows_incrementally(tmp_path: Path) -> None:
    """CSV rows are available through the iterator interface."""
    source = tmp_path / "documents.csv"
    source.write_text(
        "id,name\n1,Alice\n2,Bob\n",
        encoding="utf-8",
    )

    assert list(iter_csv_rows(source)) == [
        {"id": "1", "name": "Alice"},
        {"id": "2", "name": "Bob"},
    ]


def test_read_csv_file_rejects_missing_header(tmp_path: Path) -> None:
    """CSV input must contain a usable header row."""
    source = tmp_path / "documents.csv"
    source.write_text("", encoding="utf-8")

    with pytest.raises(CSVProcessingError, match="header"):
        read_csv_file(source)


def test_read_csv_file_rejects_duplicate_columns(tmp_path: Path) -> None:
    """Duplicate column names are rejected to prevent data loss."""
    source = tmp_path / "documents.csv"
    source.write_text(
        "id,id\n1,2\n",
        encoding="utf-8",
    )

    with pytest.raises(CSVProcessingError, match="duplicate"):
        read_csv_file(source)


def test_write_csv_file_round_trip(tmp_path: Path) -> None:
    """CSV output can be read back without losing scalar values."""
    destination = tmp_path / "output" / "documents.csv"
    documents = [
        {"id": "1", "name": "Alice"},
        {"id": "2", "name": "Bob"},
    ]

    write_csv_file(
        destination,
        documents,
        fieldnames=["id", "name"],
    )

    assert read_csv_file(destination) == documents


def test_write_csv_file_rejects_empty_documents(tmp_path: Path) -> None:
    """CSV output requires at least one document."""
    destination = tmp_path / "documents.csv"

    with pytest.raises(
        CSVProcessingError,
        match="at least one document",
    ):
        write_csv_file(destination, [])

"""Tests for CSV and JSON processors in the MongoDB import pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from processors.csv_processor import (
    CSVProcessingError,
    iter_csv_rows,
    read_csv_file,
    write_csv_file,
)
from processors.json_processor import (
    JSONProcessingError,
    iter_json_objects,
    read_json_file,
    write_json_file,
)


def test_read_json_file_returns_documents(tmp_path: Path) -> None:
    """JSON arrays are loaded as dictionaries."""
    source = tmp_path / "documents.json"
    source.write_text(
        json.dumps(
            [
                {"name": "Alice", "email": "alice@example.com"},
                {"name": "Bob", "email": "bob@example.com"},
            ]
        ),
        encoding="utf-8",
    )

    documents = read_json_file(source)

    assert documents == [
        {"name": "Alice", "email": "alice@example.com"},
        {"name": "Bob", "email": "bob@example.com"},
    ]


def test_read_json_file_rejects_non_array(tmp_path: Path) -> None:
    """JSON documents must be represented by a top-level array."""
    source = tmp_path / "document.json"
    source.write_text(
        json.dumps({"name": "Alice"}),
        encoding="utf-8",
    )

    with pytest.raises(JSONProcessingError, match="top-level JSON array"):
        read_json_file(source)


def test_read_json_file_rejects_invalid_json(tmp_path: Path) -> None:
    """Malformed JSON should raise a processing-specific exception."""
    source = tmp_path / "invalid.json"
    source.write_text(
        '{"name": "Alice"',
        encoding="utf-8",
    )

    with pytest.raises(JSONProcessingError, match="invalid JSON"):
        read_json_file(source)


def test_iter_json_objects_yields_documents(tmp_path: Path) -> None:
    """The iterator exposes each JSON object independently."""
    source = tmp_path / "documents.json"
    source.write_text(
        json.dumps([{"id": 1}, {"id": 2}]),
        encoding="utf-8",
    )

    assert list(iter_json_objects(source)) == [
        {"id": 1},
        {"id": 2},
    ]


def test_write_json_file_creates_parent_directory(tmp_path: Path) -> None:
    """JSON output creates missing parent directories."""
    destination = tmp_path / "output" / "documents.json"
    documents = [{"id": 1}, {"id": 2}]

    write_json_file(destination, documents)

    assert json.loads(
        destination.read_text(encoding="utf-8")
    ) == documents


def test_read_csv_file_returns_normalized_documents(tmp_path: Path) -> None:
    """CSV headers and string values are normalized."""
    source = tmp_path / "documents.csv"
    source.write_text(
        " name , email \n Alice , alice@example.com \n",
        encoding="utf-8",
    )

    documents = read_csv_file(source)

    assert documents == [
        {
            "name": "Alice",
            "email": "alice@example.com",
        }
    ]


def test_iter_csv_rows_yields_rows_incrementally(tmp_path: Path) -> None:
    """CSV rows are available through the iterator interface."""
    source = tmp_path / "documents.csv"
    source.write_text(
        "id,name\n1,Alice\n2,Bob\n",
        encoding="utf-8",
    )

    assert list(iter_csv_rows(source)) == [
        {"id": "1", "name": "Alice"},
        {"id": "2", "name": "Bob"},
    ]


def test_read_csv_file_rejects_missing_header(tmp_path: Path) -> None:
    """CSV input must contain a usable header row."""
    source = tmp_path / "documents.csv"
    source.write_text("", encoding="utf-8")

    with pytest.raises(CSVProcessingError, match="header"):
        read_csv_file(source)


def test_read_csv_file_rejects_duplicate_columns(tmp_path: Path) -> None:
    """Duplicate column names are rejected to prevent data loss."""
    source = tmp_path / "documents.csv"
    source.write_text(
        "id,id\n1,2\n",
        encoding="utf-8",
    )

    with pytest.raises(CSVProcessingError, match="duplicate"):
        read_csv_file(source)


def test_write_csv_file_round_trip(tmp_path: Path) -> None:
    """CSV output can be read back without losing scalar values."""
    destination = tmp_path / "output" / "documents.csv"
    documents = [
        {"id": "1", "name": "Alice"},
        {"id": "2", "name": "Bob"},
    ]

    write_csv_file(
        destination,
        documents,
        fieldnames=["id", "name"],
    )

    assert read_csv_file(destination) == documents


def test_write_csv_file_rejects_empty_documents(tmp_path: Path) -> None:
    """CSV output requires at least one document."""
    destination = tmp_path / "documents.csv"

    with pytest.raises(
        CSVProcessingError,
        match="at least one document",
    ):
        write_csv_file(destination, [])