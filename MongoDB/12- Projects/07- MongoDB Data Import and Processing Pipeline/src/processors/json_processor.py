"""JSON document processing utilities for the MongoDB data import pipeline."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any


class JSONProcessingError(ValueError):
    """Raised when a JSON input cannot be processed."""


def read_json_file(path: str | Path) -> list[dict[str, Any]]:
    """Read a JSON array from a file.

    The input file must contain a top-level JSON array where every element
    is an object. The complete file is loaded into memory, so this function
    is intended for bounded input files rather than very large datasets.

    Args:
        path: Path to the JSON file.

    Returns:
        A list of JSON objects.

    Raises:
        JSONProcessingError: If the file does not contain the expected shape.
        OSError: If the file cannot be read.
    """
    file_path = Path(path)

    try:
        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise JSONProcessingError(
            f"invalid JSON in {file_path}: {exc.msg}"
        ) from exc

    if not isinstance(data, list):
        raise JSONProcessingError(
            f"expected a top-level JSON array in {file_path}"
        )

    if not all(isinstance(item, dict) for item in data):
        raise JSONProcessingError(
            f"every item in {file_path} must be a JSON object"
        )

    return data


def iter_json_objects(path: str | Path) -> Iterator[dict[str, Any]]:
    """Yield objects from a JSON array one at a time.

    Standard-library ``json.load`` still parses the complete JSON document,
    so this function does not provide true streaming for very large files.
    It provides a lazy interface over an already parsed JSON array and keeps
    downstream processing decoupled from the file representation.
    """
    yield from read_json_file(path)


def write_json_file(
    path: str | Path,
    documents: list[dict[str, Any]],
    *,
    indent: int = 2,
) -> None:
    """Write processed documents as a JSON array.

    Args:
        path: Destination JSON file.
        documents: Documents to serialize.
        indent: JSON indentation level.

    Raises:
        OSError: If the destination cannot be written.
        TypeError: If a document contains a value unsupported by JSON.
    """
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(
            documents,
            file,
            indent=indent,
            ensure_ascii=False,
            default=str,
        )
        file.write("\n")

"""JSON document processing utilities for the MongoDB data import pipeline."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any


class JSONProcessingError(ValueError):
    """Raised when a JSON input cannot be processed."""


def read_json_file(path: str | Path) -> list[dict[str, Any]]:
    """Read a JSON array from a file.

    The input file must contain a top-level JSON array where every element
    is an object. The complete file is loaded into memory, so this function
    is intended for bounded input files rather than very large datasets.

    Args:
        path: Path to the JSON file.

    Returns:
        A list of JSON objects.

    Raises:
        JSONProcessingError: If the file does not contain the expected shape.
        OSError: If the file cannot be read.
    """
    file_path = Path(path)

    try:
        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise JSONProcessingError(
            f"invalid JSON in {file_path}: {exc.msg}"
        ) from exc

    if not isinstance(data, list):
        raise JSONProcessingError(
            f"expected a top-level JSON array in {file_path}"
        )

    if not all(isinstance(item, dict) for item in data):
        raise JSONProcessingError(
            f"every item in {file_path} must be a JSON object"
        )

    return data


def iter_json_objects(path: str | Path) -> Iterator[dict[str, Any]]:
    """Yield objects from a JSON array one at a time.

    Standard-library ``json.load`` still parses the complete JSON document,
    so this function does not provide true streaming for very large files.
    It provides a lazy interface over an already parsed JSON array and keeps
    downstream processing decoupled from the file representation.
    """
    yield from read_json_file(path)


def write_json_file(
    path: str | Path,
    documents: list[dict[str, Any]],
    *,
    indent: int = 2,
) -> None:
    """Write processed documents as a JSON array.

    Args:
        path: Destination JSON file.
        documents: Documents to serialize.
        indent: JSON indentation level.

    Raises:
        OSError: If the destination cannot be written.
        TypeError: If a document contains a value unsupported by JSON.
    """
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(
            documents,
            file,
            indent=indent,
            ensure_ascii=False,
            default=str,
        )
        file.write("\n")