"""Project configuration for the Vectorized Data Transformation pipeline."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
INPUT_DIR = DATA_DIR / "raw"
OUTPUT_DIR = DATA_DIR / "processed"

DEFAULT_INPUT_FILENAME = "input.npy"
DEFAULT_OUTPUT_FILENAME = "transformed.npy"

DEFAULT_DTYPE = "float64"
MAX_ELEMENTS = 1_000_000
BATCH_SIZE = 100_000

DEFAULT_SCALE = 1.0
DEFAULT_OFFSET = 0.0

MIN_ALLOWED_VALUE = 0.0
MAX_ALLOWED_VALUE = 1_000_000.0
REJECT_NON_FINITE_VALUES = True

NORMALIZE_OUTPUT = False
NORMALIZATION_MIN = 0.0
NORMALIZATION_MAX = 1.0

"""Project configuration for the Vectorized Data Transformation pipeline."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
INPUT_DIR = DATA_DIR / "raw"
OUTPUT_DIR = DATA_DIR / "processed"

DEFAULT_INPUT_FILENAME = "input.npy"
DEFAULT_OUTPUT_FILENAME = "transformed.npy"

DEFAULT_DTYPE = "float64"
MAX_ELEMENTS = 1_000_000
BATCH_SIZE = 100_000

DEFAULT_SCALE = 1.0
DEFAULT_OFFSET = 0.0

MIN_ALLOWED_VALUE = 0.0
MAX_ALLOWED_VALUE = 1_000_000.0
REJECT_NON_FINITE_VALUES = True

NORMALIZE_OUTPUT = False
NORMALIZATION_MIN = 0.0
NORMALIZATION_MAX = 1.0