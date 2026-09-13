"""Output sinks for persisting processed records safely and efficiently."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

from src.processor import Record


class OutputWriter:
    """Write processed records to a durable output destination."""

    def __init__(self, output_path: Path) -> None:
        self._output_path = output_path

    @property
    def output_path(self) -> Path:
        """Return the configured output path."""
        return self._output_path

    def write_jsonl(self, records: Iterable[Record]) -> int:
        """Write records as newline-delimited JSON and return the record count."""
        self._output_path.parent.mkdir(parents=True, exist_ok=True)

        count = 0

        with self._output_path.open("w", encoding="utf-8") as file:
            for record in records:
                file.write(
                    json.dumps(
                        _record_to_mapping(record),
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
                )
                file.write("\n")
                count += 1

        return count

    def write_csv(
        self,
        records: Iterable[Record],
        *,
        fieldnames: tuple[str, ...],
    ) -> int:
        """Write records as CSV and return the record count."""
        self._output_path.parent.mkdir(parents=True, exist_ok=True)

        count = 0

        with self._output_path.open(
            "w",
            encoding="utf-8",
            newline="",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames,
                extrasaction="ignore",
            )
            writer.writeheader()

            for record in records:
                writer.writerow(_record_to_mapping(record))
                count += 1

        return count

    def write_stream(
        self,
        records: Iterable[Record],
        *,
        serializer: str = "jsonl",
    ) -> Iterator[str]:
        """Serialize records incrementally without buffering the full dataset."""
        if serializer != "jsonl":
            raise ValueError(f"Unsupported serializer: {serializer}")

        for record in records:
            yield json.dumps(
                _record_to_mapping(record),
                ensure_ascii=False,
                separators=(",", ":"),
            )


def _record_to_mapping(record: Record) -> dict[str, Any]:
    """Convert a supported record object into a serializable mapping."""
    if isinstance(record, dict):
        return record.copy()

    if hasattr(record, "__dataclass_fields__"):
        from dataclasses import asdict

        return asdict(record)

    if hasattr(record, "__dict__"):
        return vars(record).copy()

    raise TypeError(
        f"Unsupported record type: {type(record).__name__}. "
        "Expected a mapping, dataclass instance, or object with __dict__."
    )

"""Output sinks for persisting processed records safely and efficiently."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

from src.processor import Record


class OutputWriter:
    """Write processed records to a durable output destination."""

    def __init__(self, output_path: Path) -> None:
        self._output_path = output_path

    @property
    def output_path(self) -> Path:
        """Return the configured output path."""
        return self._output_path

    def write_jsonl(self, records: Iterable[Record]) -> int:
        """Write records as newline-delimited JSON and return the record count."""
        self._output_path.parent.mkdir(parents=True, exist_ok=True)

        count = 0

        with self._output_path.open("w", encoding="utf-8") as file:
            for record in records:
                file.write(
                    json.dumps(
                        _record_to_mapping(record),
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
                )
                file.write("\n")
                count += 1

        return count

    def write_csv(
        self,
        records: Iterable[Record],
        *,
        fieldnames: tuple[str, ...],
    ) -> int:
        """Write records as CSV and return the record count."""
        self._output_path.parent.mkdir(parents=True, exist_ok=True)

        count = 0

        with self._output_path.open(
            "w",
            encoding="utf-8",
            newline="",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames,
                extrasaction="ignore",
            )
            writer.writeheader()

            for record in records:
                writer.writerow(_record_to_mapping(record))
                count += 1

        return count

    def write_stream(
        self,
        records: Iterable[Record],
        *,
        serializer: str = "jsonl",
    ) -> Iterator[str]:
        """Serialize records incrementally without buffering the full dataset."""
        if serializer != "jsonl":
            raise ValueError(f"Unsupported serializer: {serializer}")

        for record in records:
            yield json.dumps(
                _record_to_mapping(record),
                ensure_ascii=False,
                separators=(",", ":"),
            )


def _record_to_mapping(record: Record) -> dict[str, Any]:
    """Convert a supported record object into a serializable mapping."""
    if isinstance(record, dict):
        return record.copy()

    if hasattr(record, "__dataclass_fields__"):
        from dataclasses import asdict

        return asdict(record)

    if hasattr(record, "__dict__"):
        return vars(record).copy()

    raise TypeError(
        f"Unsupported record type: {type(record).__name__}. "
        "Expected a mapping, dataclass instance, or object with __dict__."
    )