from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


PROJECT_ROOT = Path(
    os.getenv(
        "API_PIPELINE_ROOT",
        Path(__file__).resolve().parents[1],
    )
).resolve()

DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"
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
    """Read a boolean environment variable."""
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


def _env_optional_str(name: str) -> str | None:
    """Read an optional string environment variable."""
    value = os.getenv(name)

    if value is None:
        return None

    normalized = value.strip()
    return normalized or None


@dataclass(frozen=True, slots=True)
class PipelineConfig:
    """Runtime configuration for the API data processing pipeline."""

    api_base_url: str = os.getenv(
        "API_BASE_URL",
        "https://api.example.com",
    )

    api_token: str | None = field(
        default_factory=lambda: _env_optional_str("API_TOKEN"),
        repr=False,
    )

    api_timeout_seconds: float = _env_float(
        "API_TIMEOUT_SECONDS",
        30.0,
        minimum=0.1,
    )

    api_connect_timeout_seconds: float = _env_float(
        "API_CONNECT_TIMEOUT_SECONDS",
        10.0,
        minimum=0.1,
    )

    api_read_timeout_seconds: float = _env_float(
        "API_READ_TIMEOUT_SECONDS",
        30.0,
        minimum=0.1,
    )

    api_max_retries: int = _env_int(
        "API_MAX_RETRIES",
        3,
        minimum=0,
    )

    api_backoff_factor: float = _env_float(
        "API_BACKOFF_FACTOR",
        1.0,
        minimum=0.0,
    )

    api_page_size: int = _env_int(
        "API_PAGE_SIZE",
        100,
        minimum=1,
    )

    api_max_pages: int = _env_int(
        "API_MAX_PAGES",
        10_000,
        minimum=1,
    )

    data_dir: Path = DATA_DIR
    raw_data_dir: Path = DATA_DIR / "raw"
    staging_data_dir: Path = DATA_DIR / "staging"
    processed_data_dir: Path = DATA_DIR / "processed"
    reports_dir: Path = REPORTS_DIR

    raw_response_file: str = "api_response.json"
    normalized_data_file: str = "normalized_data.parquet"
    rejected_records_file: str = "rejected_records.csv"
    processing_report_file: str = "processing_report.parquet"

    api_response_timezone: str = os.getenv(
        "API_RESPONSE_TIMEZONE",
        "UTC",
    )

    drop_invalid_records: bool = _env_bool(
        "DROP_INVALID_RECORDS",
        False,
    )

    fail_on_http_error: bool = _env_bool(
        "FAIL_ON_HTTP_ERROR",
        True,
    )

    fail_on_schema_error: bool = _env_bool(
        "FAIL_ON_SCHEMA_ERROR",
        True,
    )

    create_directories: bool = _env_bool(
        "CREATE_PIPELINE_DIRECTORIES",
        True,
    )

    atomic_writes: bool = _env_bool(
        "ATOMIC_PIPELINE_WRITES",
        True,
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
    def raw_response_path(self) -> Path:
        """Return the raw API response path."""
        return self.raw_data_dir / self.raw_response_file

    @property
    def normalized_data_path(self) -> Path:
        """Return the normalized dataset path."""
        return self.processed_data_dir / self.normalized_data_file

    @property
    def rejected_records_path(self) -> Path:
        """Return the rejected-records path."""
        return self.reports_dir / self.rejected_records_file

    @property
    def processing_report_path(self) -> Path:
        """Return the processing report path."""
        return self.reports_dir / self.processing_report_file

    @property
    def authorization_headers(self) -> dict[str, str]:
        """Build authorization headers when an API token is configured."""
        if self.api_token is None:
            return {
                "Accept": "application/json",
            }

        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_token}",
        }

    @property
    def request_timeout(self) -> tuple[float, float]:
        """Return the connect and read timeout pair."""
        return (
            self.api_connect_timeout_seconds,
            self.api_read_timeout_seconds,
        )

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
from dataclasses import dataclass, field
from pathlib import Path


PROJECT_ROOT = Path(
    os.getenv(
        "API_PIPELINE_ROOT",
        Path(__file__).resolve().parents[1],
    )
).resolve()

DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"
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
    """Read a boolean environment variable."""
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


def _env_optional_str(name: str) -> str | None:
    """Read an optional string environment variable."""
    value = os.getenv(name)

    if value is None:
        return None

    normalized = value.strip()
    return normalized or None


@dataclass(frozen=True, slots=True)
class PipelineConfig:
    """Runtime configuration for the API data processing pipeline."""

    api_base_url: str = os.getenv(
        "API_BASE_URL",
        "https://api.example.com",
    )

    api_token: str | None = field(
        default_factory=lambda: _env_optional_str("API_TOKEN"),
        repr=False,
    )

    api_timeout_seconds: float = _env_float(
        "API_TIMEOUT_SECONDS",
        30.0,
        minimum=0.1,
    )

    api_connect_timeout_seconds: float = _env_float(
        "API_CONNECT_TIMEOUT_SECONDS",
        10.0,
        minimum=0.1,
    )

    api_read_timeout_seconds: float = _env_float(
        "API_READ_TIMEOUT_SECONDS",
        30.0,
        minimum=0.1,
    )

    api_max_retries: int = _env_int(
        "API_MAX_RETRIES",
        3,
        minimum=0,
    )

    api_backoff_factor: float = _env_float(
        "API_BACKOFF_FACTOR",
        1.0,
        minimum=0.0,
    )

    api_page_size: int = _env_int(
        "API_PAGE_SIZE",
        100,
        minimum=1,
    )

    api_max_pages: int = _env_int(
        "API_MAX_PAGES",
        10_000,
        minimum=1,
    )

    data_dir: Path = DATA_DIR
    raw_data_dir: Path = DATA_DIR / "raw"
    staging_data_dir: Path = DATA_DIR / "staging"
    processed_data_dir: Path = DATA_DIR / "processed"
    reports_dir: Path = REPORTS_DIR

    raw_response_file: str = "api_response.json"
    normalized_data_file: str = "normalized_data.parquet"
    rejected_records_file: str = "rejected_records.csv"
    processing_report_file: str = "processing_report.parquet"

    api_response_timezone: str = os.getenv(
        "API_RESPONSE_TIMEZONE",
        "UTC",
    )

    drop_invalid_records: bool = _env_bool(
        "DROP_INVALID_RECORDS",
        False,
    )

    fail_on_http_error: bool = _env_bool(
        "FAIL_ON_HTTP_ERROR",
        True,
    )

    fail_on_schema_error: bool = _env_bool(
        "FAIL_ON_SCHEMA_ERROR",
        True,
    )

    create_directories: bool = _env_bool(
        "CREATE_PIPELINE_DIRECTORIES",
        True,
    )

    atomic_writes: bool = _env_bool(
        "ATOMIC_PIPELINE_WRITES",
        True,
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
    def raw_response_path(self) -> Path:
        """Return the raw API response path."""
        return self.raw_data_dir / self.raw_response_file

    @property
    def normalized_data_path(self) -> Path:
        """Return the normalized dataset path."""
        return self.processed_data_dir / self.normalized_data_file

    @property
    def rejected_records_path(self) -> Path:
        """Return the rejected-records path."""
        return self.reports_dir / self.rejected_records_file

    @property
    def processing_report_path(self) -> Path:
        """Return the processing report path."""
        return self.reports_dir / self.processing_report_file

    @property
    def authorization_headers(self) -> dict[str, str]:
        """Build authorization headers when an API token is configured."""
        if self.api_token is None:
            return {
                "Accept": "application/json",
            }

        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_token}",
        }

    @property
    def request_timeout(self) -> tuple[float, float]:
        """Return the connect and read timeout pair."""
        return (
            self.api_connect_timeout_seconds,
            self.api_read_timeout_seconds,
        )

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