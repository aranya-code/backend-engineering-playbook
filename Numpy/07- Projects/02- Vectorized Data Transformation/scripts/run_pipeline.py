from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import PipelineConfig, run_pipeline


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for a pipeline execution."""
    parser = argparse.ArgumentParser(
        description="Run the vectorized numerical transformation pipeline.",
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Path to the input .npy file.",
    )
    parser.add_argument(
        "output",
        type=Path,
        help="Path to the output .npy, .csv, or text file.",
    )
    parser.add_argument(
        "--factor",
        type=float,
        default=1.0,
        help="Multiplication factor applied to each value.",
    )
    parser.add_argument(
        "--offset",
        type=float,
        default=0.0,
        help="Additive offset applied after scaling.",
    )
    parser.add_argument(
        "--minimum",
        type=float,
        default=0.0,
        help="Inclusive minimum for transformed values.",
    )
    parser.add_argument(
        "--maximum",
        type=float,
        default=1_000_000.0,
        help="Inclusive maximum for transformed values.",
    )
    parser.add_argument(
        "--normalize",
        action="store_true",
        help="Normalize transformed values to the configured output range.",
    )
    parser.add_argument(
        "--max-elements",
        type=int,
        default=1_000_000,
        help="Maximum number of input elements allowed.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100_000,
        help="Number of elements processed per batch.",
    )

    return parser.parse_args()


def main() -> int:
    """Execute the pipeline and report operational results."""
    args = parse_args()

    config = PipelineConfig(
        factor=args.factor,
        offset=args.offset,
        minimum=args.minimum,
        maximum=args.maximum,
        normalize_output=args.normalize,
        max_elements=args.max_elements,
        batch_size=args.batch_size,
    )

    try:
        result = run_pipeline(
            args.input,
            args.output,
            config=config,
        )
    except (FileNotFoundError, FileExistsError, TypeError, ValueError) as exc:
        print(
            f"Pipeline failed: {exc}",
            file=sys.stderr,
        )
        return 1

    print(f"Output: {result.output_path}")
    print(f"Input elements: {result.input_elements:,}")
    print(f"Output elements: {result.output_elements:,}")
    print(f"Input bytes: {result.input_nbytes:,}")
    print(f"Output bytes: {result.output_nbytes:,}")

    statistics = result.statistics
    print(f"Mean: {statistics['mean']:.6f}")
    print(f"Minimum: {statistics['minimum']:.6f}")
    print(f"Maximum: {statistics['maximum']:.6f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import PipelineConfig, run_pipeline


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for a pipeline execution."""
    parser = argparse.ArgumentParser(
        description="Run the vectorized numerical transformation pipeline.",
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Path to the input .npy file.",
    )
    parser.add_argument(
        "output",
        type=Path,
        help="Path to the output .npy, .csv, or text file.",
    )
    parser.add_argument(
        "--factor",
        type=float,
        default=1.0,
        help="Multiplication factor applied to each value.",
    )
    parser.add_argument(
        "--offset",
        type=float,
        default=0.0,
        help="Additive offset applied after scaling.",
    )
    parser.add_argument(
        "--minimum",
        type=float,
        default=0.0,
        help="Inclusive minimum for transformed values.",
    )
    parser.add_argument(
        "--maximum",
        type=float,
        default=1_000_000.0,
        help="Inclusive maximum for transformed values.",
    )
    parser.add_argument(
        "--normalize",
        action="store_true",
        help="Normalize transformed values to the configured output range.",
    )
    parser.add_argument(
        "--max-elements",
        type=int,
        default=1_000_000,
        help="Maximum number of input elements allowed.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100_000,
        help="Number of elements processed per batch.",
    )

    return parser.parse_args()


def main() -> int:
    """Execute the pipeline and report operational results."""
    args = parse_args()

    config = PipelineConfig(
        factor=args.factor,
        offset=args.offset,
        minimum=args.minimum,
        maximum=args.maximum,
        normalize_output=args.normalize,
        max_elements=args.max_elements,
        batch_size=args.batch_size,
    )

    try:
        result = run_pipeline(
            args.input,
            args.output,
            config=config,
        )
    except (FileNotFoundError, FileExistsError, TypeError, ValueError) as exc:
        print(
            f"Pipeline failed: {exc}",
            file=sys.stderr,
        )
        return 1

    print(f"Output: {result.output_path}")
    print(f"Input elements: {result.input_elements:,}")
    print(f"Output elements: {result.output_elements:,}")
    print(f"Input bytes: {result.input_nbytes:,}")
    print(f"Output bytes: {result.output_nbytes:,}")

    statistics = result.statistics
    print(f"Mean: {statistics['mean']:.6f}")
    print(f"Minimum: {statistics['minimum']:.6f}")
    print(f"Maximum: {statistics['maximum']:.6f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())