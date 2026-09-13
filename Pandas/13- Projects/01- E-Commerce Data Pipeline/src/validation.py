from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


VALID_ORDER_STATUSES = frozenset(
    {
        "pending",
        "completed",
        "cancelled",
    }
)

ORDER_REQUIRED_COLUMNS = (
    "order_id",
    "customer_id",
    "product_id",
    "status",
    "amount",
    "created_at",
    "updated_at",
)

CUSTOMER_REQUIRED_COLUMNS = (
    "customer_id",
    "segment",
)

REPORT_REQUIRED_COLUMNS = (
    "order_date",
    "order_count",
    "revenue",
)


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """Represent a single validation rule violation."""

    rule: str
    message: str
    row_count: int = 0


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Collect the outcome of one or more validation checks."""

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


def validate_required_columns(
    frame: pd.DataFrame,
    required_columns: tuple[str, ...],
    *,
    dataset_name: str,
) -> ValidationResult:
    """Validate that a DataFrame contains all required columns."""
    issues: list[ValidationIssue] = []

    if not isinstance(frame, pd.DataFrame):
        issues.append(
            ValidationIssue(
                rule="dataframe_type",
                message=f"{dataset_name} must be a pandas DataFrame.",
            )
        )
        return ValidationResult(
            valid=False,
            issues=tuple(issues),
        )

    missing = [
        column
        for column in required_columns
        if column not in frame.columns
    ]

    if missing:
        issues.append(
            ValidationIssue(
                rule="required_columns",
                message=(
                    f"{dataset_name} is missing required columns: "
                    + ", ".join(missing)
                ),
                row_count=len(frame),
            )
        )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def validate_order_schema(
    orders: pd.DataFrame,
) -> ValidationResult:
    """Validate the structural schema and important data types for orders."""
    result = validate_required_columns(
        orders,
        ORDER_REQUIRED_COLUMNS,
        dataset_name="orders",
    )

    issues = list(result.issues)

    if not isinstance(orders, pd.DataFrame):
        return ValidationResult(
            valid=False,
            issues=tuple(issues),
        )

    if issues:
        return ValidationResult(
            valid=False,
            issues=tuple(issues),
        )

    if not (
        pd.api.types.is_numeric_dtype(orders["amount"])
    ):
        issues.append(
            ValidationIssue(
                rule="amount_dtype",
                message="orders.amount must be numeric.",
                row_count=len(orders),
            )
        )

    if not pd.api.types.is_datetime64_any_dtype(
        orders["created_at"]
    ):
        issues.append(
            ValidationIssue(
                rule="created_at_dtype",
                message="orders.created_at must be datetime-like.",
                row_count=len(orders),
            )
        )

    if not pd.api.types.is_datetime64_any_dtype(
        orders["updated_at"]
    ):
        issues.append(
            ValidationIssue(
                rule="updated_at_dtype",
                message="orders.updated_at must be datetime-like.",
                row_count=len(orders),
            )
        )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def validate_orders(
    orders: pd.DataFrame,
) -> ValidationResult:
    """Validate order records against pipeline business rules."""
    schema_result = validate_order_schema(orders)
    issues = list(schema_result.issues)

    if not isinstance(orders, pd.DataFrame):
        return ValidationResult(
            valid=False,
            issues=tuple(issues),
        )

    if issues:
        return ValidationResult(
            valid=False,
            issues=tuple(issues),
        )

    required_value_columns = (
        "order_id",
        "customer_id",
        "product_id",
        "status",
        "amount",
        "created_at",
        "updated_at",
    )

    null_mask = orders[
        list(required_value_columns)
    ].isna().any(axis=1)

    null_count = int(null_mask.sum())

    if null_count:
        issues.append(
            ValidationIssue(
                rule="required_values",
                message=(
                    "Required order fields contain null or invalid "
                    "missing values."
                ),
                row_count=null_count,
            )
        )

    duplicate_order_count = int(
        orders["order_id"].duplicated().sum()
    )

    if duplicate_order_count:
        issues.append(
            ValidationIssue(
                rule="unique_order_id",
                message="order_id values must be unique.",
                row_count=duplicate_order_count,
            )
        )

    invalid_status_mask = ~orders["status"].isin(
        VALID_ORDER_STATUSES
    )

    invalid_status_count = int(
        invalid_status_mask.sum()
    )

    if invalid_status_count:
        issues.append(
            ValidationIssue(
                rule="valid_status",
                message=(
                    "Order status contains unsupported values. "
                    f"Allowed values: {sorted(VALID_ORDER_STATUSES)}."
                ),
                row_count=invalid_status_count,
            )
        )

    negative_amount_mask = orders["amount"].lt(0)

    negative_amount_count = int(
        negative_amount_mask.sum()
    )

    if negative_amount_count:
        issues.append(
            ValidationIssue(
                rule="non_negative_amount",
                message="Order amount cannot be negative.",
                row_count=negative_amount_count,
            )
        )

    invalid_timestamp_mask = (
        orders["created_at"].notna()
        & orders["updated_at"].notna()
        & orders["updated_at"].lt(orders["created_at"])
    )

    invalid_timestamp_count = int(
        invalid_timestamp_mask.sum()
    )

    if invalid_timestamp_count:
        issues.append(
            ValidationIssue(
                rule="timestamp_order",
                message="updated_at must be greater than or equal to created_at.",
                row_count=invalid_timestamp_count,
            )
        )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def validate_customers(
    customers: pd.DataFrame,
) -> ValidationResult:
    """Validate customer reference data."""
    schema_result = validate_required_columns(
        customers,
        CUSTOMER_REQUIRED_COLUMNS,
        dataset_name="customers",
    )

    issues = list(schema_result.issues)

    if not isinstance(customers, pd.DataFrame):
        return ValidationResult(
            valid=False,
            issues=tuple(issues),
        )

    if issues:
        return ValidationResult(
            valid=False,
            issues=tuple(issues),
        )

    null_mask = customers[
        list(CUSTOMER_REQUIRED_COLUMNS)
    ].isna().any(axis=1)

    null_count = int(null_mask.sum())

    if null_count:
        issues.append(
            ValidationIssue(
                rule="customer_required_values",
                message=(
                    "Customer records contain null customer_id "
                    "or segment values."
                ),
                row_count=null_count,
            )
        )

    duplicate_customer_count = int(
        customers["customer_id"].duplicated().sum()
    )

    if duplicate_customer_count:
        issues.append(
            ValidationIssue(
                rule="unique_customer_id",
                message="customer_id values must be unique.",
                row_count=duplicate_customer_count,
            )
        )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def validate_order_customer_relationship(
    orders: pd.DataFrame,
    customers: pd.DataFrame,
) -> ValidationResult:
    """Ensure every order references an existing customer."""
    order_schema = validate_required_columns(
        orders,
        ("customer_id",),
        dataset_name="orders",
    )

    customer_schema = validate_required_columns(
        customers,
        ("customer_id",),
        dataset_name="customers",
    )

    issues = [
        *order_schema.issues,
        *customer_schema.issues,
    ]

    if issues:
        return ValidationResult(
            valid=False,
            issues=tuple(issues),
        )

    customer_ids = set(
        customers["customer_id"].dropna()
    )

    missing_customer_mask = (
        orders["customer_id"].notna()
        & ~orders["customer_id"].isin(customer_ids)
    )

    missing_customer_count = int(
        missing_customer_mask.sum()
    )

    if missing_customer_count:
        missing_ids = (
            orders.loc[
                missing_customer_mask,
                "customer_id",
            ]
            .drop_duplicates()
            .astype("string")
            .tolist()
        )

        issues.append(
            ValidationIssue(
                rule="customer_foreign_key",
                message=(
                    "Orders reference customers that do not exist: "
                    f"{missing_ids}"
                ),
                row_count=missing_customer_count,
            )
        )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def validate_report_reconciliation(
    orders: pd.DataFrame,
    report: pd.DataFrame,
    *,
    tolerance: float = 0.01,
) -> ValidationResult:
    """Reconcile completed-order counts and revenue against a report."""
    issues: list[ValidationIssue] = []

    if tolerance < 0:
        issues.append(
            ValidationIssue(
                rule="reconciliation_tolerance",
                message="tolerance must be non-negative.",
            )
        )
        return ValidationResult(
            valid=False,
            issues=tuple(issues),
        )

    order_schema = validate_required_columns(
        orders,
        (
            "order_id",
            "status",
            "amount",
        ),
        dataset_name="orders",
    )

    report_schema = validate_required_columns(
        report,
        REPORT_REQUIRED_COLUMNS,
        dataset_name="report",
    )

    issues.extend(order_schema.issues)
    issues.extend(report_schema.issues)

    if issues:
        return ValidationResult(
            valid=False,
            issues=tuple(issues),
        )

    completed = orders.loc[
        orders["status"].eq("completed")
    ]

    expected_order_count = int(
        completed["order_id"].nunique()
    )

    expected_revenue = float(
        completed["amount"].sum()
    )

    actual_order_count = int(
        report["order_count"].sum()
    )

    actual_revenue = float(
        report["revenue"].sum()
    )

    if expected_order_count != actual_order_count:
        issues.append(
            ValidationIssue(
                rule="report_order_count_reconciliation",
                message=(
                    "Completed order count does not reconcile: "
                    f"expected {expected_order_count}, "
                    f"reported {actual_order_count}."
                ),
            )
        )

    if abs(expected_revenue - actual_revenue) > tolerance:
        issues.append(
            ValidationIssue(
                rule="report_revenue_reconciliation",
                message=(
                    "Completed revenue does not reconcile: "
                    f"expected {expected_revenue:.2f}, "
                    f"reported {actual_revenue:.2f}, "
                    f"tolerance {tolerance:.2f}."
                )
            )
        )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def validate_pipeline_outputs(
    orders: pd.DataFrame,
    customers: pd.DataFrame,
    report: pd.DataFrame,
    *,
    tolerance: float = 0.01,
) -> ValidationResult:
    """Run the complete validation suite for pipeline outputs."""
    results = (
        validate_orders(orders),
        validate_customers(customers),
        validate_order_customer_relationship(
            orders,
            customers,
        ),
        validate_report_reconciliation(
            orders,
            report,
            tolerance=tolerance,
        ),
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


def assert_valid(
    result: ValidationResult,
) -> None:
    """Raise a validation error when a result is invalid."""
    result.raise_if_invalid()


__all__ = [
    "CUSTOMER_REQUIRED_COLUMNS",
    "ORDER_REQUIRED_COLUMNS",
    "REPORT_REQUIRED_COLUMNS",
    "VALID_ORDER_STATUSES",
    "ValidationIssue",
    "ValidationResult",
    "assert_valid",
    "validate_customers",
    "validate_order_customer_relationship",
    "validate_order_schema",
    "validate_orders",
    "validate_pipeline_outputs",
    "validate_report_reconciliation",
    "validate_required_columns",
]

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


VALID_ORDER_STATUSES = frozenset(
    {
        "pending",
        "completed",
        "cancelled",
    }
)

ORDER_REQUIRED_COLUMNS = (
    "order_id",
    "customer_id",
    "product_id",
    "status",
    "amount",
    "created_at",
    "updated_at",
)

CUSTOMER_REQUIRED_COLUMNS = (
    "customer_id",
    "segment",
)

REPORT_REQUIRED_COLUMNS = (
    "order_date",
    "order_count",
    "revenue",
)


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """Represent a single validation rule violation."""

    rule: str
    message: str
    row_count: int = 0


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Collect the outcome of one or more validation checks."""

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


def validate_required_columns(
    frame: pd.DataFrame,
    required_columns: tuple[str, ...],
    *,
    dataset_name: str,
) -> ValidationResult:
    """Validate that a DataFrame contains all required columns."""
    issues: list[ValidationIssue] = []

    if not isinstance(frame, pd.DataFrame):
        issues.append(
            ValidationIssue(
                rule="dataframe_type",
                message=f"{dataset_name} must be a pandas DataFrame.",
            )
        )
        return ValidationResult(
            valid=False,
            issues=tuple(issues),
        )

    missing = [
        column
        for column in required_columns
        if column not in frame.columns
    ]

    if missing:
        issues.append(
            ValidationIssue(
                rule="required_columns",
                message=(
                    f"{dataset_name} is missing required columns: "
                    + ", ".join(missing)
                ),
                row_count=len(frame),
            )
        )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def validate_order_schema(
    orders: pd.DataFrame,
) -> ValidationResult:
    """Validate the structural schema and important data types for orders."""
    result = validate_required_columns(
        orders,
        ORDER_REQUIRED_COLUMNS,
        dataset_name="orders",
    )

    issues = list(result.issues)

    if not isinstance(orders, pd.DataFrame):
        return ValidationResult(
            valid=False,
            issues=tuple(issues),
        )

    if issues:
        return ValidationResult(
            valid=False,
            issues=tuple(issues),
        )

    if not (
        pd.api.types.is_numeric_dtype(orders["amount"])
    ):
        issues.append(
            ValidationIssue(
                rule="amount_dtype",
                message="orders.amount must be numeric.",
                row_count=len(orders),
            )
        )

    if not pd.api.types.is_datetime64_any_dtype(
        orders["created_at"]
    ):
        issues.append(
            ValidationIssue(
                rule="created_at_dtype",
                message="orders.created_at must be datetime-like.",
                row_count=len(orders),
            )
        )

    if not pd.api.types.is_datetime64_any_dtype(
        orders["updated_at"]
    ):
        issues.append(
            ValidationIssue(
                rule="updated_at_dtype",
                message="orders.updated_at must be datetime-like.",
                row_count=len(orders),
            )
        )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def validate_orders(
    orders: pd.DataFrame,
) -> ValidationResult:
    """Validate order records against pipeline business rules."""
    schema_result = validate_order_schema(orders)
    issues = list(schema_result.issues)

    if not isinstance(orders, pd.DataFrame):
        return ValidationResult(
            valid=False,
            issues=tuple(issues),
        )

    if issues:
        return ValidationResult(
            valid=False,
            issues=tuple(issues),
        )

    required_value_columns = (
        "order_id",
        "customer_id",
        "product_id",
        "status",
        "amount",
        "created_at",
        "updated_at",
    )

    null_mask = orders[
        list(required_value_columns)
    ].isna().any(axis=1)

    null_count = int(null_mask.sum())

    if null_count:
        issues.append(
            ValidationIssue(
                rule="required_values",
                message=(
                    "Required order fields contain null or invalid "
                    "missing values."
                ),
                row_count=null_count,
            )
        )

    duplicate_order_count = int(
        orders["order_id"].duplicated().sum()
    )

    if duplicate_order_count:
        issues.append(
            ValidationIssue(
                rule="unique_order_id",
                message="order_id values must be unique.",
                row_count=duplicate_order_count,
            )
        )

    invalid_status_mask = ~orders["status"].isin(
        VALID_ORDER_STATUSES
    )

    invalid_status_count = int(
        invalid_status_mask.sum()
    )

    if invalid_status_count:
        issues.append(
            ValidationIssue(
                rule="valid_status",
                message=(
                    "Order status contains unsupported values. "
                    f"Allowed values: {sorted(VALID_ORDER_STATUSES)}."
                ),
                row_count=invalid_status_count,
            )
        )

    negative_amount_mask = orders["amount"].lt(0)

    negative_amount_count = int(
        negative_amount_mask.sum()
    )

    if negative_amount_count:
        issues.append(
            ValidationIssue(
                rule="non_negative_amount",
                message="Order amount cannot be negative.",
                row_count=negative_amount_count,
            )
        )

    invalid_timestamp_mask = (
        orders["created_at"].notna()
        & orders["updated_at"].notna()
        & orders["updated_at"].lt(orders["created_at"])
    )

    invalid_timestamp_count = int(
        invalid_timestamp_mask.sum()
    )

    if invalid_timestamp_count:
        issues.append(
            ValidationIssue(
                rule="timestamp_order",
                message="updated_at must be greater than or equal to created_at.",
                row_count=invalid_timestamp_count,
            )
        )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def validate_customers(
    customers: pd.DataFrame,
) -> ValidationResult:
    """Validate customer reference data."""
    schema_result = validate_required_columns(
        customers,
        CUSTOMER_REQUIRED_COLUMNS,
        dataset_name="customers",
    )

    issues = list(schema_result.issues)

    if not isinstance(customers, pd.DataFrame):
        return ValidationResult(
            valid=False,
            issues=tuple(issues),
        )

    if issues:
        return ValidationResult(
            valid=False,
            issues=tuple(issues),
        )

    null_mask = customers[
        list(CUSTOMER_REQUIRED_COLUMNS)
    ].isna().any(axis=1)

    null_count = int(null_mask.sum())

    if null_count:
        issues.append(
            ValidationIssue(
                rule="customer_required_values",
                message=(
                    "Customer records contain null customer_id "
                    "or segment values."
                ),
                row_count=null_count,
            )
        )

    duplicate_customer_count = int(
        customers["customer_id"].duplicated().sum()
    )

    if duplicate_customer_count:
        issues.append(
            ValidationIssue(
                rule="unique_customer_id",
                message="customer_id values must be unique.",
                row_count=duplicate_customer_count,
            )
        )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def validate_order_customer_relationship(
    orders: pd.DataFrame,
    customers: pd.DataFrame,
) -> ValidationResult:
    """Ensure every order references an existing customer."""
    order_schema = validate_required_columns(
        orders,
        ("customer_id",),
        dataset_name="orders",
    )

    customer_schema = validate_required_columns(
        customers,
        ("customer_id",),
        dataset_name="customers",
    )

    issues = [
        *order_schema.issues,
        *customer_schema.issues,
    ]

    if issues:
        return ValidationResult(
            valid=False,
            issues=tuple(issues),
        )

    customer_ids = set(
        customers["customer_id"].dropna()
    )

    missing_customer_mask = (
        orders["customer_id"].notna()
        & ~orders["customer_id"].isin(customer_ids)
    )

    missing_customer_count = int(
        missing_customer_mask.sum()
    )

    if missing_customer_count:
        missing_ids = (
            orders.loc[
                missing_customer_mask,
                "customer_id",
            ]
            .drop_duplicates()
            .astype("string")
            .tolist()
        )

        issues.append(
            ValidationIssue(
                rule="customer_foreign_key",
                message=(
                    "Orders reference customers that do not exist: "
                    f"{missing_ids}"
                ),
                row_count=missing_customer_count,
            )
        )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def validate_report_reconciliation(
    orders: pd.DataFrame,
    report: pd.DataFrame,
    *,
    tolerance: float = 0.01,
) -> ValidationResult:
    """Reconcile completed-order counts and revenue against a report."""
    issues: list[ValidationIssue] = []

    if tolerance < 0:
        issues.append(
            ValidationIssue(
                rule="reconciliation_tolerance",
                message="tolerance must be non-negative.",
            )
        )
        return ValidationResult(
            valid=False,
            issues=tuple(issues),
        )

    order_schema = validate_required_columns(
        orders,
        (
            "order_id",
            "status",
            "amount",
        ),
        dataset_name="orders",
    )

    report_schema = validate_required_columns(
        report,
        REPORT_REQUIRED_COLUMNS,
        dataset_name="report",
    )

    issues.extend(order_schema.issues)
    issues.extend(report_schema.issues)

    if issues:
        return ValidationResult(
            valid=False,
            issues=tuple(issues),
        )

    completed = orders.loc[
        orders["status"].eq("completed")
    ]

    expected_order_count = int(
        completed["order_id"].nunique()
    )

    expected_revenue = float(
        completed["amount"].sum()
    )

    actual_order_count = int(
        report["order_count"].sum()
    )

    actual_revenue = float(
        report["revenue"].sum()
    )

    if expected_order_count != actual_order_count:
        issues.append(
            ValidationIssue(
                rule="report_order_count_reconciliation",
                message=(
                    "Completed order count does not reconcile: "
                    f"expected {expected_order_count}, "
                    f"reported {actual_order_count}."
                ),
            )
        )

    if abs(expected_revenue - actual_revenue) > tolerance:
        issues.append(
            ValidationIssue(
                rule="report_revenue_reconciliation",
                message=(
                    "Completed revenue does not reconcile: "
                    f"expected {expected_revenue:.2f}, "
                    f"reported {actual_revenue:.2f}, "
                    f"tolerance {tolerance:.2f}."
                )
            )
        )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def validate_pipeline_outputs(
    orders: pd.DataFrame,
    customers: pd.DataFrame,
    report: pd.DataFrame,
    *,
    tolerance: float = 0.01,
) -> ValidationResult:
    """Run the complete validation suite for pipeline outputs."""
    results = (
        validate_orders(orders),
        validate_customers(customers),
        validate_order_customer_relationship(
            orders,
            customers,
        ),
        validate_report_reconciliation(
            orders,
            report,
            tolerance=tolerance,
        ),
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


def assert_valid(
    result: ValidationResult,
) -> None:
    """Raise a validation error when a result is invalid."""
    result.raise_if_invalid()


__all__ = [
    "CUSTOMER_REQUIRED_COLUMNS",
    "ORDER_REQUIRED_COLUMNS",
    "REPORT_REQUIRED_COLUMNS",
    "VALID_ORDER_STATUSES",
    "ValidationIssue",
    "ValidationResult",
    "assert_valid",
    "validate_customers",
    "validate_order_customer_relationship",
    "validate_order_schema",
    "validate_orders",
    "validate_pipeline_outputs",
    "validate_report_reconciliation",
    "validate_required_columns",
]