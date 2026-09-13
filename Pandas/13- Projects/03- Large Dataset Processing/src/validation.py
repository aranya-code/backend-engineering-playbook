from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

import pandas as pd


class ValidationError(ValueError):
    """Raised when a large-dataset validation operation fails."""


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """Represent one data-quality validation issue."""

    check: str
    message: str
    column: str | None = None
    row_count: int = 0


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Represent the outcome of one or more validation checks."""

    issues: tuple[ValidationIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        """Return whether no validation issues were recorded."""
        return not self.issues

    @property
    def issue_count(self) -> int:
        """Return the number of validation issues."""
        return len(self.issues)

    def extend(
        self,
        *results: ValidationResult,
    ) -> ValidationResult:
        """Return a new result containing issues from all supplied results."""
        issues = list(self.issues)

        for result in results:
            issues.extend(result.issues)

        return ValidationResult(
            issues=tuple(issues)
        )


def _validate_frame(
    frame: pd.DataFrame,
) -> None:
    """Validate that the input is a DataFrame."""
    if not isinstance(frame, pd.DataFrame):
        raise ValidationError(
            "frame must be a pandas DataFrame."
        )


def _validate_columns(
    frame: pd.DataFrame,
    columns: Iterable[str],
) -> tuple[str, ...]:
    """Validate that all requested columns exist."""
    requested = tuple(columns)
    missing = [
        column
        for column in requested
        if column not in frame.columns
    ]

    if missing:
        raise ValidationError(
            "Missing required columns: "
            + ", ".join(missing)
        )

    return requested


def validate_required_columns(
    frame: pd.DataFrame,
    *,
    required_columns: Iterable[str],
) -> ValidationResult:
    """Check whether all required columns are present."""
    _validate_frame(frame)

    required = tuple(required_columns)
    missing = [
        column
        for column in required
        if column not in frame.columns
    ]

    issues = tuple(
        ValidationIssue(
            check="required_columns",
            column=column,
            message=f"Required column is missing: {column}",
            row_count=len(frame),
        )
        for column in missing
    )

    return ValidationResult(
        issues=issues
    )


def validate_not_empty(
    frame: pd.DataFrame,
) -> ValidationResult:
    """Reject datasets or chunks with zero rows."""
    _validate_frame(frame)

    if not frame.empty:
        return ValidationResult()

    return ValidationResult(
        issues=(
            ValidationIssue(
                check="not_empty",
                message="Dataset contains no rows.",
                row_count=0,
            ),
        )
    )


def validate_required_values(
    frame: pd.DataFrame,
    *,
    columns: Iterable[str],
) -> ValidationResult:
    """Check that required columns contain usable values."""
    _validate_frame(frame)

    columns = _validate_columns(
        frame,
        columns,
    )

    issues: list[ValidationIssue] = []

    for column in columns:
        values = frame[column]
        missing = values.isna()

        if pd.api.types.is_string_dtype(values):
            missing |= (
                values.astype("string")
                .fillna("")
                .str.strip()
                .eq("")
            )

        row_count = int(missing.sum())

        if row_count:
            issues.append(
                ValidationIssue(
                    check="required_values",
                    column=column,
                    message=(
                        f"Column '{column}' contains "
                        f"{row_count} missing or blank values."
                    ),
                    row_count=row_count,
                )
            )

    return ValidationResult(
        issues=tuple(issues)
    )


def validate_unique_keys(
    frame: pd.DataFrame,
    *,
    columns: Sequence[str],
) -> ValidationResult:
    """Check uniqueness of a single or composite key."""
    _validate_frame(frame)

    columns = _validate_columns(
        frame,
        columns,
    )

    if not columns or frame.empty:
        return ValidationResult()

    duplicate_mask = frame.duplicated(
        subset=list(columns),
        keep=False,
    )

    duplicate_rows = int(
        duplicate_mask.sum()
    )

    if not duplicate_rows:
        return ValidationResult()

    return ValidationResult(
        issues=(
            ValidationIssue(
                check="unique_keys",
                message=(
                    "Duplicate key values detected for "
                    + ", ".join(columns)
                    + f": {duplicate_rows} rows."
                ),
                column=",".join(columns),
                row_count=duplicate_rows,
            ),
        )
    )


def validate_numeric_columns(
    frame: pd.DataFrame,
    *,
    columns: Iterable[str],
) -> ValidationResult:
    """Check that configured columns contain numeric-compatible values."""
    _validate_frame(frame)

    columns = _validate_columns(
        frame,
        columns,
    )

    issues: list[ValidationIssue] = []

    for column in columns:
        values = pd.to_numeric(
            frame[column],
            errors="coerce",
        )

        invalid = (
            frame[column].notna()
            & values.isna()
        )

        invalid_rows = int(
            invalid.sum()
        )

        if invalid_rows:
            issues.append(
                ValidationIssue(
                    check="numeric",
                    column=column,
                    message=(
                        f"Column '{column}' contains "
                        f"{invalid_rows} non-numeric values."
                    ),
                    row_count=invalid_rows,
                )
            )

    return ValidationResult(
        issues=tuple(issues)
    )


def validate_non_negative_columns(
    frame: pd.DataFrame,
    *,
    columns: Iterable[str],
) -> ValidationResult:
    """Check that numeric columns do not contain negative values."""
    _validate_frame(frame)

    columns = _validate_columns(
        frame,
        columns,
    )

    issues: list[ValidationIssue] = []

    for column in columns:
        values = pd.to_numeric(
            frame[column],
            errors="coerce",
        )
        negative = values.lt(0)

        invalid_rows = int(
            negative.sum()
        )

        if invalid_rows:
            issues.append(
                ValidationIssue(
                    check="non_negative",
                    column=column,
                    message=(
                        f"Column '{column}' contains "
                        f"{invalid_rows} negative values."
                    ),
                    row_count=invalid_rows,
                )
            )

    return ValidationResult(
        issues=tuple(issues)
    )


def validate_datetime_columns(
    frame: pd.DataFrame,
    *,
    columns: Iterable[str],
) -> ValidationResult:
    """Check that non-null values in configured columns are valid datetimes."""
    _validate_frame(frame)

    columns = _validate_columns(
        frame,
        columns,
    )

    issues: list[ValidationIssue] = []

    for column in columns:
        parsed = pd.to_datetime(
            frame[column],
            errors="coerce",
            utc=True,
        )

        invalid = (
            frame[column].notna()
            & parsed.isna()
        )

        invalid_rows = int(
            invalid.sum()
        )

        if invalid_rows:
            issues.append(
                ValidationIssue(
                    check="datetime",
                    column=column,
                    message=(
                        f"Column '{column}' contains "
                        f"{invalid_rows} invalid timestamps."
                    ),
                    row_count=invalid_rows,
                )
            )

    return ValidationResult(
        issues=tuple(issues)
    )


def validate_timestamp_order(
    frame: pd.DataFrame,
    *,
    start_column: str,
    end_column: str,
) -> ValidationResult:
    """Check that an end timestamp does not precede its start timestamp."""
    _validate_frame(frame)

    _validate_columns(
        frame,
        (
            start_column,
            end_column,
        ),
    )

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

    invalid = (
        start.notna()
        & end.notna()
        & end.lt(start)
    )

    invalid_rows = int(
        invalid.sum()
    )

    if not invalid_rows:
        return ValidationResult()

    return ValidationResult(
        issues=(
            ValidationIssue(
                check="timestamp_order",
                column=end_column,
                message=(
                    f"Column '{end_column}' precedes "
                    f"'{start_column}' in {invalid_rows} rows."
                ),
                row_count=invalid_rows,
            ),
        )
    )


def validate_allowed_values(
    frame: pd.DataFrame,
    *,
    column: str,
    allowed_values: Iterable[object],
) -> ValidationResult:
    """Check that non-null values belong to an allowed set."""
    _validate_frame(frame)

    _validate_columns(
        frame,
        (column,),
    )

    allowed = set(
        allowed_values
    )

    invalid = (
        frame[column].notna()
        & ~frame[column].isin(allowed)
    )

    invalid_rows = int(
        invalid.sum()
    )

    if not invalid_rows:
        return ValidationResult()

    invalid_values = (
        frame.loc[
            invalid,
            column,
        ]
        .drop_duplicates()
        .astype(str)
        .tolist()
    )

    return ValidationResult(
        issues=(
            ValidationIssue(
                check="allowed_values",
                column=column,
                message=(
                    f"Column '{column}' contains "
                    f"{invalid_rows} values outside the allowed set. "
                    f"Examples: {invalid_values[:10]}"
                ),
                row_count=invalid_rows,
            ),
        )
    )


def validate_foreign_key(
    frame: pd.DataFrame,
    *,
    column: str,
    reference: pd.DataFrame,
    reference_column: str,
) -> ValidationResult:
    """Check that non-null foreign-key values exist in a reference dataset."""
    _validate_frame(frame)
    _validate_frame(reference)

    _validate_columns(
        frame,
        (column,),
    )
    _validate_columns(
        reference,
        (reference_column,),
    )

    reference_values = (
        reference[reference_column]
        .dropna()
        .drop_duplicates()
    )

    invalid = (
        frame[column].notna()
        & ~frame[column].isin(reference_values)
    )

    invalid_rows = int(
        invalid.sum()
    )

    if not invalid_rows:
        return ValidationResult()

    return ValidationResult(
        issues=(
            ValidationIssue(
                check="foreign_key",
                column=column,
                message=(
                    f"Column '{column}' contains "
                    f"{invalid_rows} orphan foreign-key values."
                ),
                row_count=invalid_rows,
            ),
        )
    )


def validate_schema_consistency(
    frame: pd.DataFrame,
    *,
    expected_columns: Sequence[str],
) -> ValidationResult:
    """Check that a DataFrame exposes the expected schema."""
    _validate_frame(frame)

    expected = tuple(expected_columns)
    actual = tuple(
        str(column)
        for column in frame.columns
    )

    missing = [
        column
        for column in expected
        if column not in actual
    ]
    unexpected = [
        column
        for column in actual
        if column not in expected
    ]

    issues: list[ValidationIssue] = []

    if missing:
        issues.append(
            ValidationIssue(
                check="schema",
                message=(
                    "Expected columns are missing: "
                    + ", ".join(missing)
                ),
                row_count=len(frame),
            )
        )

    if unexpected:
        issues.append(
            ValidationIssue(
                check="schema",
                message=(
                    "Unexpected columns are present: "
                    + ", ".join(unexpected)
                ),
                row_count=len(frame),
            )
        )

    return ValidationResult(
        issues=tuple(issues)
    )


def validate_memory_usage(
    frame: pd.DataFrame,
    *,
    maximum_bytes: int,
) -> ValidationResult:
    """Check that a chunk remains below the configured memory budget."""
    _validate_frame(frame)

    if maximum_bytes <= 0:
        raise ValidationError(
            "maximum_bytes must be greater than zero."
        )

    memory_bytes = int(
        frame.memory_usage(
            index=True,
            deep=True,
        ).sum()
    )

    if memory_bytes <= maximum_bytes:
        return ValidationResult()

    return ValidationResult(
        issues=(
            ValidationIssue(
                check="memory_usage",
                message=(
                    f"DataFrame uses {memory_bytes} bytes, "
                    f"exceeding the configured limit of "
                    f"{maximum_bytes} bytes."
                ),
                row_count=len(frame),
            ),
        )
    )


def validate_chunk(
    frame: pd.DataFrame,
    *,
    required_columns: Iterable[str] = (),
    required_value_columns: Iterable[str] = (),
    unique_key_columns: Sequence[str] = (),
    numeric_columns: Iterable[str] = (),
    non_negative_columns: Iterable[str] = (),
    datetime_columns: Iterable[str] = (),
    allowed_values: Mapping[str, Iterable[object]] | None = None,
    require_non_empty: bool = False,
    maximum_memory_bytes: int | None = None,
) -> ValidationResult:
    """Run configured data-quality checks against one chunk."""
    _validate_frame(frame)

    results: list[ValidationResult] = []

    if require_non_empty:
        results.append(
            validate_not_empty(
                frame
            )
        )

    results.append(
        validate_required_columns(
            frame,
            required_columns=required_columns,
        )
    )

    results.append(
        validate_required_values(
            frame,
            columns=required_value_columns,
        )
    )

    if unique_key_columns:
        results.append(
            validate_unique_keys(
                frame,
                columns=unique_key_columns,
            )
        )

    if numeric_columns:
        results.append(
            validate_numeric_columns(
                frame,
                columns=numeric_columns,
            )
        )

    if non_negative_columns:
        results.append(
            validate_non_negative_columns(
                frame,
                columns=non_negative_columns,
            )
        )

    if datetime_columns:
        results.append(
            validate_datetime_columns(
                frame,
                columns=datetime_columns,
            )
        )

    for column, values in (
        allowed_values or {}
    ).items():
        results.append(
            validate_allowed_values(
                frame,
                column=column,
                allowed_values=values,
            )
        )

    if maximum_memory_bytes is not None:
        results.append(
            validate_memory_usage(
                frame,
                maximum_bytes=maximum_memory_bytes,
            )
        )

    combined = ValidationResult()

    for result in results:
        combined = combined.extend(
            result
        )

    return combined


def validate_global_dataset(
    frame: pd.DataFrame,
    *,
    required_columns: Iterable[str] = (),
    unique_key_columns: Sequence[str] = (),
    numeric_columns: Iterable[str] = (),
    non_negative_columns: Iterable[str] = (),
    datetime_columns: Iterable[str] = (),
    allowed_values: Mapping[str, Iterable[object]] | None = None,
) -> ValidationResult:
    """Run dataset-level checks after all chunks have been combined."""
    return validate_chunk(
        frame,
        required_columns=required_columns,
        required_value_columns=required_columns,
        unique_key_columns=unique_key_columns,
        numeric_columns=numeric_columns,
        non_negative_columns=non_negative_columns,
        datetime_columns=datetime_columns,
        allowed_values=allowed_values,
        require_non_empty=True,
    )


def assert_valid(
    result: ValidationResult,
) -> ValidationResult:
    """Raise ValidationError when a validation result is invalid."""
    if result.is_valid:
        return result

    messages = [
        (
            f"[{issue.check}] "
            f"{issue.message}"
        )
        for issue in result.issues
    ]

    raise ValidationError(
        "Dataset validation failed:\n"
        + "\n".join(messages)
    )


__all__ = [
    "ValidationError",
    "ValidationIssue",
    "ValidationResult",
    "assert_valid",
    "validate_allowed_values",
    "validate_chunk",
    "validate_datetime_columns",
    "validate_foreign_key",
    "validate_global_dataset",
    "validate_memory_usage",
    "validate_non_negative_columns",
    "validate_not_empty",
    "validate_numeric_columns",
    "validate_required_columns",
    "validate_required_values",
    "validate_schema_consistency",
    "validate_timestamp_order",
    "validate_unique_keys",
]

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

import pandas as pd


class ValidationError(ValueError):
    """Raised when a large-dataset validation operation fails."""


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """Represent one data-quality validation issue."""

    check: str
    message: str
    column: str | None = None
    row_count: int = 0


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Represent the outcome of one or more validation checks."""

    issues: tuple[ValidationIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        """Return whether no validation issues were recorded."""
        return not self.issues

    @property
    def issue_count(self) -> int:
        """Return the number of validation issues."""
        return len(self.issues)

    def extend(
        self,
        *results: ValidationResult,
    ) -> ValidationResult:
        """Return a new result containing issues from all supplied results."""
        issues = list(self.issues)

        for result in results:
            issues.extend(result.issues)

        return ValidationResult(
            issues=tuple(issues)
        )


def _validate_frame(
    frame: pd.DataFrame,
) -> None:
    """Validate that the input is a DataFrame."""
    if not isinstance(frame, pd.DataFrame):
        raise ValidationError(
            "frame must be a pandas DataFrame."
        )


def _validate_columns(
    frame: pd.DataFrame,
    columns: Iterable[str],
) -> tuple[str, ...]:
    """Validate that all requested columns exist."""
    requested = tuple(columns)
    missing = [
        column
        for column in requested
        if column not in frame.columns
    ]

    if missing:
        raise ValidationError(
            "Missing required columns: "
            + ", ".join(missing)
        )

    return requested


def validate_required_columns(
    frame: pd.DataFrame,
    *,
    required_columns: Iterable[str],
) -> ValidationResult:
    """Check whether all required columns are present."""
    _validate_frame(frame)

    required = tuple(required_columns)
    missing = [
        column
        for column in required
        if column not in frame.columns
    ]

    issues = tuple(
        ValidationIssue(
            check="required_columns",
            column=column,
            message=f"Required column is missing: {column}",
            row_count=len(frame),
        )
        for column in missing
    )

    return ValidationResult(
        issues=issues
    )


def validate_not_empty(
    frame: pd.DataFrame,
) -> ValidationResult:
    """Reject datasets or chunks with zero rows."""
    _validate_frame(frame)

    if not frame.empty:
        return ValidationResult()

    return ValidationResult(
        issues=(
            ValidationIssue(
                check="not_empty",
                message="Dataset contains no rows.",
                row_count=0,
            ),
        )
    )


def validate_required_values(
    frame: pd.DataFrame,
    *,
    columns: Iterable[str],
) -> ValidationResult:
    """Check that required columns contain usable values."""
    _validate_frame(frame)

    columns = _validate_columns(
        frame,
        columns,
    )

    issues: list[ValidationIssue] = []

    for column in columns:
        values = frame[column]
        missing = values.isna()

        if pd.api.types.is_string_dtype(values):
            missing |= (
                values.astype("string")
                .fillna("")
                .str.strip()
                .eq("")
            )

        row_count = int(missing.sum())

        if row_count:
            issues.append(
                ValidationIssue(
                    check="required_values",
                    column=column,
                    message=(
                        f"Column '{column}' contains "
                        f"{row_count} missing or blank values."
                    ),
                    row_count=row_count,
                )
            )

    return ValidationResult(
        issues=tuple(issues)
    )


def validate_unique_keys(
    frame: pd.DataFrame,
    *,
    columns: Sequence[str],
) -> ValidationResult:
    """Check uniqueness of a single or composite key."""
    _validate_frame(frame)

    columns = _validate_columns(
        frame,
        columns,
    )

    if not columns or frame.empty:
        return ValidationResult()

    duplicate_mask = frame.duplicated(
        subset=list(columns),
        keep=False,
    )

    duplicate_rows = int(
        duplicate_mask.sum()
    )

    if not duplicate_rows:
        return ValidationResult()

    return ValidationResult(
        issues=(
            ValidationIssue(
                check="unique_keys",
                message=(
                    "Duplicate key values detected for "
                    + ", ".join(columns)
                    + f": {duplicate_rows} rows."
                ),
                column=",".join(columns),
                row_count=duplicate_rows,
            ),
        )
    )


def validate_numeric_columns(
    frame: pd.DataFrame,
    *,
    columns: Iterable[str],
) -> ValidationResult:
    """Check that configured columns contain numeric-compatible values."""
    _validate_frame(frame)

    columns = _validate_columns(
        frame,
        columns,
    )

    issues: list[ValidationIssue] = []

    for column in columns:
        values = pd.to_numeric(
            frame[column],
            errors="coerce",
        )

        invalid = (
            frame[column].notna()
            & values.isna()
        )

        invalid_rows = int(
            invalid.sum()
        )

        if invalid_rows:
            issues.append(
                ValidationIssue(
                    check="numeric",
                    column=column,
                    message=(
                        f"Column '{column}' contains "
                        f"{invalid_rows} non-numeric values."
                    ),
                    row_count=invalid_rows,
                )
            )

    return ValidationResult(
        issues=tuple(issues)
    )


def validate_non_negative_columns(
    frame: pd.DataFrame,
    *,
    columns: Iterable[str],
) -> ValidationResult:
    """Check that numeric columns do not contain negative values."""
    _validate_frame(frame)

    columns = _validate_columns(
        frame,
        columns,
    )

    issues: list[ValidationIssue] = []

    for column in columns:
        values = pd.to_numeric(
            frame[column],
            errors="coerce",
        )
        negative = values.lt(0)

        invalid_rows = int(
            negative.sum()
        )

        if invalid_rows:
            issues.append(
                ValidationIssue(
                    check="non_negative",
                    column=column,
                    message=(
                        f"Column '{column}' contains "
                        f"{invalid_rows} negative values."
                    ),
                    row_count=invalid_rows,
                )
            )

    return ValidationResult(
        issues=tuple(issues)
    )


def validate_datetime_columns(
    frame: pd.DataFrame,
    *,
    columns: Iterable[str],
) -> ValidationResult:
    """Check that non-null values in configured columns are valid datetimes."""
    _validate_frame(frame)

    columns = _validate_columns(
        frame,
        columns,
    )

    issues: list[ValidationIssue] = []

    for column in columns:
        parsed = pd.to_datetime(
            frame[column],
            errors="coerce",
            utc=True,
        )

        invalid = (
            frame[column].notna()
            & parsed.isna()
        )

        invalid_rows = int(
            invalid.sum()
        )

        if invalid_rows:
            issues.append(
                ValidationIssue(
                    check="datetime",
                    column=column,
                    message=(
                        f"Column '{column}' contains "
                        f"{invalid_rows} invalid timestamps."
                    ),
                    row_count=invalid_rows,
                )
            )

    return ValidationResult(
        issues=tuple(issues)
    )


def validate_timestamp_order(
    frame: pd.DataFrame,
    *,
    start_column: str,
    end_column: str,
) -> ValidationResult:
    """Check that an end timestamp does not precede its start timestamp."""
    _validate_frame(frame)

    _validate_columns(
        frame,
        (
            start_column,
            end_column,
        ),
    )

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

    invalid = (
        start.notna()
        & end.notna()
        & end.lt(start)
    )

    invalid_rows = int(
        invalid.sum()
    )

    if not invalid_rows:
        return ValidationResult()

    return ValidationResult(
        issues=(
            ValidationIssue(
                check="timestamp_order",
                column=end_column,
                message=(
                    f"Column '{end_column}' precedes "
                    f"'{start_column}' in {invalid_rows} rows."
                ),
                row_count=invalid_rows,
            ),
        )
    )


def validate_allowed_values(
    frame: pd.DataFrame,
    *,
    column: str,
    allowed_values: Iterable[object],
) -> ValidationResult:
    """Check that non-null values belong to an allowed set."""
    _validate_frame(frame)

    _validate_columns(
        frame,
        (column,),
    )

    allowed = set(
        allowed_values
    )

    invalid = (
        frame[column].notna()
        & ~frame[column].isin(allowed)
    )

    invalid_rows = int(
        invalid.sum()
    )

    if not invalid_rows:
        return ValidationResult()

    invalid_values = (
        frame.loc[
            invalid,
            column,
        ]
        .drop_duplicates()
        .astype(str)
        .tolist()
    )

    return ValidationResult(
        issues=(
            ValidationIssue(
                check="allowed_values",
                column=column,
                message=(
                    f"Column '{column}' contains "
                    f"{invalid_rows} values outside the allowed set. "
                    f"Examples: {invalid_values[:10]}"
                ),
                row_count=invalid_rows,
            ),
        )
    )


def validate_foreign_key(
    frame: pd.DataFrame,
    *,
    column: str,
    reference: pd.DataFrame,
    reference_column: str,
) -> ValidationResult:
    """Check that non-null foreign-key values exist in a reference dataset."""
    _validate_frame(frame)
    _validate_frame(reference)

    _validate_columns(
        frame,
        (column,),
    )
    _validate_columns(
        reference,
        (reference_column,),
    )

    reference_values = (
        reference[reference_column]
        .dropna()
        .drop_duplicates()
    )

    invalid = (
        frame[column].notna()
        & ~frame[column].isin(reference_values)
    )

    invalid_rows = int(
        invalid.sum()
    )

    if not invalid_rows:
        return ValidationResult()

    return ValidationResult(
        issues=(
            ValidationIssue(
                check="foreign_key",
                column=column,
                message=(
                    f"Column '{column}' contains "
                    f"{invalid_rows} orphan foreign-key values."
                ),
                row_count=invalid_rows,
            ),
        )
    )


def validate_schema_consistency(
    frame: pd.DataFrame,
    *,
    expected_columns: Sequence[str],
) -> ValidationResult:
    """Check that a DataFrame exposes the expected schema."""
    _validate_frame(frame)

    expected = tuple(expected_columns)
    actual = tuple(
        str(column)
        for column in frame.columns
    )

    missing = [
        column
        for column in expected
        if column not in actual
    ]
    unexpected = [
        column
        for column in actual
        if column not in expected
    ]

    issues: list[ValidationIssue] = []

    if missing:
        issues.append(
            ValidationIssue(
                check="schema",
                message=(
                    "Expected columns are missing: "
                    + ", ".join(missing)
                ),
                row_count=len(frame),
            )
        )

    if unexpected:
        issues.append(
            ValidationIssue(
                check="schema",
                message=(
                    "Unexpected columns are present: "
                    + ", ".join(unexpected)
                ),
                row_count=len(frame),
            )
        )

    return ValidationResult(
        issues=tuple(issues)
    )


def validate_memory_usage(
    frame: pd.DataFrame,
    *,
    maximum_bytes: int,
) -> ValidationResult:
    """Check that a chunk remains below the configured memory budget."""
    _validate_frame(frame)

    if maximum_bytes <= 0:
        raise ValidationError(
            "maximum_bytes must be greater than zero."
        )

    memory_bytes = int(
        frame.memory_usage(
            index=True,
            deep=True,
        ).sum()
    )

    if memory_bytes <= maximum_bytes:
        return ValidationResult()

    return ValidationResult(
        issues=(
            ValidationIssue(
                check="memory_usage",
                message=(
                    f"DataFrame uses {memory_bytes} bytes, "
                    f"exceeding the configured limit of "
                    f"{maximum_bytes} bytes."
                ),
                row_count=len(frame),
            ),
        )
    )


def validate_chunk(
    frame: pd.DataFrame,
    *,
    required_columns: Iterable[str] = (),
    required_value_columns: Iterable[str] = (),
    unique_key_columns: Sequence[str] = (),
    numeric_columns: Iterable[str] = (),
    non_negative_columns: Iterable[str] = (),
    datetime_columns: Iterable[str] = (),
    allowed_values: Mapping[str, Iterable[object]] | None = None,
    require_non_empty: bool = False,
    maximum_memory_bytes: int | None = None,
) -> ValidationResult:
    """Run configured data-quality checks against one chunk."""
    _validate_frame(frame)

    results: list[ValidationResult] = []

    if require_non_empty:
        results.append(
            validate_not_empty(
                frame
            )
        )

    results.append(
        validate_required_columns(
            frame,
            required_columns=required_columns,
        )
    )

    results.append(
        validate_required_values(
            frame,
            columns=required_value_columns,
        )
    )

    if unique_key_columns:
        results.append(
            validate_unique_keys(
                frame,
                columns=unique_key_columns,
            )
        )

    if numeric_columns:
        results.append(
            validate_numeric_columns(
                frame,
                columns=numeric_columns,
            )
        )

    if non_negative_columns:
        results.append(
            validate_non_negative_columns(
                frame,
                columns=non_negative_columns,
            )
        )

    if datetime_columns:
        results.append(
            validate_datetime_columns(
                frame,
                columns=datetime_columns,
            )
        )

    for column, values in (
        allowed_values or {}
    ).items():
        results.append(
            validate_allowed_values(
                frame,
                column=column,
                allowed_values=values,
            )
        )

    if maximum_memory_bytes is not None:
        results.append(
            validate_memory_usage(
                frame,
                maximum_bytes=maximum_memory_bytes,
            )
        )

    combined = ValidationResult()

    for result in results:
        combined = combined.extend(
            result
        )

    return combined


def validate_global_dataset(
    frame: pd.DataFrame,
    *,
    required_columns: Iterable[str] = (),
    unique_key_columns: Sequence[str] = (),
    numeric_columns: Iterable[str] = (),
    non_negative_columns: Iterable[str] = (),
    datetime_columns: Iterable[str] = (),
    allowed_values: Mapping[str, Iterable[object]] | None = None,
) -> ValidationResult:
    """Run dataset-level checks after all chunks have been combined."""
    return validate_chunk(
        frame,
        required_columns=required_columns,
        required_value_columns=required_columns,
        unique_key_columns=unique_key_columns,
        numeric_columns=numeric_columns,
        non_negative_columns=non_negative_columns,
        datetime_columns=datetime_columns,
        allowed_values=allowed_values,
        require_non_empty=True,
    )


def assert_valid(
    result: ValidationResult,
) -> ValidationResult:
    """Raise ValidationError when a validation result is invalid."""
    if result.is_valid:
        return result

    messages = [
        (
            f"[{issue.check}] "
            f"{issue.message}"
        )
        for issue in result.issues
    ]

    raise ValidationError(
        "Dataset validation failed:\n"
        + "\n".join(messages)
    )


__all__ = [
    "ValidationError",
    "ValidationIssue",
    "ValidationResult",
    "assert_valid",
    "validate_allowed_values",
    "validate_chunk",
    "validate_datetime_columns",
    "validate_foreign_key",
    "validate_global_dataset",
    "validate_memory_usage",
    "validate_non_negative_columns",
    "validate_not_empty",
    "validate_numeric_columns",
    "validate_required_columns",
    "validate_required_values",
    "validate_schema_consistency",
    "validate_timestamp_order",
    "validate_unique_keys",
]