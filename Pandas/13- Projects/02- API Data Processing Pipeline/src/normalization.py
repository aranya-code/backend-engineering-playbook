from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

import pandas as pd


class NormalizationError(ValueError):
    """Raised when API records cannot be normalized safely."""


DEFAULT_TIMESTAMP_COLUMNS = (
    "created_at",
    "updated_at",
    "timestamp",
)

DEFAULT_IDENTIFIER_COLUMNS = (
    "id",
    "order_id",
    "customer_id",
    "product_id",
)


@dataclass(frozen=True, slots=True)
class NormalizationResult:
    """Represent normalized records and records that could not be normalized."""

    normalized: pd.DataFrame
    rejected: pd.DataFrame


def _ensure_records(
    records: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Convert API record mappings into independent dictionaries."""
    normalized_records: list[dict[str, Any]] = []

    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise NormalizationError(
                f"Record at index {index} must be a mapping."
            )

        normalized_records.append(dict(record))

    return normalized_records


def records_to_dataframe(
    records: Iterable[Mapping[str, Any]],
) -> pd.DataFrame:
    """Convert API records into a DataFrame without mutating the source data."""
    normalized_records = _ensure_records(records)

    if not normalized_records:
        return pd.DataFrame()

    try:
        frame = pd.DataFrame.from_records(
            normalized_records,
        )
    except (TypeError, ValueError) as exc:
        raise NormalizationError(
            "Failed to convert API records into a DataFrame."
        ) from exc

    return frame.reset_index(drop=True)


def normalize_column_names(
    frame: pd.DataFrame,
    *,
    lowercase: bool = True,
    separator: str = "_",
) -> pd.DataFrame:
    """Normalize column names into stable API-to-warehouse identifiers."""
    if not isinstance(frame, pd.DataFrame):
        raise NormalizationError(
            "frame must be a pandas DataFrame."
        )

    if not separator:
        raise ValueError("separator cannot be empty.")

    result = frame.copy()

    normalized_columns: list[str] = []

    for column in result.columns:
        name = str(column).strip()

        if lowercase:
            name = name.lower()

        name = "".join(
            separator if not character.isalnum() else character
            for character in name
        )

        parts = [
            part
            for part in name.split(separator)
            if part
        ]

        normalized_name = separator.join(parts)

        if not normalized_name:
            normalized_name = "unnamed"

        normalized_columns.append(normalized_name)

    if len(set(normalized_columns)) != len(normalized_columns):
        raise NormalizationError(
            "Column normalization produced duplicate column names."
        )

    result.columns = normalized_columns
    return result


def normalize_identifier_columns(
    frame: pd.DataFrame,
    *,
    columns: Iterable[str] = DEFAULT_IDENTIFIER_COLUMNS,
) -> pd.DataFrame:
    """Normalize identifier columns to nullable Pandas string values."""
    if not isinstance(frame, pd.DataFrame):
        raise NormalizationError(
            "frame must be a pandas DataFrame."
        )

    result = frame.copy()

    for column in columns:
        if column not in result.columns:
            continue

        result[column] = (
            result[column]
            .astype("string")
            .str.strip()
        )

    return result


def normalize_timestamps(
    frame: pd.DataFrame,
    *,
    columns: Iterable[str] = DEFAULT_TIMESTAMP_COLUMNS,
    timezone: str = "UTC",
) -> pd.DataFrame:
    """Convert configured timestamp columns to timezone-aware datetimes."""
    if not isinstance(frame, pd.DataFrame):
        raise NormalizationError(
            "frame must be a pandas DataFrame."
        )

    if not timezone:
        raise ValueError("timezone cannot be empty.")

    result = frame.copy()

    for column in columns:
        if column not in result.columns:
            continue

        try:
            result[column] = pd.to_datetime(
                result[column],
                errors="coerce",
                utc=True,
            )
            result[column] = result[column].dt.tz_convert(
                timezone,
            )
        except (TypeError, ValueError) as exc:
            raise NormalizationError(
                f"Failed to normalize timestamp column: {column}"
            ) from exc

    return result


def normalize_numeric_columns(
    frame: pd.DataFrame,
    *,
    columns: Iterable[str],
) -> pd.DataFrame:
    """Convert configured numeric columns using coercive parsing."""
    if not isinstance(frame, pd.DataFrame):
        raise NormalizationError(
            "frame must be a pandas DataFrame."
        )

    result = frame.copy()

    for column in columns:
        if column not in result.columns:
            continue

        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        )

    return result


def strip_string_columns(
    frame: pd.DataFrame,
    *,
    columns: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Trim leading and trailing whitespace from string-like columns."""
    if not isinstance(frame, pd.DataFrame):
        raise NormalizationError(
            "frame must be a pandas DataFrame."
        )

    result = frame.copy()

    selected_columns = (
        list(columns)
        if columns is not None
        else list(result.select_dtypes(include=["object", "string"]).columns)
    )

    for column in selected_columns:
        if column not in result.columns:
            continue

        if pd.api.types.is_string_dtype(result[column]):
            result[column] = result[column].astype("string").str.strip()

    return result


def drop_fully_empty_rows(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Remove records where every field is missing."""
    if not isinstance(frame, pd.DataFrame):
        raise NormalizationError(
            "frame must be a pandas DataFrame."
        )

    return frame.dropna(
        how="all",
    ).reset_index(drop=True)


def reject_records_with_missing_columns(
    frame: pd.DataFrame,
    *,
    required_columns: Iterable[str],
) -> NormalizationResult:
    """Split records based on required-column completeness."""
    if not isinstance(frame, pd.DataFrame):
        raise NormalizationError(
            "frame must be a pandas DataFrame."
        )

    required = tuple(required_columns)

    if not required:
        raise ValueError(
            "required_columns must contain at least one column."
        )

    missing_columns = [
        column
        for column in required
        if column not in frame.columns
    ]

    if missing_columns:
        raise NormalizationError(
            "Missing required columns: "
            + ", ".join(missing_columns)
        )

    invalid_mask = frame[list(required)].isna().any(axis=1)

    rejected = frame.loc[invalid_mask].copy()
    normalized = frame.loc[~invalid_mask].copy()

    return NormalizationResult(
        normalized=normalized.reset_index(drop=True),
        rejected=rejected.reset_index(drop=True),
    )


def normalize_api_records(
    records: Iterable[Mapping[str, Any]],
    *,
    required_columns: Iterable[str] = (),
    identifier_columns: Iterable[str] = DEFAULT_IDENTIFIER_COLUMNS,
    timestamp_columns: Iterable[str] = DEFAULT_TIMESTAMP_COLUMNS,
    numeric_columns: Iterable[str] = (),
    timezone: str = "UTC",
    drop_empty_rows: bool = True,
) -> NormalizationResult:
    """Normalize raw API records into a stable DataFrame representation."""
    frame = records_to_dataframe(records)

    if frame.empty:
        return NormalizationResult(
            normalized=frame,
            rejected=pd.DataFrame(),
        )

    frame = normalize_column_names(
        frame,
    )
    frame = strip_string_columns(
        frame,
    )
    frame = normalize_identifier_columns(
        frame,
        columns=identifier_columns,
    )
    frame = normalize_timestamps(
        frame,
        columns=timestamp_columns,
        timezone=timezone,
    )
    frame = normalize_numeric_columns(
        frame,
        columns=numeric_columns,
    )

    if drop_empty_rows:
        frame = drop_fully_empty_rows(
            frame,
        )

    if required_columns:
        return reject_records_with_missing_columns(
            frame,
            required_columns=required_columns,
        )

    return NormalizationResult(
        normalized=frame.reset_index(drop=True),
        rejected=pd.DataFrame(
            columns=frame.columns,
        ),
    )


__all__ = [
    "DEFAULT_IDENTIFIER_COLUMNS",
    "DEFAULT_TIMESTAMP_COLUMNS",
    "NormalizationError",
    "NormalizationResult",
    "drop_fully_empty_rows",
    "normalize_api_records",
    "normalize_column_names",
    "normalize_identifier_columns",
    "normalize_numeric_columns",
    "normalize_timestamps",
    "records_to_dataframe",
    "reject_records_with_missing_columns",
    "strip_string_columns",
]

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

import pandas as pd


class NormalizationError(ValueError):
    """Raised when API records cannot be normalized safely."""


DEFAULT_TIMESTAMP_COLUMNS = (
    "created_at",
    "updated_at",
    "timestamp",
)

DEFAULT_IDENTIFIER_COLUMNS = (
    "id",
    "order_id",
    "customer_id",
    "product_id",
)


@dataclass(frozen=True, slots=True)
class NormalizationResult:
    """Represent normalized records and records that could not be normalized."""

    normalized: pd.DataFrame
    rejected: pd.DataFrame


def _ensure_records(
    records: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Convert API record mappings into independent dictionaries."""
    normalized_records: list[dict[str, Any]] = []

    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise NormalizationError(
                f"Record at index {index} must be a mapping."
            )

        normalized_records.append(dict(record))

    return normalized_records


def records_to_dataframe(
    records: Iterable[Mapping[str, Any]],
) -> pd.DataFrame:
    """Convert API records into a DataFrame without mutating the source data."""
    normalized_records = _ensure_records(records)

    if not normalized_records:
        return pd.DataFrame()

    try:
        frame = pd.DataFrame.from_records(
            normalized_records,
        )
    except (TypeError, ValueError) as exc:
        raise NormalizationError(
            "Failed to convert API records into a DataFrame."
        ) from exc

    return frame.reset_index(drop=True)


def normalize_column_names(
    frame: pd.DataFrame,
    *,
    lowercase: bool = True,
    separator: str = "_",
) -> pd.DataFrame:
    """Normalize column names into stable API-to-warehouse identifiers."""
    if not isinstance(frame, pd.DataFrame):
        raise NormalizationError(
            "frame must be a pandas DataFrame."
        )

    if not separator:
        raise ValueError("separator cannot be empty.")

    result = frame.copy()

    normalized_columns: list[str] = []

    for column in result.columns:
        name = str(column).strip()

        if lowercase:
            name = name.lower()

        name = "".join(
            separator if not character.isalnum() else character
            for character in name
        )

        parts = [
            part
            for part in name.split(separator)
            if part
        ]

        normalized_name = separator.join(parts)

        if not normalized_name:
            normalized_name = "unnamed"

        normalized_columns.append(normalized_name)

    if len(set(normalized_columns)) != len(normalized_columns):
        raise NormalizationError(
            "Column normalization produced duplicate column names."
        )

    result.columns = normalized_columns
    return result


def normalize_identifier_columns(
    frame: pd.DataFrame,
    *,
    columns: Iterable[str] = DEFAULT_IDENTIFIER_COLUMNS,
) -> pd.DataFrame:
    """Normalize identifier columns to nullable Pandas string values."""
    if not isinstance(frame, pd.DataFrame):
        raise NormalizationError(
            "frame must be a pandas DataFrame."
        )

    result = frame.copy()

    for column in columns:
        if column not in result.columns:
            continue

        result[column] = (
            result[column]
            .astype("string")
            .str.strip()
        )

    return result


def normalize_timestamps(
    frame: pd.DataFrame,
    *,
    columns: Iterable[str] = DEFAULT_TIMESTAMP_COLUMNS,
    timezone: str = "UTC",
) -> pd.DataFrame:
    """Convert configured timestamp columns to timezone-aware datetimes."""
    if not isinstance(frame, pd.DataFrame):
        raise NormalizationError(
            "frame must be a pandas DataFrame."
        )

    if not timezone:
        raise ValueError("timezone cannot be empty.")

    result = frame.copy()

    for column in columns:
        if column not in result.columns:
            continue

        try:
            result[column] = pd.to_datetime(
                result[column],
                errors="coerce",
                utc=True,
            )
            result[column] = result[column].dt.tz_convert(
                timezone,
            )
        except (TypeError, ValueError) as exc:
            raise NormalizationError(
                f"Failed to normalize timestamp column: {column}"
            ) from exc

    return result


def normalize_numeric_columns(
    frame: pd.DataFrame,
    *,
    columns: Iterable[str],
) -> pd.DataFrame:
    """Convert configured numeric columns using coercive parsing."""
    if not isinstance(frame, pd.DataFrame):
        raise NormalizationError(
            "frame must be a pandas DataFrame."
        )

    result = frame.copy()

    for column in columns:
        if column not in result.columns:
            continue

        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        )

    return result


def strip_string_columns(
    frame: pd.DataFrame,
    *,
    columns: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Trim leading and trailing whitespace from string-like columns."""
    if not isinstance(frame, pd.DataFrame):
        raise NormalizationError(
            "frame must be a pandas DataFrame."
        )

    result = frame.copy()

    selected_columns = (
        list(columns)
        if columns is not None
        else list(result.select_dtypes(include=["object", "string"]).columns)
    )

    for column in selected_columns:
        if column not in result.columns:
            continue

        if pd.api.types.is_string_dtype(result[column]):
            result[column] = result[column].astype("string").str.strip()

    return result


def drop_fully_empty_rows(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Remove records where every field is missing."""
    if not isinstance(frame, pd.DataFrame):
        raise NormalizationError(
            "frame must be a pandas DataFrame."
        )

    return frame.dropna(
        how="all",
    ).reset_index(drop=True)


def reject_records_with_missing_columns(
    frame: pd.DataFrame,
    *,
    required_columns: Iterable[str],
) -> NormalizationResult:
    """Split records based on required-column completeness."""
    if not isinstance(frame, pd.DataFrame):
        raise NormalizationError(
            "frame must be a pandas DataFrame."
        )

    required = tuple(required_columns)

    if not required:
        raise ValueError(
            "required_columns must contain at least one column."
        )

    missing_columns = [
        column
        for column in required
        if column not in frame.columns
    ]

    if missing_columns:
        raise NormalizationError(
            "Missing required columns: "
            + ", ".join(missing_columns)
        )

    invalid_mask = frame[list(required)].isna().any(axis=1)

    rejected = frame.loc[invalid_mask].copy()
    normalized = frame.loc[~invalid_mask].copy()

    return NormalizationResult(
        normalized=normalized.reset_index(drop=True),
        rejected=rejected.reset_index(drop=True),
    )


def normalize_api_records(
    records: Iterable[Mapping[str, Any]],
    *,
    required_columns: Iterable[str] = (),
    identifier_columns: Iterable[str] = DEFAULT_IDENTIFIER_COLUMNS,
    timestamp_columns: Iterable[str] = DEFAULT_TIMESTAMP_COLUMNS,
    numeric_columns: Iterable[str] = (),
    timezone: str = "UTC",
    drop_empty_rows: bool = True,
) -> NormalizationResult:
    """Normalize raw API records into a stable DataFrame representation."""
    frame = records_to_dataframe(records)

    if frame.empty:
        return NormalizationResult(
            normalized=frame,
            rejected=pd.DataFrame(),
        )

    frame = normalize_column_names(
        frame,
    )
    frame = strip_string_columns(
        frame,
    )
    frame = normalize_identifier_columns(
        frame,
        columns=identifier_columns,
    )
    frame = normalize_timestamps(
        frame,
        columns=timestamp_columns,
        timezone=timezone,
    )
    frame = normalize_numeric_columns(
        frame,
        columns=numeric_columns,
    )

    if drop_empty_rows:
        frame = drop_fully_empty_rows(
            frame,
        )

    if required_columns:
        return reject_records_with_missing_columns(
            frame,
            required_columns=required_columns,
        )

    return NormalizationResult(
        normalized=frame.reset_index(drop=True),
        rejected=pd.DataFrame(
            columns=frame.columns,
        ),
    )


__all__ = [
    "DEFAULT_IDENTIFIER_COLUMNS",
    "DEFAULT_TIMESTAMP_COLUMNS",
    "NormalizationError",
    "NormalizationResult",
    "drop_fully_empty_rows",
    "normalize_api_records",
    "normalize_column_names",
    "normalize_identifier_columns",
    "normalize_numeric_columns",
    "normalize_timestamps",
    "records_to_dataframe",
    "reject_records_with_missing_columns",
    "strip_string_columns",
]