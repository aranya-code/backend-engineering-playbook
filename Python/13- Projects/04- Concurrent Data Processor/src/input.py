"""Input handling and streaming utilities for the concurrent data processor."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any


class InputError(ValueError):
    """Raised when an input source cannot be read or parsed."""


def iter_csv(
    path: str | Path,
    *,
    encoding: str = "utf-8",
) -> Iterator[dict[str, str]]:
    """Stream CSV records without loading the entire file into memory."""
    input_path = Path(path)

    if not input_path.is_file():
        raise InputError(f"Input file does not exist: {input_path}")

    try:
        with input_path.open("r", encoding=encoding, newline="") as file:
            reader = csv.DictReader(file)

            if reader.fieldnames is None:
                raise InputError(f"CSV file has no header row: {input_path}")

            for row in reader:
                yield dict(row)
    except OSError as exc:
        raise InputError(f"Unable to read CSV file: {input_path}") from exc
    except csv.Error as exc:
        raise InputError(f"Invalid CSV data: {input_path}") from exc


def iter_json_lines(
    path: str | Path,
    *,
    encoding: str = "utf-8",
) -> Iterator[Mapping[str, Any]]:
    """Stream newline-delimited JSON records from a file."""
    input_path = Path(path)

    if not input_path.is_file():
        raise InputError(f"Input file does not exist: {input_path}")

    try:
        with input_path.open("r", encoding=encoding) as file:
            for line_number, line in enumerate(file, start=1):
                content = line.strip()

                if not content:
                    continue

                try:
                    record = json.loads(content)
                except json.JSONDecodeError as exc:
                    raise InputError(
                        f"Invalid JSON on line {line_number} of {input_path}: "
                        f"{exc.msg}",
                    ) from exc

                if not isinstance(record, Mapping):
                    raise InputError(
                        f"Expected a JSON object on line {line_number} "
                        f"of {input_path}.",
                    )

                yield record
    except OSError as exc:
        raise InputError(f"Unable to read JSON Lines file: {input_path}") from exc


def iter_records(
    path: str | Path,
    *,
    encoding: str = "utf-8",
) -> Iterator[Mapping[str, Any]]:
    """Stream records from a supported input format based on file extension."""
    input_path = Path(path)
    suffix = input_path.suffix.lower()

    if suffix == ".csv":
        yield from iter_csv(input_path, encoding=encoding)
        return

    if suffix in {".jsonl", ".ndjson"}:
        yield from iter_json_lines(input_path, encoding=encoding)
        return

    raise InputError(
        f"Unsupported input format '{suffix or '<none>'}' for {input_path}. "
        "Supported formats are .csv, .jsonl, and .ndjson.",
    )

"""Input handling and streaming utilities for the concurrent data processor."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any


class InputError(ValueError):
    """Raised when an input source cannot be read or parsed."""


def iter_csv(
    path: str | Path,
    *,
    encoding: str = "utf-8",
) -> Iterator[dict[str, str]]:
    """Stream CSV records without loading the entire file into memory."""
    input_path = Path(path)

    if not input_path.is_file():
        raise InputError(f"Input file does not exist: {input_path}")

    try:
        with input_path.open("r", encoding=encoding, newline="") as file:
            reader = csv.DictReader(file)

            if reader.fieldnames is None:
                raise InputError(f"CSV file has no header row: {input_path}")

            for row in reader:
                yield dict(row)
    except OSError as exc:
        raise InputError(f"Unable to read CSV file: {input_path}") from exc
    except csv.Error as exc:
        raise InputError(f"Invalid CSV data: {input_path}") from exc


def iter_json_lines(
    path: str | Path,
    *,
    encoding: str = "utf-8",
) -> Iterator[Mapping[str, Any]]:
    """Stream newline-delimited JSON records from a file."""
    input_path = Path(path)

    if not input_path.is_file():
        raise InputError(f"Input file does not exist: {input_path}")

    try:
        with input_path.open("r", encoding=encoding) as file:
            for line_number, line in enumerate(file, start=1):
                content = line.strip()

                if not content:
                    continue

                try:
                    record = json.loads(content)
                except json.JSONDecodeError as exc:
                    raise InputError(
                        f"Invalid JSON on line {line_number} of {input_path}: "
                        f"{exc.msg}",
                    ) from exc

                if not isinstance(record, Mapping):
                    raise InputError(
                        f"Expected a JSON object on line {line_number} "
                        f"of {input_path}.",
                    )

                yield record
    except OSError as exc:
        raise InputError(f"Unable to read JSON Lines file: {input_path}") from exc


def iter_records(
    path: str | Path,
    *,
    encoding: str = "utf-8",
) -> Iterator[Mapping[str, Any]]:
    """Stream records from a supported input format based on file extension."""
    input_path = Path(path)
    suffix = input_path.suffix.lower()

    if suffix == ".csv":
        yield from iter_csv(input_path, encoding=encoding)
        return

    if suffix in {".jsonl", ".ndjson"}:
        yield from iter_json_lines(input_path, encoding=encoding)
        return

    raise InputError(
        f"Unsupported input format '{suffix or '<none>'}' for {input_path}. "
        "Supported formats are .csv, .jsonl, and .ndjson.",
    )