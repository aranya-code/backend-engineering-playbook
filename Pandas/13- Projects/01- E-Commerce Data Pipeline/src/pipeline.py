from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from .aggregation import aggregate_pipeline_metrics
from .cleaning import CleaningResult, clean_order_chunks
from .config import PipelineConfig, config
from .ingestion import ingest_customers, ingest_orders, ingest_products
from .reporting import ReportResult, build_report_bundle
from .transformation import enrich_orders
from .validation import (
    validate_customers,
    validate_order_customer_relationship,
    validate_orders,
    validate_report_reconciliation,
)

logger = logging.getLogger(__name__)


class PipelineError(RuntimeError):
    """Raised when the pipeline cannot complete successfully."""


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """Results produced by a successful pipeline execution."""

    enriched_orders: pd.DataFrame
    reports: ReportResult
    rejected_orders: pd.DataFrame
    metrics: dict[str, float | int]


def _configure_logging(
    pipeline_config: PipelineConfig,
) -> None:
    """Configure process-level logging."""
    logging.basicConfig(
        level=getattr(
            logging,
            pipeline_config.log_level,
            logging.INFO,
        ),
        format=pipeline_config.log_format,
    )


def _format_validation_errors(
    issues: Iterable,
) -> str:
    """Format validation issues for pipeline-level exceptions."""
    return "\n".join(
        f"- {issue.rule}: {issue.message}"
        for issue in issues
    )


def _validate_reference_data(
    customers: pd.DataFrame,
) -> None:
    """Validate reference datasets before transformation."""
    result = validate_customers(customers)

    if not result.valid:
        raise PipelineError(
            "Customer reference data validation failed:\n"
            f"{_format_validation_errors(result.issues)}"
        )


def _clean_orders(
    order_chunks,
    *,
    pipeline_config: PipelineConfig,
) -> CleaningResult:
    """Clean order chunks and enforce the rejection policy."""
    result = clean_order_chunks(order_chunks)

    rejected_count = len(result.rejected)

    if rejected_count:
        logger.warning(
            "Order cleaning rejected %d record(s).",
            rejected_count,
        )

        if pipeline_config.fail_on_invalid_records:
            raise PipelineError(
                "Order cleaning rejected "
                f"{rejected_count} record(s)."
            )

    return result


def _write_parquet_atomically(
    frame: pd.DataFrame,
    path: Path,
) -> None:
    """Write a Parquet file through a temporary file and atomic rename."""
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_name(
        f".{path.name}.tmp-{os.getpid()}",
    )

    try:
        frame.to_parquet(
            temporary_path,
            index=False,
        )
        os.replace(
            temporary_path,
            path,
        )
    except (
        OSError,
        ImportError,
        ValueError,
    ) as exc:
        try:
            temporary_path.unlink(
                missing_ok=True,
            )
        except OSError:
            logger.exception(
                "Failed to remove temporary output: %s",
                temporary_path,
            )

        raise PipelineError(
            f"Failed to write Parquet output: {path}"
        ) from exc


def _write_csv_atomically(
    frame: pd.DataFrame,
    path: Path,
) -> None:
    """Write a CSV file through a temporary file and atomic rename."""
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_name(
        f".{path.name}.tmp-{os.getpid()}",
    )

    try:
        frame.to_csv(
            temporary_path,
            index=False,
        )
        os.replace(
            temporary_path,
            path,
        )
    except (
        OSError,
        ValueError,
    ) as exc:
        try:
            temporary_path.unlink(
                missing_ok=True,
            )
        except OSError:
            logger.exception(
                "Failed to remove temporary output: %s",
                temporary_path,
            )

        raise PipelineError(
            f"Failed to write CSV output: {path}"
        ) from exc


def _write_outputs(
    reports: ReportResult,
    rejected_orders: pd.DataFrame,
    *,
    pipeline_config: PipelineConfig,
) -> None:
    """Persist all pipeline outputs."""
    if pipeline_config.atomic_writes:
        _write_parquet_atomically(
            reports.daily_sales,
            pipeline_config.daily_sales_report_path,
        )
        _write_parquet_atomically(
            reports.customer_sales,
            pipeline_config.customer_sales_report_path,
        )
        _write_parquet_atomically(
            reports.product_sales,
            pipeline_config.product_sales_report_path,
        )
        _write_csv_atomically(
            rejected_orders,
            pipeline_config.rejected_orders_path,
        )
        return

    try:
        reports.daily_sales.to_parquet(
            pipeline_config.daily_sales_report_path,
            index=False,
        )
        reports.customer_sales.to_parquet(
            pipeline_config.customer_sales_report_path,
            index=False,
        )
        reports.product_sales.to_parquet(
            pipeline_config.product_sales_report_path,
            index=False,
        )
        rejected_orders.to_csv(
            pipeline_config.rejected_orders_path,
            index=False,
        )
    except (
        OSError,
        ImportError,
        ValueError,
    ) as exc:
        raise PipelineError(
            "Failed to write pipeline outputs."
        ) from exc


def _validate_pipeline_results(
    orders: pd.DataFrame,
    customers: pd.DataFrame,
    reports: ReportResult,
    *,
    tolerance: float,
) -> None:
    """Validate cleaned data, relationships, and report reconciliation."""
    order_result = validate_orders(orders)

    if not order_result.valid:
        raise PipelineError(
            "Cleaned order validation failed:\n"
            f"{_format_validation_errors(order_result.issues)}"
        )

    customer_result = validate_customers(customers)

    if not customer_result.valid:
        raise PipelineError(
            "Customer validation failed:\n"
            f"{_format_validation_errors(customer_result.issues)}"
        )

    relationship_result = validate_order_customer_relationship(
        orders,
        customers,
    )

    if not relationship_result.valid:
        raise PipelineError(
            "Order/customer relationship validation failed:\n"
            f"{_format_validation_errors(relationship_result.issues)}"
        )

    reconciliation_result = validate_report_reconciliation(
        orders,
        reports.daily_sales,
        tolerance=tolerance,
    )

    if not reconciliation_result.valid:
        raise PipelineError(
            "Report reconciliation failed:\n"
            f"{_format_validation_errors(reconciliation_result.issues)}"
        )


def run_pipeline(
    pipeline_config: PipelineConfig = config,
) -> PipelineResult:
    """Execute ingestion, cleaning, transformation, validation, and reporting."""
    _configure_logging(pipeline_config)

    logger.info(
        "Starting e-commerce data pipeline.",
    )

    try:
        pipeline_config.ensure_directories()

        logger.info(
            "Ingesting source datasets.",
        )

        order_chunks = ingest_orders(
            pipeline_config,
        )
        customers = ingest_customers(
            pipeline_config,
        )

        # Products are part of the input contract and are ingested so the
        # pipeline fails early when the configured source is unavailable.
        ingest_products(
            pipeline_config,
        )

        _validate_reference_data(
            customers,
        )

        logger.info(
            "Cleaning order data.",
        )

        cleaning_result = _clean_orders(
            order_chunks,
            pipeline_config=pipeline_config,
        )

        orders = cleaning_result.cleaned

        logger.info(
            "Cleaned %d order records and rejected %d records.",
            len(orders),
            len(cleaning_result.rejected),
        )

        logger.info(
            "Enriching orders with customer attributes.",
        )

        enriched_orders = enrich_orders(
            orders,
            customers,
        )

        logger.info(
            "Building report bundle.",
        )

        reports = build_report_bundle(
            enriched_orders,
        )

        if pipeline_config.reconciliation_enabled:
            _validate_pipeline_results(
                enriched_orders,
                customers,
                reports,
                tolerance=pipeline_config.reconciliation_tolerance,
            )
        else:
            logger.warning(
                "Report reconciliation is disabled.",
            )

        metrics = aggregate_pipeline_metrics(
            enriched_orders,
        )

        logger.info(
            "Pipeline metrics: %s",
            metrics,
        )

        logger.info(
            "Writing pipeline outputs.",
        )

        _write_outputs(
            reports,
            cleaning_result.rejected,
            pipeline_config=pipeline_config,
        )

        logger.info(
            "Pipeline completed successfully.",
        )

        return PipelineResult(
            enriched_orders=enriched_orders,
            reports=reports,
            rejected_orders=cleaning_result.rejected,
            metrics=metrics,
        )

    except PipelineError:
        logger.exception(
            "Pipeline execution failed.",
        )
        raise
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        ImportError,
        pd.errors.PandasError,
    ) as exc:
        logger.exception(
            "Unexpected pipeline failure.",
        )
        raise PipelineError(
            "E-commerce data pipeline failed."
        ) from exc


def main() -> int:
    """Run the pipeline as a command-line entry point."""
    try:
        run_pipeline()
    except PipelineError as exc:
        logger.error(
            "%s",
            exc,
        )
        return 1

    return 0


__all__ = [
    "PipelineError",
    "PipelineResult",
    "main",
    "run_pipeline",
]


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from .aggregation import aggregate_pipeline_metrics
from .cleaning import CleaningResult, clean_order_chunks
from .config import PipelineConfig, config
from .ingestion import ingest_customers, ingest_orders, ingest_products
from .reporting import ReportResult, build_report_bundle
from .transformation import enrich_orders
from .validation import (
    validate_customers,
    validate_order_customer_relationship,
    validate_orders,
    validate_report_reconciliation,
)

logger = logging.getLogger(__name__)


class PipelineError(RuntimeError):
    """Raised when the pipeline cannot complete successfully."""


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """Results produced by a successful pipeline execution."""

    enriched_orders: pd.DataFrame
    reports: ReportResult
    rejected_orders: pd.DataFrame
    metrics: dict[str, float | int]


def _configure_logging(
    pipeline_config: PipelineConfig,
) -> None:
    """Configure process-level logging."""
    logging.basicConfig(
        level=getattr(
            logging,
            pipeline_config.log_level,
            logging.INFO,
        ),
        format=pipeline_config.log_format,
    )


def _format_validation_errors(
    issues: Iterable,
) -> str:
    """Format validation issues for pipeline-level exceptions."""
    return "\n".join(
        f"- {issue.rule}: {issue.message}"
        for issue in issues
    )


def _validate_reference_data(
    customers: pd.DataFrame,
) -> None:
    """Validate reference datasets before transformation."""
    result = validate_customers(customers)

    if not result.valid:
        raise PipelineError(
            "Customer reference data validation failed:\n"
            f"{_format_validation_errors(result.issues)}"
        )


def _clean_orders(
    order_chunks,
    *,
    pipeline_config: PipelineConfig,
) -> CleaningResult:
    """Clean order chunks and enforce the rejection policy."""
    result = clean_order_chunks(order_chunks)

    rejected_count = len(result.rejected)

    if rejected_count:
        logger.warning(
            "Order cleaning rejected %d record(s).",
            rejected_count,
        )

        if pipeline_config.fail_on_invalid_records:
            raise PipelineError(
                "Order cleaning rejected "
                f"{rejected_count} record(s)."
            )

    return result


def _write_parquet_atomically(
    frame: pd.DataFrame,
    path: Path,
) -> None:
    """Write a Parquet file through a temporary file and atomic rename."""
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_name(
        f".{path.name}.tmp-{os.getpid()}",
    )

    try:
        frame.to_parquet(
            temporary_path,
            index=False,
        )
        os.replace(
            temporary_path,
            path,
        )
    except (
        OSError,
        ImportError,
        ValueError,
    ) as exc:
        try:
            temporary_path.unlink(
                missing_ok=True,
            )
        except OSError:
            logger.exception(
                "Failed to remove temporary output: %s",
                temporary_path,
            )

        raise PipelineError(
            f"Failed to write Parquet output: {path}"
        ) from exc


def _write_csv_atomically(
    frame: pd.DataFrame,
    path: Path,
) -> None:
    """Write a CSV file through a temporary file and atomic rename."""
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_name(
        f".{path.name}.tmp-{os.getpid()}",
    )

    try:
        frame.to_csv(
            temporary_path,
            index=False,
        )
        os.replace(
            temporary_path,
            path,
        )
    except (
        OSError,
        ValueError,
    ) as exc:
        try:
            temporary_path.unlink(
                missing_ok=True,
            )
        except OSError:
            logger.exception(
                "Failed to remove temporary output: %s",
                temporary_path,
            )

        raise PipelineError(
            f"Failed to write CSV output: {path}"
        ) from exc


def _write_outputs(
    reports: ReportResult,
    rejected_orders: pd.DataFrame,
    *,
    pipeline_config: PipelineConfig,
) -> None:
    """Persist all pipeline outputs."""
    if pipeline_config.atomic_writes:
        _write_parquet_atomically(
            reports.daily_sales,
            pipeline_config.daily_sales_report_path,
        )
        _write_parquet_atomically(
            reports.customer_sales,
            pipeline_config.customer_sales_report_path,
        )
        _write_parquet_atomically(
            reports.product_sales,
            pipeline_config.product_sales_report_path,
        )
        _write_csv_atomically(
            rejected_orders,
            pipeline_config.rejected_orders_path,
        )
        return

    try:
        reports.daily_sales.to_parquet(
            pipeline_config.daily_sales_report_path,
            index=False,
        )
        reports.customer_sales.to_parquet(
            pipeline_config.customer_sales_report_path,
            index=False,
        )
        reports.product_sales.to_parquet(
            pipeline_config.product_sales_report_path,
            index=False,
        )
        rejected_orders.to_csv(
            pipeline_config.rejected_orders_path,
            index=False,
        )
    except (
        OSError,
        ImportError,
        ValueError,
    ) as exc:
        raise PipelineError(
            "Failed to write pipeline outputs."
        ) from exc


def _validate_pipeline_results(
    orders: pd.DataFrame,
    customers: pd.DataFrame,
    reports: ReportResult,
    *,
    tolerance: float,
) -> None:
    """Validate cleaned data, relationships, and report reconciliation."""
    order_result = validate_orders(orders)

    if not order_result.valid:
        raise PipelineError(
            "Cleaned order validation failed:\n"
            f"{_format_validation_errors(order_result.issues)}"
        )

    customer_result = validate_customers(customers)

    if not customer_result.valid:
        raise PipelineError(
            "Customer validation failed:\n"
            f"{_format_validation_errors(customer_result.issues)}"
        )

    relationship_result = validate_order_customer_relationship(
        orders,
        customers,
    )

    if not relationship_result.valid:
        raise PipelineError(
            "Order/customer relationship validation failed:\n"
            f"{_format_validation_errors(relationship_result.issues)}"
        )

    reconciliation_result = validate_report_reconciliation(
        orders,
        reports.daily_sales,
        tolerance=tolerance,
    )

    if not reconciliation_result.valid:
        raise PipelineError(
            "Report reconciliation failed:\n"
            f"{_format_validation_errors(reconciliation_result.issues)}"
        )


def run_pipeline(
    pipeline_config: PipelineConfig = config,
) -> PipelineResult:
    """Execute ingestion, cleaning, transformation, validation, and reporting."""
    _configure_logging(pipeline_config)

    logger.info(
        "Starting e-commerce data pipeline.",
    )

    try:
        pipeline_config.ensure_directories()

        logger.info(
            "Ingesting source datasets.",
        )

        order_chunks = ingest_orders(
            pipeline_config,
        )
        customers = ingest_customers(
            pipeline_config,
        )

        # Products are part of the input contract and are ingested so the
        # pipeline fails early when the configured source is unavailable.
        ingest_products(
            pipeline_config,
        )

        _validate_reference_data(
            customers,
        )

        logger.info(
            "Cleaning order data.",
        )

        cleaning_result = _clean_orders(
            order_chunks,
            pipeline_config=pipeline_config,
        )

        orders = cleaning_result.cleaned

        logger.info(
            "Cleaned %d order records and rejected %d records.",
            len(orders),
            len(cleaning_result.rejected),
        )

        logger.info(
            "Enriching orders with customer attributes.",
        )

        enriched_orders = enrich_orders(
            orders,
            customers,
        )

        logger.info(
            "Building report bundle.",
        )

        reports = build_report_bundle(
            enriched_orders,
        )

        if pipeline_config.reconciliation_enabled:
            _validate_pipeline_results(
                enriched_orders,
                customers,
                reports,
                tolerance=pipeline_config.reconciliation_tolerance,
            )
        else:
            logger.warning(
                "Report reconciliation is disabled.",
            )

        metrics = aggregate_pipeline_metrics(
            enriched_orders,
        )

        logger.info(
            "Pipeline metrics: %s",
            metrics,
        )

        logger.info(
            "Writing pipeline outputs.",
        )

        _write_outputs(
            reports,
            cleaning_result.rejected,
            pipeline_config=pipeline_config,
        )

        logger.info(
            "Pipeline completed successfully.",
        )

        return PipelineResult(
            enriched_orders=enriched_orders,
            reports=reports,
            rejected_orders=cleaning_result.rejected,
            metrics=metrics,
        )

    except PipelineError:
        logger.exception(
            "Pipeline execution failed.",
        )
        raise
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        ImportError,
        pd.errors.PandasError,
    ) as exc:
        logger.exception(
            "Unexpected pipeline failure.",
        )
        raise PipelineError(
            "E-commerce data pipeline failed."
        ) from exc


def main() -> int:
    """Run the pipeline as a command-line entry point."""
    try:
        run_pipeline()
    except PipelineError as exc:
        logger.error(
            "%s",
            exc,
        )
        return 1

    return 0


__all__ = [
    "PipelineError",
    "PipelineResult",
    "main",
    "run_pipeline",
]


if __name__ == "__main__":
    raise SystemExit(main())