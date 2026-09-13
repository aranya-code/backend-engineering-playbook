"""Core record-processing logic for the concurrent data processor."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Any, TypeAlias


Record: TypeAlias = Mapping[str, Any]
Processor: TypeAlias = Callable[[Record], Record]


class ProcessingError(RuntimeError):
    """Raised when a record cannot be processed."""


@dataclass(frozen=True, slots=True)
class ProcessingResult:
    """Represent the outcome of processing a collection of records."""

    processed: int
    failed: int
    records: list[Record]


def process_record(
    record: Record,
    transform: Processor,
) -> Record:
    """Validate and transform a single input record."""
    if not isinstance(record, Mapping):
        raise ProcessingError("Each input record must be a mapping.")

    try:
        result = transform(record)
    except Exception as exc:
        raise ProcessingError("Record transformation failed.") from exc

    if not isinstance(result, Mapping):
        raise ProcessingError("Record processor must return a mapping.")

    return dict(result)


def process_records(
    records: Iterable[Record],
    transform: Processor,
    *,
    fail_fast: bool = True,
) -> ProcessingResult:
    """Process records sequentially while preserving input order."""
    processed_records: list[Record] = []
    failed = 0

    for record in records:
        try:
            processed_records.append(process_record(record, transform))
        except ProcessingError:
            failed += 1

            if fail_fast:
                raise

    return ProcessingResult(
        processed=len(processed_records),
        failed=failed,
        records=processed_records,
    )


def default_transform(record: Record) -> Record:
    """Apply the default normalization used by the processor."""
    normalized: dict[str, Any] = {}

    for key, value in record.items():
        if not isinstance(key, str):
            raise ProcessingError("Record keys must be strings.")

        normalized[key.strip()] = value

    return normalized

"""Core record-processing logic for the concurrent data processor."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Any, TypeAlias


Record: TypeAlias = Mapping[str, Any]
Processor: TypeAlias = Callable[[Record], Record]


class ProcessingError(RuntimeError):
    """Raised when a record cannot be processed."""


@dataclass(frozen=True, slots=True)
class ProcessingResult:
    """Represent the outcome of processing a collection of records."""

    processed: int
    failed: int
    records: list[Record]


def process_record(
    record: Record,
    transform: Processor,
) -> Record:
    """Validate and transform a single input record."""
    if not isinstance(record, Mapping):
        raise ProcessingError("Each input record must be a mapping.")

    try:
        result = transform(record)
    except Exception as exc:
        raise ProcessingError("Record transformation failed.") from exc

    if not isinstance(result, Mapping):
        raise ProcessingError("Record processor must return a mapping.")

    return dict(result)


def process_records(
    records: Iterable[Record],
    transform: Processor,
    *,
    fail_fast: bool = True,
) -> ProcessingResult:
    """Process records sequentially while preserving input order."""
    processed_records: list[Record] = []
    failed = 0

    for record in records:
        try:
            processed_records.append(process_record(record, transform))
        except ProcessingError:
            failed += 1

            if fail_fast:
                raise

    return ProcessingResult(
        processed=len(processed_records),
        failed=failed,
        records=processed_records,
    )


def default_transform(record: Record) -> Record:
    """Apply the default normalization used by the processor."""
    normalized: dict[str, Any] = {}

    for key, value in record.items():
        if not isinstance(key, str):
            raise ProcessingError("Record keys must be strings.")

        normalized[key.strip()] = value

    return normalized