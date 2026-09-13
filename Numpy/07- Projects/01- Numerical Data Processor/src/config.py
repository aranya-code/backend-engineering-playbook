"""Project configuration for the Numerical Data Processor."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

DEFAULT_INPUT_FILENAME = "numerical_data.npy"
DEFAULT_OUTPUT_FILENAME = "processed_data.npy"

DEFAULT_DTYPE = "float64"
MAX_ELEMENTS = 1_000_000
BATCH_SIZE = 100_000

MIN_ALLOWED_VALUE = 0.0
MAX_ALLOWED_VALUE = 1_000_000.0
REJECT_NON_FINITE_VALUES = True

"""Project configuration for the Numerical Data Processor."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

DEFAULT_INPUT_FILENAME = "numerical_data.npy"
DEFAULT_OUTPUT_FILENAME = "processed_data.npy"

DEFAULT_DTYPE = "float64"
MAX_ELEMENTS = 1_000_000
BATCH_SIZE = 100_000

MIN_ALLOWED_VALUE = 0.0
MAX_ALLOWED_VALUE = 1_000_000.0
REJECT_NON_FINITE_VALUES = True