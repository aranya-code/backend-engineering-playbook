from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(
    os.getenv(
        "ECOMMERCE_PIPELINE_ROOT",
        Path(__file__).resolve().parents[1],
    )
).resolve()

DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"
CONFIG_DIR = PROJECT_ROOT / "config"


def _env_int(name: str, default: int) -> int:
    """Read a positive integer from an environment variable."""
    value = os.getenv(name)

    if value is None:
        return default

    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc

    if parsed <= 0:
        raise ValueError(f"{name} must be greater than zero")

    return parsed


def _env_float(name: str, default: float) -> float:
    """Read a non-negative float from an environment variable."""
    value = os.getenv(name)

    if value is None:
        return default

    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc

    if parsed < 0:
        raise ValueError(f"{name} must be non-negative")

    return parsed


def _env_bool(name: str, default: bool) -> bool:
    """Read a boolean value from an environment variable."""
    value = os.getenv(name)

    if value is None:
        return default

    normalized = value.strip().lower()

    if normalized in {"1", "true", "yes", "on"}:
        return True

    if normalized in {"0", "false", "no", "off"}:
        return False

    raise ValueError(
        f"{name} must be one of: "
        "1, 0, true, false, yes, no, on, off"
    )


@dataclass(frozen=True, slots=True)
class PipelineConfig:
    """Runtime configuration for the e-commerce data pipeline."""

    raw_data_dir: Path = DATA_DIR / "raw"
    staging_data_dir: Path = DATA_DIR / "staging"
    processed_data_dir: Path = DATA_DIR / "processed"
    reports_dir: Path = REPORTS_DIR

    orders_file: str = "orders.csv"
    customers_file: str = "customers.csv"
    products_file: str = "products.csv"

    daily_sales_report_file: str = "daily_sales_report.parquet"
    customer_sales_report_file: str = "customer_sales_report.parquet"
    product_sales_report_file: str = "product_sales_report.parquet"
    rejected_orders_file: str = "rejected_orders.csv"

    csv_chunksize: int = _env_int(
        "PANDAS_CSV_CHUNKSIZE",
        100_000,
    )

    report_timezone: str = os.getenv(
        "REPORT_TIMEZONE",
        "UTC",
    )

    fail_on_invalid_records: bool = _env_bool(
        "FAIL_ON_INVALID_RECORDS",
        False,
    )

    create_directories: bool = _env_bool(
        "CREATE_PIPELINE_DIRECTORIES",
        True,
    )

    atomic_writes: bool = _env_bool(
        "ATOMIC_PIPELINE_WRITES",
        True,
    )

    reconciliation_enabled: bool = _env_bool(
        "PIPELINE_RECONCILIATION_ENABLED",
        True,
    )

    reconciliation_tolerance: float = _env_float(
        "PIPELINE_RECONCILIATION_TOLERANCE",
        0.01,
    )

    log_level: str = os.getenv(
        "LOG_LEVEL",
        "INFO",
    ).upper()

    log_format: str = os.getenv(
        "LOG_FORMAT",
        "%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    @property
    def orders_path(self) -> Path:
        """Return the configured orders input path."""
        return self.raw_data_dir / self.orders_file

    @property
    def customers_path(self) -> Path:
        """Return the configured customers input path."""
        return self.raw_data_dir / self.customers_file

    @property
    def products_path(self) -> Path:
        """Return the configured products input path."""
        return self.raw_data_dir / self.products_file

    @property
    def daily_sales_report_path(self) -> Path:
        """Return the configured daily sales report path."""
        return self.reports_dir / self.daily_sales_report_file

    @property
    def customer_sales_report_path(self) -> Path:
        """Return the configured customer sales report path."""
        return self.reports_dir / self.customer_sales_report_file

    @property
    def product_sales_report_path(self) -> Path:
        """Return the configured product sales report path."""
        return self.reports_dir / self.product_sales_report_file

    @property
    def rejected_orders_path(self) -> Path:
        """Return the configured rejected-order output path."""
        return self.reports_dir / self.rejected_orders_file

    def ensure_directories(self) -> None:
        """Create required pipeline directories when enabled."""
        if not self.create_directories:
            return

        for directory in (
            self.raw_data_dir,
            self.staging_data_dir,
            self.processed_data_dir,
            self.reports_dir,
        ):
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )


config = PipelineConfig()


__all__ = [
    "CONFIG_DIR",
    "DATA_DIR",
    "PROJECT_ROOT",
    "REPORTS_DIR",
    "PipelineConfig",
    "config",
]

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(
    os.getenv(
        "ECOMMERCE_PIPELINE_ROOT",
        Path(__file__).resolve().parents[1],
    )
).resolve()

DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"
CONFIG_DIR = PROJECT_ROOT / "config"


def _env_int(name: str, default: int) -> int:
    """Read a positive integer from an environment variable."""
    value = os.getenv(name)

    if value is None:
        return default

    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc

    if parsed <= 0:
        raise ValueError(f"{name} must be greater than zero")

    return parsed


def _env_float(name: str, default: float) -> float:
    """Read a non-negative float from an environment variable."""
    value = os.getenv(name)

    if value is None:
        return default

    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc

    if parsed < 0:
        raise ValueError(f"{name} must be non-negative")

    return parsed


def _env_bool(name: str, default: bool) -> bool:
    """Read a boolean value from an environment variable."""
    value = os.getenv(name)

    if value is None:
        return default

    normalized = value.strip().lower()

    if normalized in {"1", "true", "yes", "on"}:
        return True

    if normalized in {"0", "false", "no", "off"}:
        return False

    raise ValueError(
        f"{name} must be one of: "
        "1, 0, true, false, yes, no, on, off"
    )


@dataclass(frozen=True, slots=True)
class PipelineConfig:
    """Runtime configuration for the e-commerce data pipeline."""

    raw_data_dir: Path = DATA_DIR / "raw"
    staging_data_dir: Path = DATA_DIR / "staging"
    processed_data_dir: Path = DATA_DIR / "processed"
    reports_dir: Path = REPORTS_DIR

    orders_file: str = "orders.csv"
    customers_file: str = "customers.csv"
    products_file: str = "products.csv"

    daily_sales_report_file: str = "daily_sales_report.parquet"
    customer_sales_report_file: str = "customer_sales_report.parquet"
    product_sales_report_file: str = "product_sales_report.parquet"
    rejected_orders_file: str = "rejected_orders.csv"

    csv_chunksize: int = _env_int(
        "PANDAS_CSV_CHUNKSIZE",
        100_000,
    )

    report_timezone: str = os.getenv(
        "REPORT_TIMEZONE",
        "UTC",
    )

    fail_on_invalid_records: bool = _env_bool(
        "FAIL_ON_INVALID_RECORDS",
        False,
    )

    create_directories: bool = _env_bool(
        "CREATE_PIPELINE_DIRECTORIES",
        True,
    )

    atomic_writes: bool = _env_bool(
        "ATOMIC_PIPELINE_WRITES",
        True,
    )

    reconciliation_enabled: bool = _env_bool(
        "PIPELINE_RECONCILIATION_ENABLED",
        True,
    )

    reconciliation_tolerance: float = _env_float(
        "PIPELINE_RECONCILIATION_TOLERANCE",
        0.01,
    )

    log_level: str = os.getenv(
        "LOG_LEVEL",
        "INFO",
    ).upper()

    log_format: str = os.getenv(
        "LOG_FORMAT",
        "%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    @property
    def orders_path(self) -> Path:
        """Return the configured orders input path."""
        return self.raw_data_dir / self.orders_file

    @property
    def customers_path(self) -> Path:
        """Return the configured customers input path."""
        return self.raw_data_dir / self.customers_file

    @property
    def products_path(self) -> Path:
        """Return the configured products input path."""
        return self.raw_data_dir / self.products_file

    @property
    def daily_sales_report_path(self) -> Path:
        """Return the configured daily sales report path."""
        return self.reports_dir / self.daily_sales_report_file

    @property
    def customer_sales_report_path(self) -> Path:
        """Return the configured customer sales report path."""
        return self.reports_dir / self.customer_sales_report_file

    @property
    def product_sales_report_path(self) -> Path:
        """Return the configured product sales report path."""
        return self.reports_dir / self.product_sales_report_file

    @property
    def rejected_orders_path(self) -> Path:
        """Return the configured rejected-order output path."""
        return self.reports_dir / self.rejected_orders_file

    def ensure_directories(self) -> None:
        """Create required pipeline directories when enabled."""
        if not self.create_directories:
            return

        for directory in (
            self.raw_data_dir,
            self.staging_data_dir,
            self.processed_data_dir,
            self.reports_dir,
        ):
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )


config = PipelineConfig()


__all__ = [
    "CONFIG_DIR",
    "DATA_DIR",
    "PROJECT_ROOT",
    "REPORTS_DIR",
    "PipelineConfig",
    "config",
]