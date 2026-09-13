from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import pandas as pd


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """Represent one data-quality validation failure."""

    rule: str
    message: str
    row_count: int = 0


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Represent the outcome of a validation operation."""

    valid: bool
    issues: tuple[ValidationIssue, ...]

    @property
    def issue_count(self) -> int:
        """Return the number of validation issues."""
        return len(self.issues)

    def raise_if_invalid(self) -> None:
        """Raise ValueError when the validation result is invalid."""
        if self.valid:
            return

        details = "\n".join(
            f"- {issue.rule}: {issue.message}"
            for issue in self.issues
        )
        raise ValueError(
            "Validation failed:\n"
            f"{details}"
        )


class ValidationError(ValueError):
    """Raised when validation cannot be performed safely."""


def _validate_dataframe(frame: pd.DataFrame) -> None:
    """Validate that the input is a DataFrame."""
    if not isinstance(frame, pd.DataFrame):
        raise ValidationError(
            "frame must be a pandas DataFrame."
        )


def validate_required_columns(
    frame: pd.DataFrame,
    required_columns: Iterable[str],
) -> ValidationResult:
    """Validate that all required columns exist."""
    if not isinstance(frame, pd.DataFrame):
        return ValidationResult(
            valid=False,
            issues=(
                ValidationIssue(
                    rule="dataframe_type",
                    message="frame must be a pandas DataFrame.",
                ),
            ),
        )

    required = tuple(required_columns)

    missing = [
        column
        for column in required
        if column not in frame.columns
    ]

    if missing:
        return ValidationResult(
            valid=False,
            issues=(
                ValidationIssue(
                    rule="required_columns",
                    message=(
                        "Input DataFrame is missing required columns: "
                        + ", ".join(missing)
                    ),
                    row_count=len(frame),
                ),
            ),
        )

    return ValidationResult(
        valid=True,
        issues=(),
    )


def validate_not_empty(
    frame: pd.DataFrame,
) -> ValidationResult:
    """Validate that a dataset contains at least one record."""
    if not isinstance(frame, pd.DataFrame):
        return ValidationResult(
            valid=False,
            issues=(
                ValidationIssue(
                    rule="dataframe_type",
                    message="frame must be a pandas DataFrame.",
                ),
            ),
        )

    if frame.empty:
        return ValidationResult(
            valid=False,
            issues=(
                ValidationIssue(
                    rule="not_empty",
                    message="Input DataFrame must contain at least one row.",
                ),
            ),
        )

    return ValidationResult(
        valid=True,
        issues=(),
    )


def validate_required_values(
    frame: pd.DataFrame,
    required_columns: Iterable[str],
) -> ValidationResult:
    """Validate that required columns contain no missing values."""
    required = tuple(required_columns)

    schema_result = validate_required_columns(
        frame,
        required,
    )

    if not schema_result.valid:
        return schema_result

    null_mask = frame[list(required)].isna().any(axis=1)
    null_count = int(null_mask.sum())

    if null_count:
        return ValidationResult(
            valid=False,
            issues=(
                ValidationIssue(
                    rule="required_values",
                    message=(
                        "Required columns contain missing values."
                    ),
                    row_count=null_count,
                ),
            ),
        )

    return ValidationResult(
        valid=True,
        issues=(),
    )


def validate_unique_keys(
    frame: pd.DataFrame,
    key_columns: Iterable[str],
) -> ValidationResult:
    """Validate uniqueness of one or more business keys."""
    keys = tuple(key_columns)

    schema_result = validate_required_columns(
        frame,
        keys,
    )

    if not schema_result.valid:
        return schema_result

    if not keys:
        raise ValidationError(
            "At least one key column is required."
        )

    duplicate_mask = frame.duplicated(
        subset=list(keys),
        keep=False,
    )
    duplicate_count = int(duplicate_mask.sum())

    if duplicate_count:
        key_description = ", ".join(keys)

        return ValidationResult(
            valid=False,
            issues=(
                ValidationIssue(
                    rule="unique_keys",
                    message=(
                        f"Duplicate records found for key(s): "
                        f"{key_description}."
                    ),
                    row_count=duplicate_count,
                ),
            ),
        )

    return ValidationResult(
        valid=True,
        issues=(),
    )


def validate_numeric_columns(
    frame: pd.DataFrame,
    columns: Iterable[str],
) -> ValidationResult:
    """Validate that configured columns contain numeric values."""
    columns_tuple = tuple(columns)

    schema_result = validate_required_columns(
        frame,
        columns_tuple,
    )

    if not schema_result.valid:
        return schema_result

    issues: list[ValidationIssue] = []

    for column in columns_tuple:
        numeric = pd.to_numeric(
            frame[column],
            errors="coerce",
        )
        invalid_mask = frame[column].notna() & numeric.isna()
        invalid_count = int(invalid_mask.sum())

        if invalid_count:
            issues.append(
                ValidationIssue(
                    rule="numeric_dtype",
                    message=(
                        f"Column '{column}' contains non-numeric values."
                    ),
                    row_count=invalid_count,
                )
            )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def validate_non_negative_columns(
    frame: pd.DataFrame,
    columns: Iterable[str],
) -> ValidationResult:
    """Validate that configured numeric columns are non-negative."""
    columns_tuple = tuple(columns)

    schema_result = validate_required_columns(
        frame,
        columns_tuple,
    )

    if not schema_result.valid:
        return schema_result

    issues: list[ValidationIssue] = []

    for column in columns_tuple:
        numeric = pd.to_numeric(
            frame[column],
            errors="coerce",
        )

        negative_mask = numeric.lt(0)
        negative_count = int(negative_mask.sum())

        if negative_count:
            issues.append(
                ValidationIssue(
                    rule="non_negative",
                    message=(
                        f"Column '{column}' contains negative values."
                    ),
                    row_count=negative_count,
                )
            )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def validate_datetime_columns(
    frame: pd.DataFrame,
    columns: Iterable[str],
) -> ValidationResult:
    """Validate that configured columns contain parseable datetimes."""
    columns_tuple = tuple(columns)

    schema_result = validate_required_columns(
        frame,
        columns_tuple,
    )

    if not schema_result.valid:
        return schema_result

    issues: list[ValidationIssue] = []

    for column in columns_tuple:
        parsed = pd.to_datetime(
            frame[column],
            errors="coerce",
            utc=True,
        )

        invalid_mask = frame[column].notna() & parsed.isna()
        invalid_count = int(invalid_mask.sum())

        if invalid_count:
            issues.append(
                ValidationIssue(
                    rule="datetime_parseable",
                    message=(
                        f"Column '{column}' contains invalid timestamps."
                    ),
                    row_count=invalid_count,
                )
            )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def validate_timestamp_order(
    frame: pd.DataFrame,
    *,
    start_column: str,
    end_column: str,
) -> ValidationResult:
    """Validate that end timestamps are not earlier than start timestamps."""
    schema_result = validate_required_columns(
        frame,
        (
            start_column,
            end_column,
        ),
    )

    if not schema_result.valid:
        return schema_result

    start = pd.to_datetime(
        frame[start_column],
        errors="coerce",
        utc=True,
    )
    end = pd.to_datetime(
        frame[end_column],
        errors="coerce",
        utc=True,
    )

    invalid_mask = (
        start.notna()
        & end.notna()
        & end.lt(start)
    )
    invalid_count = int(invalid_mask.sum())

    if invalid_count:
        return ValidationResult(
            valid=False,
            issues=(
                ValidationIssue(
                    rule="timestamp_order",
                    message=(
                        f"'{end_column}' must be greater than or equal "
                        f"to '{start_column}'."
                    ),
                    row_count=invalid_count,
                ),
            ),
        )

    return ValidationResult(
        valid=True,
        issues=(),
    )


def validate_allowed_values(
    frame: pd.DataFrame,
    *,
    column: str,
    allowed_values: Iterable[Any],
) -> ValidationResult:
    """Validate that a column contains only configured values."""
    schema_result = validate_required_columns(
        frame,
        [column],
    )

    if not schema_result.valid:
        return schema_result

    allowed = set(allowed_values)
    invalid_mask = frame[column].notna() & ~frame[column].isin(allowed)
    invalid_count = int(invalid_mask.sum())

    if invalid_count:
        return ValidationResult(
            valid=False,
            issues=(
                ValidationIssue(
                    rule="allowed_values",
                    message=(
                        f"Column '{column}' contains unsupported values. "
                        f"Allowed values: {sorted(allowed)}."
                    ),
                    row_count=invalid_count,
                ),
            ),
        )

    return ValidationResult(
        valid=True,
        issues=(),
    )


def validate_foreign_key(
    frame: pd.DataFrame,
    *,
    key_column: str,
    reference: pd.DataFrame,
    reference_key: str | None = None,
) -> ValidationResult:
    """Validate that source keys exist in a reference DataFrame."""
    resolved_reference_key = reference_key or key_column

    source_schema = validate_required_columns(
        frame,
        [key_column],
    )
    if not source_schema.valid:
        return source_schema

    reference_schema = validate_required_columns(
        reference,
        [resolved_reference_key],
    )
    if not reference_schema.valid:
        return reference_schema

    reference_values = set(
        reference[resolved_reference_key].dropna()
    )

    missing_mask = (
        frame[key_column].notna()
        & ~frame[key_column].isin(reference_values)
    )
    missing_count = int(missing_mask.sum())

    if missing_count:
        missing_values = (
            frame.loc[missing_mask, key_column]
            .drop_duplicates()
            .astype("string")
            .tolist()
        )

        return ValidationResult(
            valid=False,
            issues=(
                ValidationIssue(
                    rule="foreign_key",
                    message=(
                        f"Column '{key_column}' contains references "
                        f"missing from '{resolved_reference_key}': "
                        f"{missing_values}"
                    ),
                    row_count=missing_count,
                ),
            ),
        )

    return ValidationResult(
        valid=True,
        issues=(),
    )


def validate_dataframe(
    frame: pd.DataFrame,
    *,
    required_columns: Iterable[str] = (),
    required_value_columns: Iterable[str] = (),
    unique_key_columns: Iterable[str] = (),
    numeric_columns: Iterable[str] = (),
    non_negative_columns: Iterable[str] = (),
    datetime_columns: Iterable[str] = (),
    allowed_values: Mapping[str, Iterable[Any]] | None = None,
) -> ValidationResult:
    """Run the standard validation suite for normalized API data."""
    _validate_dataframe(frame)

    results: list[ValidationResult] = [
        validate_required_columns(
            frame,
            required_columns,
        ),
        validate_required_values(
            frame,
            required_value_columns,
        )
        if tuple(required_value_columns)
        else ValidationResult(
            valid=True,
            issues=(),
        ),
        validate_unique_keys(
            frame,
            unique_key_columns,
        )
        if tuple(unique_key_columns)
        else ValidationResult(
            valid=True,
            issues=(),
        ),
        validate_numeric_columns(
            frame,
            numeric_columns,
        )
        if tuple(numeric_columns)
        else ValidationResult(
            valid=True,
            issues=(),
        ),
        validate_non_negative_columns(
            frame,
            non_negative_columns,
        )
        if tuple(non_negative_columns)
        else ValidationResult(
            valid=True,
            issues=(),
        ),
        validate_datetime_columns(
            frame,
            datetime_columns,
        )
        if tuple(datetime_columns)
        else ValidationResult(
            valid=True,
            issues=(),
        ),
    ]

    if allowed_values:
        results.extend(
            validate_allowed_values(
                frame,
                column=column,
                allowed_values=values,
            )
            for column, values in allowed_values.items()
        )

    issues = tuple(
        issue
        for result in results
        for issue in result.issues
    )

    return ValidationResult(
        valid=not issues,
        issues=issues,
    )


def validate_ingestion_result(
    frame: pd.DataFrame,
    *,
    required_columns: Iterable[str] = (),
) -> ValidationResult:
    """Validate the normalized dataset immediately after ingestion."""
    return validate_dataframe(
        frame,
        required_columns=required_columns,
    )


def validate_transformed_data(
    frame: pd.DataFrame,
    *,
    required_columns: Iterable[str] = (),
    numeric_columns: Iterable[str] = (),
    datetime_columns: Iterable[str] = (),
) -> ValidationResult:
    """Validate the dataset contract expected by downstream processing."""
    return validate_dataframe(
        frame,
        required_columns=required_columns,
        numeric_columns=numeric_columns,
        datetime_columns=datetime_columns,
    )


def assert_valid(result: ValidationResult) -> None:
    """Raise a validation exception when the result is invalid."""
    try:
        result.raise_if_invalid()
    except ValueError as exc:
        raise ValidationError(
            str(exc)
        ) from exc


__all__ = [
    "ValidationError",
    "ValidationIssue",
    "ValidationResult",
    "assert_valid",
    "validate_allowed_values",
    "validate_dataframe",
    "validate_datetime_columns",
    "validate_foreign_key",
    "validate_ingestion_result",
    "validate_non_negative_columns",
    "validate_numeric_columns",
    "validate_required_columns",
    "validate_required_values",
    "validate_timestamp_order",
    "validate_transformed_data",
    "validate_unique_keys",
]

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import pandas as pd


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """Represent one data-quality validation failure."""

    rule: str
    message: str
    row_count: int = 0


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Represent the outcome of a validation operation."""

    valid: bool
    issues: tuple[ValidationIssue, ...]

    @property
    def issue_count(self) -> int:
        """Return the number of validation issues."""
        return len(self.issues)

    def raise_if_invalid(self) -> None:
        """Raise ValueError when the validation result is invalid."""
        if self.valid:
            return

        details = "\n".join(
            f"- {issue.rule}: {issue.message}"
            for issue in self.issues
        )
        raise ValueError(
            "Validation failed:\n"
            f"{details}"
        )


class ValidationError(ValueError):
    """Raised when validation cannot be performed safely."""


def _validate_dataframe(frame: pd.DataFrame) -> None:
    """Validate that the input is a DataFrame."""
    if not isinstance(frame, pd.DataFrame):
        raise ValidationError(
            "frame must be a pandas DataFrame."
        )


def validate_required_columns(
    frame: pd.DataFrame,
    required_columns: Iterable[str],
) -> ValidationResult:
    """Validate that all required columns exist."""
    if not isinstance(frame, pd.DataFrame):
        return ValidationResult(
            valid=False,
            issues=(
                ValidationIssue(
                    rule="dataframe_type",
                    message="frame must be a pandas DataFrame.",
                ),
            ),
        )

    required = tuple(required_columns)

    missing = [
        column
        for column in required
        if column not in frame.columns
    ]

    if missing:
        return ValidationResult(
            valid=False,
            issues=(
                ValidationIssue(
                    rule="required_columns",
                    message=(
                        "Input DataFrame is missing required columns: "
                        + ", ".join(missing)
                    ),
                    row_count=len(frame),
                ),
            ),
        )

    return ValidationResult(
        valid=True,
        issues=(),
    )


def validate_not_empty(
    frame: pd.DataFrame,
) -> ValidationResult:
    """Validate that a dataset contains at least one record."""
    if not isinstance(frame, pd.DataFrame):
        return ValidationResult(
            valid=False,
            issues=(
                ValidationIssue(
                    rule="dataframe_type",
                    message="frame must be a pandas DataFrame.",
                ),
            ),
        )

    if frame.empty:
        return ValidationResult(
            valid=False,
            issues=(
                ValidationIssue(
                    rule="not_empty",
                    message="Input DataFrame must contain at least one row.",
                ),
            ),
        )

    return ValidationResult(
        valid=True,
        issues=(),
    )


def validate_required_values(
    frame: pd.DataFrame,
    required_columns: Iterable[str],
) -> ValidationResult:
    """Validate that required columns contain no missing values."""
    required = tuple(required_columns)

    schema_result = validate_required_columns(
        frame,
        required,
    )

    if not schema_result.valid:
        return schema_result

    null_mask = frame[list(required)].isna().any(axis=1)
    null_count = int(null_mask.sum())

    if null_count:
        return ValidationResult(
            valid=False,
            issues=(
                ValidationIssue(
                    rule="required_values",
                    message=(
                        "Required columns contain missing values."
                    ),
                    row_count=null_count,
                ),
            ),
        )

    return ValidationResult(
        valid=True,
        issues=(),
    )


def validate_unique_keys(
    frame: pd.DataFrame,
    key_columns: Iterable[str],
) -> ValidationResult:
    """Validate uniqueness of one or more business keys."""
    keys = tuple(key_columns)

    schema_result = validate_required_columns(
        frame,
        keys,
    )

    if not schema_result.valid:
        return schema_result

    if not keys:
        raise ValidationError(
            "At least one key column is required."
        )

    duplicate_mask = frame.duplicated(
        subset=list(keys),
        keep=False,
    )
    duplicate_count = int(duplicate_mask.sum())

    if duplicate_count:
        key_description = ", ".join(keys)

        return ValidationResult(
            valid=False,
            issues=(
                ValidationIssue(
                    rule="unique_keys",
                    message=(
                        f"Duplicate records found for key(s): "
                        f"{key_description}."
                    ),
                    row_count=duplicate_count,
                ),
            ),
        )

    return ValidationResult(
        valid=True,
        issues=(),
    )


def validate_numeric_columns(
    frame: pd.DataFrame,
    columns: Iterable[str],
) -> ValidationResult:
    """Validate that configured columns contain numeric values."""
    columns_tuple = tuple(columns)

    schema_result = validate_required_columns(
        frame,
        columns_tuple,
    )

    if not schema_result.valid:
        return schema_result

    issues: list[ValidationIssue] = []

    for column in columns_tuple:
        numeric = pd.to_numeric(
            frame[column],
            errors="coerce",
        )
        invalid_mask = frame[column].notna() & numeric.isna()
        invalid_count = int(invalid_mask.sum())

        if invalid_count:
            issues.append(
                ValidationIssue(
                    rule="numeric_dtype",
                    message=(
                        f"Column '{column}' contains non-numeric values."
                    ),
                    row_count=invalid_count,
                )
            )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def validate_non_negative_columns(
    frame: pd.DataFrame,
    columns: Iterable[str],
) -> ValidationResult:
    """Validate that configured numeric columns are non-negative."""
    columns_tuple = tuple(columns)

    schema_result = validate_required_columns(
        frame,
        columns_tuple,
    )

    if not schema_result.valid:
        return schema_result

    issues: list[ValidationIssue] = []

    for column in columns_tuple:
        numeric = pd.to_numeric(
            frame[column],
            errors="coerce",
        )

        negative_mask = numeric.lt(0)
        negative_count = int(negative_mask.sum())

        if negative_count:
            issues.append(
                ValidationIssue(
                    rule="non_negative",
                    message=(
                        f"Column '{column}' contains negative values."
                    ),
                    row_count=negative_count,
                )
            )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def validate_datetime_columns(
    frame: pd.DataFrame,
    columns: Iterable[str],
) -> ValidationResult:
    """Validate that configured columns contain parseable datetimes."""
    columns_tuple = tuple(columns)

    schema_result = validate_required_columns(
        frame,
        columns_tuple,
    )

    if not schema_result.valid:
        return schema_result

    issues: list[ValidationIssue] = []

    for column in columns_tuple:
        parsed = pd.to_datetime(
            frame[column],
            errors="coerce",
            utc=True,
        )

        invalid_mask = frame[column].notna() & parsed.isna()
        invalid_count = int(invalid_mask.sum())

        if invalid_count:
            issues.append(
                ValidationIssue(
                    rule="datetime_parseable",
                    message=(
                        f"Column '{column}' contains invalid timestamps."
                    ),
                    row_count=invalid_count,
                )
            )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def validate_timestamp_order(
    frame: pd.DataFrame,
    *,
    start_column: str,
    end_column: str,
) -> ValidationResult:
    """Validate that end timestamps are not earlier than start timestamps."""
    schema_result = validate_required_columns(
        frame,
        (
            start_column,
            end_column,
        ),
    )

    if not schema_result.valid:
        return schema_result

    start = pd.to_datetime(
        frame[start_column],
        errors="coerce",
        utc=True,
    )
    end = pd.to_datetime(
        frame[end_column],
        errors="coerce",
        utc=True,
    )

    invalid_mask = (
        start.notna()
        & end.notna()
        & end.lt(start)
    )
    invalid_count = int(invalid_mask.sum())

    if invalid_count:
        return ValidationResult(
            valid=False,
            issues=(
                ValidationIssue(
                    rule="timestamp_order",
                    message=(
                        f"'{end_column}' must be greater than or equal "
                        f"to '{start_column}'."
                    ),
                    row_count=invalid_count,
                ),
            ),
        )

    return ValidationResult(
        valid=True,
        issues=(),
    )


def validate_allowed_values(
    frame: pd.DataFrame,
    *,
    column: str,
    allowed_values: Iterable[Any],
) -> ValidationResult:
    """Validate that a column contains only configured values."""
    schema_result = validate_required_columns(
        frame,
        [column],
    )

    if not schema_result.valid:
        return schema_result

    allowed = set(allowed_values)
    invalid_mask = frame[column].notna() & ~frame[column].isin(allowed)
    invalid_count = int(invalid_mask.sum())

    if invalid_count:
        return ValidationResult(
            valid=False,
            issues=(
                ValidationIssue(
                    rule="allowed_values",
                    message=(
                        f"Column '{column}' contains unsupported values. "
                        f"Allowed values: {sorted(allowed)}."
                    ),
                    row_count=invalid_count,
                ),
            ),
        )

    return ValidationResult(
        valid=True,
        issues=(),
    )


def validate_foreign_key(
    frame: pd.DataFrame,
    *,
    key_column: str,
    reference: pd.DataFrame,
    reference_key: str | None = None,
) -> ValidationResult:
    """Validate that source keys exist in a reference DataFrame."""
    resolved_reference_key = reference_key or key_column

    source_schema = validate_required_columns(
        frame,
        [key_column],
    )
    if not source_schema.valid:
        return source_schema

    reference_schema = validate_required_columns(
        reference,
        [resolved_reference_key],
    )
    if not reference_schema.valid:
        return reference_schema

    reference_values = set(
        reference[resolved_reference_key].dropna()
    )

    missing_mask = (
        frame[key_column].notna()
        & ~frame[key_column].isin(reference_values)
    )
    missing_count = int(missing_mask.sum())

    if missing_count:
        missing_values = (
            frame.loc[missing_mask, key_column]
            .drop_duplicates()
            .astype("string")
            .tolist()
        )

        return ValidationResult(
            valid=False,
            issues=(
                ValidationIssue(
                    rule="foreign_key",
                    message=(
                        f"Column '{key_column}' contains references "
                        f"missing from '{resolved_reference_key}': "
                        f"{missing_values}"
                    ),
                    row_count=missing_count,
                ),
            ),
        )

    return ValidationResult(
        valid=True,
        issues=(),
    )


def validate_dataframe(
    frame: pd.DataFrame,
    *,
    required_columns: Iterable[str] = (),
    required_value_columns: Iterable[str] = (),
    unique_key_columns: Iterable[str] = (),
    numeric_columns: Iterable[str] = (),
    non_negative_columns: Iterable[str] = (),
    datetime_columns: Iterable[str] = (),
    allowed_values: Mapping[str, Iterable[Any]] | None = None,
) -> ValidationResult:
    """Run the standard validation suite for normalized API data."""
    _validate_dataframe(frame)

    results: list[ValidationResult] = [
        validate_required_columns(
            frame,
            required_columns,
        ),
        validate_required_values(
            frame,
            required_value_columns,
        )
        if tuple(required_value_columns)
        else ValidationResult(
            valid=True,
            issues=(),
        ),
        validate_unique_keys(
            frame,
            unique_key_columns,
        )
        if tuple(unique_key_columns)
        else ValidationResult(
            valid=True,
            issues=(),
        ),
        validate_numeric_columns(
            frame,
            numeric_columns,
        )
        if tuple(numeric_columns)
        else ValidationResult(
            valid=True,
            issues=(),
        ),
        validate_non_negative_columns(
            frame,
            non_negative_columns,
        )
        if tuple(non_negative_columns)
        else ValidationResult(
            valid=True,
            issues=(),
        ),
        validate_datetime_columns(
            frame,
            datetime_columns,
        )
        if tuple(datetime_columns)
        else ValidationResult(
            valid=True,
            issues=(),
        ),
    ]

    if allowed_values:
        results.extend(
            validate_allowed_values(
                frame,
                column=column,
                allowed_values=values,
            )
            for column, values in allowed_values.items()
        )

    issues = tuple(
        issue
        for result in results
        for issue in result.issues
    )

    return ValidationResult(
        valid=not issues,
        issues=issues,
    )


def validate_ingestion_result(
    frame: pd.DataFrame,
    *,
    required_columns: Iterable[str] = (),
) -> ValidationResult:
    """Validate the normalized dataset immediately after ingestion."""
    return validate_dataframe(
        frame,
        required_columns=required_columns,
    )


def validate_transformed_data(
    frame: pd.DataFrame,
    *,
    required_columns: Iterable[str] = (),
    numeric_columns: Iterable[str] = (),
    datetime_columns: Iterable[str] = (),
) -> ValidationResult:
    """Validate the dataset contract expected by downstream processing."""
    return validate_dataframe(
        frame,
        required_columns=required_columns,
        numeric_columns=numeric_columns,
        datetime_columns=datetime_columns,
    )


def assert_valid(result: ValidationResult) -> None:
    """Raise a validation exception when the result is invalid."""
    try:
        result.raise_if_invalid()
    except ValueError as exc:
        raise ValidationError(
            str(exc)
        ) from exc


__all__ = [
    "ValidationError",
    "ValidationIssue",
    "ValidationResult",
    "assert_valid",
    "validate_allowed_values",
    "validate_dataframe",
    "validate_datetime_columns",
    "validate_foreign_key",
    "validate_ingestion_result",
    "validate_non_negative_columns",
    "validate_numeric_columns",
    "validate_required_columns",
    "validate_required_values",
    "validate_timestamp_order",
    "validate_transformed_data",
    "validate_unique_keys",
]