from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


PROJECT_ROOT = Path(
    os.getenv(
        "LARGE_DATASET_PIPELINE_ROOT",
        Path(__file__).resolve().parents[1],
    )
).resolve()

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
STAGING_DATA_DIR = DATA_DIR / "staging"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
BENCHMARKS_DIR = PROJECT_ROOT / "benchmarks"
CONFIG_DIR = PROJECT_ROOT / "config"


def _env_int(
    name: str,
    default: int,
    *,
    minimum: int | None = None,
) -> int:
    """Read and validate an integer environment variable."""
    value = os.getenv(name)

    if value is None:
        return default

    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc

    if minimum is not None and parsed < minimum:
        raise ValueError(
            f"{name} must be greater than or equal to {minimum}"
        )

    return parsed


def _env_float(
    name: str,
    default: float,
    *,
    minimum: float | None = None,
) -> float:
    """Read and validate a floating-point environment variable."""
    value = os.getenv(name)

    if value is None:
        return default

    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc

    if minimum is not None and parsed < minimum:
        raise ValueError(
            f"{name} must be greater than or equal to {minimum}"
        )

    return parsed


def _env_bool(
    name: str,
    default: bool,
) -> bool:
    """Read and validate a boolean environment variable."""
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


def _env_str(
    name: str,
    default: str,
) -> str:
    """Read a required string configuration value."""
    value = os.getenv(name)

    if value is None:
        return default

    normalized = value.strip()

    if not normalized:
        raise ValueError(f"{name} cannot be empty")

    return normalized


def _env_optional_str(
    name: str,
) -> str | None:
    """Read an optional string environment variable."""
    value = os.getenv(name)

    if value is None:
        return None

    normalized = value.strip()
    return normalized or None


def _env_path(
    name: str,
    default: Path,
) -> Path:
    """Read a filesystem path from an environment variable."""
    value = os.getenv(name)

    if value is None:
        return default

    normalized = value.strip()

    if not normalized:
        raise ValueError(f"{name} cannot be empty")

    return Path(normalized).expanduser().resolve()


def _env_csv(
    name: str,
    default: tuple[str, ...],
) -> tuple[str, ...]:
    """Read a comma-separated tuple of values."""
    value = os.getenv(name)

    if value is None:
        return default

    values = tuple(
        item.strip()
        for item in value.split(",")
        if item.strip()
    )

    return values


@dataclass(frozen=True, slots=True)
class PipelineConfig:
    """Runtime configuration for the large dataset processing pipeline."""

    input_file: Path = field(
        default_factory=lambda: _env_path(
            "PIPELINE_INPUT_FILE",
            RAW_DATA_DIR / "input.csv",
        )
    )

    output_file: Path = field(
        default_factory=lambda: _env_path(
            "PIPELINE_OUTPUT_FILE",
            PROCESSED_DATA_DIR / "processed.parquet",
        )
    )

    rejected_records_file: Path = field(
        default_factory=lambda: _env_path(
            "PIPELINE_REJECTED_RECORDS_FILE",
            REPORTS_DIR / "rejected_records.parquet",
        )
    )

    processing_report_file: Path = field(
        default_factory=lambda: _env_path(
            "PIPELINE_PROCESSING_REPORT_FILE",
            REPORTS_DIR / "processing_report.parquet",
        )
    )

    data_dir: Path = DATA_DIR
    raw_data_dir: Path = RAW_DATA_DIR
    staging_data_dir: Path = STAGING_DATA_DIR
    processed_data_dir: Path = PROCESSED_DATA_DIR
    reports_dir: Path = REPORTS_DIR
    benchmarks_dir: Path = BENCHMARKS_DIR

    file_format: str = field(
        default_factory=lambda: _env_str(
            "PIPELINE_FILE_FORMAT",
            "csv",
        ).lower()
    )

    output_format: str = field(
        default_factory=lambda: _env_str(
            "PIPELINE_OUTPUT_FORMAT",
            "parquet",
        ).lower()
    )

    chunk_size: int = field(
        default_factory=lambda: _env_int(
            "PIPELINE_CHUNK_SIZE",
            100_000,
            minimum=1,
        )
    )

    benchmark_chunk_size: int = field(
        default_factory=lambda: _env_int(
            "PIPELINE_BENCHMARK_CHUNK_SIZE",
            250_000,
            minimum=1,
        )
    )

    max_rows: int | None = field(
        default_factory=lambda: (
            _env_int(
                "PIPELINE_MAX_ROWS",
                0,
                minimum=0,
            )
            or None
        )
    )

    min_chunk_size: int = field(
        default_factory=lambda: _env_int(
            "PIPELINE_MIN_CHUNK_SIZE",
            10_000,
            minimum=1,
        )
    )

    max_chunk_size: int = field(
        default_factory=lambda: _env_int(
            "PIPELINE_MAX_CHUNK_SIZE",
            1_000_000,
            minimum=1,
        )
    )

    parquet_compression: str = field(
        default_factory=lambda: _env_str(
            "PIPELINE_PARQUET_COMPRESSION",
            "snappy",
        ).lower()
    )

    csv_encoding: str = field(
        default_factory=lambda: _env_str(
            "PIPELINE_CSV_ENCODING",
            "utf-8",
        )
    )

    csv_separator: str = field(
        default_factory=lambda: _env_str(
            "PIPELINE_CSV_SEPARATOR",
            ",",
        )
    )

    null_value: str = field(
        default_factory=lambda: os.getenv(
            "PIPELINE_NULL_VALUE",
            "",
        )
    )

    timestamp_timezone: str = field(
        default_factory=lambda: _env_str(
            "PIPELINE_TIMESTAMP_TIMEZONE",
            "UTC",
        )
    )

    timestamp_columns: tuple[str, ...] = field(
        default_factory=lambda: _env_csv(
            "PIPELINE_TIMESTAMP_COLUMNS",
            (
                "created_at",
                "updated_at",
                "timestamp",
            ),
        )
    )

    numeric_columns: tuple[str, ...] = field(
        default_factory=lambda: _env_csv(
            "PIPELINE_NUMERIC_COLUMNS",
            (
                "amount",
                "quantity",
                "price",
            ),
        )
    )

    identifier_columns: tuple[str, ...] = field(
        default_factory=lambda: _env_csv(
            "PIPELINE_IDENTIFIER_COLUMNS",
            (
                "id",
                "order_id",
                "customer_id",
                "product_id",
                "transaction_id",
            ),
        )
    )

    required_columns: tuple[str, ...] = field(
        default_factory=lambda: _env_csv(
            "PIPELINE_REQUIRED_COLUMNS",
            (),
        )
    )

    categorical_columns: tuple[str, ...] = field(
        default_factory=lambda: _env_csv(
            "PIPELINE_CATEGORICAL_COLUMNS",
            (
                "status",
                "region",
                "category",
            ),
        )
    )

    usecols: tuple[str, ...] = field(
        default_factory=lambda: _env_csv(
            "PIPELINE_USECOLS",
            (),
        )
    )

    low_memory: bool = field(
        default_factory=lambda: _env_bool(
            "PIPELINE_LOW_MEMORY",
            True,
        )
    )

    memory_map: bool = field(
        default_factory=lambda: _env_bool(
            "PIPELINE_MEMORY_MAP",
            True,
        )
    )

    infer_datetime_format: bool = field(
        default_factory=lambda: _env_bool(
            "PIPELINE_INFER_DATETIME_FORMAT",
            True,
        )
    )

    parse_dates: bool = field(
        default_factory=lambda: _env_bool(
            "PIPELINE_PARSE_DATES",
            False,
        )
    )

    drop_invalid_records: bool = field(
        default_factory=lambda: _env_bool(
            "PIPELINE_DROP_INVALID_RECORDS",
            False,
        )
    )

    drop_duplicate_records: bool = field(
        default_factory=lambda: _env_bool(
            "PIPELINE_DROP_DUPLICATES",
            True,
        )
    )

    fail_on_schema_error: bool = field(
        default_factory=lambda: _env_bool(
            "PIPELINE_FAIL_ON_SCHEMA_ERROR",
            True,
        )
    )

    fail_on_validation_error: bool = field(
        default_factory=lambda: _env_bool(
            "PIPELINE_FAIL_ON_VALIDATION_ERROR",
            True,
        )
    )

    create_directories: bool = field(
        default_factory=lambda: _env_bool(
            "PIPELINE_CREATE_DIRECTORIES",
            True,
        )
    )

    atomic_writes: bool = field(
        default_factory=lambda: _env_bool(
            "PIPELINE_ATOMIC_WRITES",
            True,
        )
    )

    checkpointing_enabled: bool = field(
        default_factory=lambda: _env_bool(
            "PIPELINE_CHECKPOINTING_ENABLED",
            True,
        )
    )

    checkpoint_interval_chunks: int = field(
        default_factory=lambda: _env_int(
            "PIPELINE_CHECKPOINT_INTERVAL_CHUNKS",
            10,
            minimum=1,
        )
    )

    checkpoint_dir: Path = field(
        default_factory=lambda: _env_path(
            "PIPELINE_CHECKPOINT_DIR",
            STAGING_DATA_DIR / "checkpoints",
        )
    )

    resume_enabled: bool = field(
        default_factory=lambda: _env_bool(
            "PIPELINE_RESUME_ENABLED",
            False,
        )
    )

    preserve_chunk_order: bool = field(
        default_factory=lambda: _env_bool(
            "PIPELINE_PRESERVE_CHUNK_ORDER",
            True,
        )
    )

    target_memory_mb: int = field(
        default_factory=lambda: _env_int(
            "PIPELINE_TARGET_MEMORY_MB",
            1024,
            minimum=128,
        )
    )

    memory_warning_threshold_percent: float = field(
        default_factory=lambda: _env_float(
            "PIPELINE_MEMORY_WARNING_THRESHOLD_PERCENT",
            80.0,
            minimum=1.0,
        )
    )

    benchmark_enabled: bool = field(
        default_factory=lambda: _env_bool(
            "PIPELINE_BENCHMARK_ENABLED",
            False,
        )
    )

    benchmark_repetitions: int = field(
        default_factory=lambda: _env_int(
            "PIPELINE_BENCHMARK_REPETITIONS",
            3,
            minimum=1,
        )
    )

    log_level: str = field(
        default_factory=lambda: _env_str(
            "LOG_LEVEL",
            "INFO",
        ).upper()
    )

    log_format: str = field(
        default_factory=lambda: os.getenv(
            "LOG_FORMAT",
            "%(asctime)s %(levelname)s %(name)s %(message)s",
        )
    )

    pipeline_name: str = field(
        default_factory=lambda: _env_str(
            "PIPELINE_NAME",
            "large_dataset_processing",
        )
    )

    @property
    def input_suffix(self) -> str:
        """Return the normalized input file suffix."""
        return self.input_file.suffix.lower()

    @property
    def output_suffix(self) -> str:
        """Return the normalized output file suffix."""
        return self.output_file.suffix.lower()

    @property
    def effective_chunk_size(self) -> int:
        """Return a chunk size constrained by configured safety bounds."""
        return max(
            self.min_chunk_size,
            min(
                self.chunk_size,
                self.max_chunk_size,
            ),
        )

    @property
    def csv_read_kwargs(self) -> dict[str, object]:
        """Return keyword arguments for Pandas CSV chunked reads."""
        kwargs: dict[str, object] = {
            "chunksize": self.effective_chunk_size,
            "sep": self.csv_separator,
            "encoding": self.csv_encoding,
            "low_memory": self.low_memory,
        }

        if self.usecols:
            kwargs["usecols"] = list(self.usecols)

        if self.null_value:
            kwargs["na_values"] = [self.null_value]

        return kwargs

    @property
    def parquet_write_kwargs(self) -> dict[str, object]:
        """Return keyword arguments for Parquet writes."""
        return {
            "compression": self.parquet_compression,
            "index": False,
        }

    def ensure_directories(self) -> None:
        """Create directories required by the pipeline."""
        if not self.create_directories:
            return

        for directory in (
            self.data_dir,
            self.raw_data_dir,
            self.staging_data_dir,
            self.processed_data_dir,
            self.reports_dir,
            self.benchmarks_dir,
            self.checkpoint_dir,
        ):
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )

    def validate(self) -> None:
        """Validate configuration combinations and operational constraints."""
        if self.min_chunk_size > self.max_chunk_size:
            raise ValueError(
                "min_chunk_size cannot be greater than max_chunk_size"
            )

        if self.benchmark_chunk_size <= 0:
            raise ValueError(
                "benchmark_chunk_size must be greater than zero"
            )

        if self.target_memory_mb < 128:
            raise ValueError(
                "target_memory_mb must be at least 128 MB"
            )

        if not 1.0 <= self.memory_warning_threshold_percent <= 100.0:
            raise ValueError(
                "memory_warning_threshold_percent must be between 1 and 100"
            )

        if self.file_format not in {
            "csv",
            "parquet",
            "json",
        }:
            raise ValueError(
                "file_format must be one of: csv, parquet, json"
            )

        if self.output_format not in {
            "csv",
            "parquet",
            "json",
        }:
            raise ValueError(
                "output_format must be one of: csv, parquet, json"
            )

        if self.file_format == "csv" and len(self.csv_separator) == 0:
            raise ValueError(
                "csv_separator cannot be empty"
            )

        if self.output_format == "parquet" and not self.output_file.suffix:
            raise ValueError(
                "output_file must have a file extension for Parquet output"
            )

        if self.resume_enabled and not self.checkpointing_enabled:
            raise ValueError(
                "resume_enabled requires checkpointing_enabled"
            )

        if self.checkpoint_interval_chunks <= 0:
            raise ValueError(
                "checkpoint_interval_chunks must be greater than zero"
            )

        if self.benchmark_repetitions <= 0:
            raise ValueError(
                "benchmark_repetitions must be greater than zero"
            )


config = PipelineConfig()
config.validate()


__all__ = [
    "BENCHMARKS_DIR",
    "CONFIG_DIR",
    "DATA_DIR",
    "PIPELINE_ROOT" if False else "PROJECT_ROOT",
    "RAW_DATA_DIR",
    "REPORTS_DIR",
    "STAGING_DATA_DIR",
    "PROCESSED_DATA_DIR",
    "PipelineConfig",
    "config",
]

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


PROJECT_ROOT = Path(
    os.getenv(
        "LARGE_DATASET_PIPELINE_ROOT",
        Path(__file__).resolve().parents[1],
    )
).resolve()

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
STAGING_DATA_DIR = DATA_DIR / "staging"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
BENCHMARKS_DIR = PROJECT_ROOT / "benchmarks"
CONFIG_DIR = PROJECT_ROOT / "config"


def _env_int(
    name: str,
    default: int,
    *,
    minimum: int | None = None,
) -> int:
    """Read and validate an integer environment variable."""
    value = os.getenv(name)

    if value is None:
        return default

    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc

    if minimum is not None and parsed < minimum:
        raise ValueError(
            f"{name} must be greater than or equal to {minimum}"
        )

    return parsed


def _env_float(
    name: str,
    default: float,
    *,
    minimum: float | None = None,
) -> float:
    """Read and validate a floating-point environment variable."""
    value = os.getenv(name)

    if value is None:
        return default

    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc

    if minimum is not None and parsed < minimum:
        raise ValueError(
            f"{name} must be greater than or equal to {minimum}"
        )

    return parsed


def _env_bool(
    name: str,
    default: bool,
) -> bool:
    """Read and validate a boolean environment variable."""
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


def _env_str(
    name: str,
    default: str,
) -> str:
    """Read a required string configuration value."""
    value = os.getenv(name)

    if value is None:
        return default

    normalized = value.strip()

    if not normalized:
        raise ValueError(f"{name} cannot be empty")

    return normalized


def _env_optional_str(
    name: str,
) -> str | None:
    """Read an optional string environment variable."""
    value = os.getenv(name)

    if value is None:
        return None

    normalized = value.strip()
    return normalized or None


def _env_path(
    name: str,
    default: Path,
) -> Path:
    """Read a filesystem path from an environment variable."""
    value = os.getenv(name)

    if value is None:
        return default

    normalized = value.strip()

    if not normalized:
        raise ValueError(f"{name} cannot be empty")

    return Path(normalized).expanduser().resolve()


def _env_csv(
    name: str,
    default: tuple[str, ...],
) -> tuple[str, ...]:
    """Read a comma-separated tuple of values."""
    value = os.getenv(name)

    if value is None:
        return default

    values = tuple(
        item.strip()
        for item in value.split(",")
        if item.strip()
    )

    return values


@dataclass(frozen=True, slots=True)
class PipelineConfig:
    """Runtime configuration for the large dataset processing pipeline."""

    input_file: Path = field(
        default_factory=lambda: _env_path(
            "PIPELINE_INPUT_FILE",
            RAW_DATA_DIR / "input.csv",
        )
    )

    output_file: Path = field(
        default_factory=lambda: _env_path(
            "PIPELINE_OUTPUT_FILE",
            PROCESSED_DATA_DIR / "processed.parquet",
        )
    )

    rejected_records_file: Path = field(
        default_factory=lambda: _env_path(
            "PIPELINE_REJECTED_RECORDS_FILE",
            REPORTS_DIR / "rejected_records.parquet",
        )
    )

    processing_report_file: Path = field(
        default_factory=lambda: _env_path(
            "PIPELINE_PROCESSING_REPORT_FILE",
            REPORTS_DIR / "processing_report.parquet",
        )
    )

    data_dir: Path = DATA_DIR
    raw_data_dir: Path = RAW_DATA_DIR
    staging_data_dir: Path = STAGING_DATA_DIR
    processed_data_dir: Path = PROCESSED_DATA_DIR
    reports_dir: Path = REPORTS_DIR
    benchmarks_dir: Path = BENCHMARKS_DIR

    file_format: str = field(
        default_factory=lambda: _env_str(
            "PIPELINE_FILE_FORMAT",
            "csv",
        ).lower()
    )

    output_format: str = field(
        default_factory=lambda: _env_str(
            "PIPELINE_OUTPUT_FORMAT",
            "parquet",
        ).lower()
    )

    chunk_size: int = field(
        default_factory=lambda: _env_int(
            "PIPELINE_CHUNK_SIZE",
            100_000,
            minimum=1,
        )
    )

    benchmark_chunk_size: int = field(
        default_factory=lambda: _env_int(
            "PIPELINE_BENCHMARK_CHUNK_SIZE",
            250_000,
            minimum=1,
        )
    )

    max_rows: int | None = field(
        default_factory=lambda: (
            _env_int(
                "PIPELINE_MAX_ROWS",
                0,
                minimum=0,
            )
            or None
        )
    )

    min_chunk_size: int = field(
        default_factory=lambda: _env_int(
            "PIPELINE_MIN_CHUNK_SIZE",
            10_000,
            minimum=1,
        )
    )

    max_chunk_size: int = field(
        default_factory=lambda: _env_int(
            "PIPELINE_MAX_CHUNK_SIZE",
            1_000_000,
            minimum=1,
        )
    )

    parquet_compression: str = field(
        default_factory=lambda: _env_str(
            "PIPELINE_PARQUET_COMPRESSION",
            "snappy",
        ).lower()
    )

    csv_encoding: str = field(
        default_factory=lambda: _env_str(
            "PIPELINE_CSV_ENCODING",
            "utf-8",
        )
    )

    csv_separator: str = field(
        default_factory=lambda: _env_str(
            "PIPELINE_CSV_SEPARATOR",
            ",",
        )
    )

    null_value: str = field(
        default_factory=lambda: os.getenv(
            "PIPELINE_NULL_VALUE",
            "",
        )
    )

    timestamp_timezone: str = field(
        default_factory=lambda: _env_str(
            "PIPELINE_TIMESTAMP_TIMEZONE",
            "UTC",
        )
    )

    timestamp_columns: tuple[str, ...] = field(
        default_factory=lambda: _env_csv(
            "PIPELINE_TIMESTAMP_COLUMNS",
            (
                "created_at",
                "updated_at",
                "timestamp",
            ),
        )
    )

    numeric_columns: tuple[str, ...] = field(
        default_factory=lambda: _env_csv(
            "PIPELINE_NUMERIC_COLUMNS",
            (
                "amount",
                "quantity",
                "price",
            ),
        )
    )

    identifier_columns: tuple[str, ...] = field(
        default_factory=lambda: _env_csv(
            "PIPELINE_IDENTIFIER_COLUMNS",
            (
                "id",
                "order_id",
                "customer_id",
                "product_id",
                "transaction_id",
            ),
        )
    )

    required_columns: tuple[str, ...] = field(
        default_factory=lambda: _env_csv(
            "PIPELINE_REQUIRED_COLUMNS",
            (),
        )
    )

    categorical_columns: tuple[str, ...] = field(
        default_factory=lambda: _env_csv(
            "PIPELINE_CATEGORICAL_COLUMNS",
            (
                "status",
                "region",
                "category",
            ),
        )
    )

    usecols: tuple[str, ...] = field(
        default_factory=lambda: _env_csv(
            "PIPELINE_USECOLS",
            (),
        )
    )

    low_memory: bool = field(
        default_factory=lambda: _env_bool(
            "PIPELINE_LOW_MEMORY",
            True,
        )
    )

    memory_map: bool = field(
        default_factory=lambda: _env_bool(
            "PIPELINE_MEMORY_MAP",
            True,
        )
    )

    infer_datetime_format: bool = field(
        default_factory=lambda: _env_bool(
            "PIPELINE_INFER_DATETIME_FORMAT",
            True,
        )
    )

    parse_dates: bool = field(
        default_factory=lambda: _env_bool(
            "PIPELINE_PARSE_DATES",
            False,
        )
    )

    drop_invalid_records: bool = field(
        default_factory=lambda: _env_bool(
            "PIPELINE_DROP_INVALID_RECORDS",
            False,
        )
    )

    drop_duplicate_records: bool = field(
        default_factory=lambda: _env_bool(
            "PIPELINE_DROP_DUPLICATES",
            True,
        )
    )

    fail_on_schema_error: bool = field(
        default_factory=lambda: _env_bool(
            "PIPELINE_FAIL_ON_SCHEMA_ERROR",
            True,
        )
    )

    fail_on_validation_error: bool = field(
        default_factory=lambda: _env_bool(
            "PIPELINE_FAIL_ON_VALIDATION_ERROR",
            True,
        )
    )

    create_directories: bool = field(
        default_factory=lambda: _env_bool(
            "PIPELINE_CREATE_DIRECTORIES",
            True,
        )
    )

    atomic_writes: bool = field(
        default_factory=lambda: _env_bool(
            "PIPELINE_ATOMIC_WRITES",
            True,
        )
    )

    checkpointing_enabled: bool = field(
        default_factory=lambda: _env_bool(
            "PIPELINE_CHECKPOINTING_ENABLED",
            True,
        )
    )

    checkpoint_interval_chunks: int = field(
        default_factory=lambda: _env_int(
            "PIPELINE_CHECKPOINT_INTERVAL_CHUNKS",
            10,
            minimum=1,
        )
    )

    checkpoint_dir: Path = field(
        default_factory=lambda: _env_path(
            "PIPELINE_CHECKPOINT_DIR",
            STAGING_DATA_DIR / "checkpoints",
        )
    )

    resume_enabled: bool = field(
        default_factory=lambda: _env_bool(
            "PIPELINE_RESUME_ENABLED",
            False,
        )
    )

    preserve_chunk_order: bool = field(
        default_factory=lambda: _env_bool(
            "PIPELINE_PRESERVE_CHUNK_ORDER",
            True,
        )
    )

    target_memory_mb: int = field(
        default_factory=lambda: _env_int(
            "PIPELINE_TARGET_MEMORY_MB",
            1024,
            minimum=128,
        )
    )

    memory_warning_threshold_percent: float = field(
        default_factory=lambda: _env_float(
            "PIPELINE_MEMORY_WARNING_THRESHOLD_PERCENT",
            80.0,
            minimum=1.0,
        )
    )

    benchmark_enabled: bool = field(
        default_factory=lambda: _env_bool(
            "PIPELINE_BENCHMARK_ENABLED",
            False,
        )
    )

    benchmark_repetitions: int = field(
        default_factory=lambda: _env_int(
            "PIPELINE_BENCHMARK_REPETITIONS",
            3,
            minimum=1,
        )
    )

    log_level: str = field(
        default_factory=lambda: _env_str(
            "LOG_LEVEL",
            "INFO",
        ).upper()
    )

    log_format: str = field(
        default_factory=lambda: os.getenv(
            "LOG_FORMAT",
            "%(asctime)s %(levelname)s %(name)s %(message)s",
        )
    )

    pipeline_name: str = field(
        default_factory=lambda: _env_str(
            "PIPELINE_NAME",
            "large_dataset_processing",
        )
    )

    @property
    def input_suffix(self) -> str:
        """Return the normalized input file suffix."""
        return self.input_file.suffix.lower()

    @property
    def output_suffix(self) -> str:
        """Return the normalized output file suffix."""
        return self.output_file.suffix.lower()

    @property
    def effective_chunk_size(self) -> int:
        """Return a chunk size constrained by configured safety bounds."""
        return max(
            self.min_chunk_size,
            min(
                self.chunk_size,
                self.max_chunk_size,
            ),
        )

    @property
    def csv_read_kwargs(self) -> dict[str, object]:
        """Return keyword arguments for Pandas CSV chunked reads."""
        kwargs: dict[str, object] = {
            "chunksize": self.effective_chunk_size,
            "sep": self.csv_separator,
            "encoding": self.csv_encoding,
            "low_memory": self.low_memory,
        }

        if self.usecols:
            kwargs["usecols"] = list(self.usecols)

        if self.null_value:
            kwargs["na_values"] = [self.null_value]

        return kwargs

    @property
    def parquet_write_kwargs(self) -> dict[str, object]:
        """Return keyword arguments for Parquet writes."""
        return {
            "compression": self.parquet_compression,
            "index": False,
        }

    def ensure_directories(self) -> None:
        """Create directories required by the pipeline."""
        if not self.create_directories:
            return

        for directory in (
            self.data_dir,
            self.raw_data_dir,
            self.staging_data_dir,
            self.processed_data_dir,
            self.reports_dir,
            self.benchmarks_dir,
            self.checkpoint_dir,
        ):
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )

    def validate(self) -> None:
        """Validate configuration combinations and operational constraints."""
        if self.min_chunk_size > self.max_chunk_size:
            raise ValueError(
                "min_chunk_size cannot be greater than max_chunk_size"
            )

        if self.benchmark_chunk_size <= 0:
            raise ValueError(
                "benchmark_chunk_size must be greater than zero"
            )

        if self.target_memory_mb < 128:
            raise ValueError(
                "target_memory_mb must be at least 128 MB"
            )

        if not 1.0 <= self.memory_warning_threshold_percent <= 100.0:
            raise ValueError(
                "memory_warning_threshold_percent must be between 1 and 100"
            )

        if self.file_format not in {
            "csv",
            "parquet",
            "json",
        }:
            raise ValueError(
                "file_format must be one of: csv, parquet, json"
            )

        if self.output_format not in {
            "csv",
            "parquet",
            "json",
        }:
            raise ValueError(
                "output_format must be one of: csv, parquet, json"
            )

        if self.file_format == "csv" and len(self.csv_separator) == 0:
            raise ValueError(
                "csv_separator cannot be empty"
            )

        if self.output_format == "parquet" and not self.output_file.suffix:
            raise ValueError(
                "output_file must have a file extension for Parquet output"
            )

        if self.resume_enabled and not self.checkpointing_enabled:
            raise ValueError(
                "resume_enabled requires checkpointing_enabled"
            )

        if self.checkpoint_interval_chunks <= 0:
            raise ValueError(
                "checkpoint_interval_chunks must be greater than zero"
            )

        if self.benchmark_repetitions <= 0:
            raise ValueError(
                "benchmark_repetitions must be greater than zero"
            )


config = PipelineConfig()
config.validate()


__all__ = [
    "BENCHMARKS_DIR",
    "CONFIG_DIR",
    "DATA_DIR",
    "PIPELINE_ROOT" if False else "PROJECT_ROOT",
    "RAW_DATA_DIR",
    "REPORTS_DIR",
    "STAGING_DATA_DIR",
    "PROCESSED_DATA_DIR",
    "PipelineConfig",
    "config",
]