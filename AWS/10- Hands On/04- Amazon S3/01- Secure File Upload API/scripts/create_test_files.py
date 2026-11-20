from __future__ import annotations

import argparse
import base64
import json
import logging
import sys
from pathlib import Path
from typing import Any


LOGGER = logging.getLogger("create_test_files")

DEFAULT_OUTPUT_DIR = Path("data/test-files")
DEFAULT_LARGE_FILE_SIZE_MIB = 5
MIB = 1024 * 1024
CHUNK_SIZE = 64 * 1024

SAMPLE_TEXT = (
    "Secure File Upload API test fixture.\n"
    "This file is intended for upload, download, and metadata testing.\n"
    "It contains non-sensitive sample data.\n"
)

SAMPLE_JSON = {
    "document_id": "test-document-001",
    "name": "sample-document",
    "category": "engineering",
    "description": "Sample JSON file for S3 upload testing.",
    "metadata": {
        "environment": "test",
        "source": "create_test_files.py",
    },
}

SAMPLE_CSV = (
    "document_id,name,category,status\n"
    "DOC-001,Architecture Document,engineering,active\n"
    "DOC-002,API Specification,technical,active\n"
    "DOC-003,Test Report,testing,archived\n"
)

# A valid 1x1 PNG image.
SAMPLE_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwC"
    "AAAAC0lEQVR42mP8/x8AAwMCAO+/pL8AAAAASUVORK5CYII="
)

SAMPLE_FILES: dict[str, bytes] = {
    "sample.txt": SAMPLE_TEXT.encode("utf-8"),
    "sample.json": json.dumps(
        SAMPLE_JSON,
        indent=2,
        ensure_ascii=False,
    ).encode("utf-8"),
    "sample.csv": SAMPLE_CSV.encode("utf-8"),
    "sample.png": SAMPLE_PNG,
    "empty.txt": b"",
}


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Generate deterministic test files for the Secure File Upload API."
        )
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=(
            "Directory where test files will be created. "
            f"Default: {DEFAULT_OUTPUT_DIR}"
        ),
    )

    parser.add_argument(
        "--large-size-mib",
        type=int,
        default=DEFAULT_LARGE_FILE_SIZE_MIB,
        help=(
            "Size of the generated large binary test file in MiB. "
            f"Default: {DEFAULT_LARGE_FILE_SIZE_MIB}"
        ),
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow existing generated files to be overwritten.",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable detailed logging.",
    )

    return parser.parse_args()


def configure_logging(verbose: bool) -> None:
    """Configure command-line logging."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )


def validate_arguments(args: argparse.Namespace) -> None:
    """Validate command-line arguments before creating files."""
    if args.large_size_mib < 1:
        raise ValueError("--large-size-mib must be at least 1.")

    if args.large_size_mib > 1024:
        raise ValueError(
            "--large-size-mib cannot exceed 1024 MiB. "
            "Use a dedicated large-file test workflow for larger files."
        )

    if not args.output_dir.name:
        raise ValueError("The output directory must have a valid name.")


def ensure_output_directory(output_dir: Path) -> None:
    """Create the output directory if it does not exist."""
    output_dir.mkdir(parents=True, exist_ok=True)

    if not output_dir.is_dir():
        raise NotADirectoryError(
            f"Output path is not a directory: {output_dir}"
        )


def write_file(
    output_dir: Path,
    filename: str,
    content: bytes,
    force: bool,
) -> Path:
    """Write a test fixture without overwriting files by default."""
    destination = output_dir / filename

    if destination.exists() and not force:
        raise FileExistsError(
            f"{destination} already exists. "
            "Use --force to overwrite generated files."
        )

    temporary_path = destination.with_name(
        f".{destination.name}.tmp"
    )

    try:
        with temporary_path.open("wb") as file:
            file.write(content)

        temporary_path.replace(destination)

    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise

    LOGGER.info(
        "Created %-24s %10d bytes",
        filename,
        destination.stat().st_size,
    )

    return destination


def write_large_binary_file(
    output_dir: Path,
    size_mib: int,
    force: bool,
) -> Path:
    """
    Generate a large binary file without loading its complete contents
    into memory.

    The generated content is deterministic and suitable for repeatable
    upload and download tests.
    """
    filename = "large-binary.bin"
    destination = output_dir / filename

    if destination.exists() and not force:
        raise FileExistsError(
            f"{destination} already exists. "
            "Use --force to overwrite generated files."
        )

    total_size = size_mib * MIB
    remaining = total_size
    pattern = bytes(range(256))
    temporary_path = destination.with_name(
        f".{destination.name}.tmp"
    )

    try:
        with temporary_path.open("wb") as file:
            while remaining > 0:
                chunk_size = min(CHUNK_SIZE, remaining)
                repetitions = (chunk_size + len(pattern) - 1) // len(pattern)
                chunk = (pattern * repetitions)[:chunk_size]

                file.write(chunk)
                remaining -= chunk_size

        temporary_path.replace(destination)

    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise

    LOGGER.info(
        "Created %-24s %10d bytes",
        filename,
        destination.stat().st_size,
    )

    return destination


def build_manifest(
    output_dir: Path,
    generated_files: list[Path],
) -> Path:
    """Create a JSON manifest describing the generated fixtures."""
    manifest: dict[str, Any] = {
        "description": "Generated test fixtures for the Secure File Upload API.",
        "files": [
            {
                "filename": path.name,
                "size_bytes": path.stat().st_size,
                "extension": path.suffix.lower(),
            }
            for path in sorted(generated_files)
        ],
    }

    manifest_path = output_dir / "manifest.json"
    temporary_path = output_dir / ".manifest.json.tmp"

    try:
        with temporary_path.open(
            "w",
            encoding="utf-8",
            newline="\n",
        ) as file:
            json.dump(
                manifest,
                file,
                indent=2,
                ensure_ascii=False,
            )
            file.write("\n")

        temporary_path.replace(manifest_path)

    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise

    LOGGER.info(
        "Created %-24s %10d bytes",
        manifest_path.name,
        manifest_path.stat().st_size,
    )

    return manifest_path


def create_test_files(
    output_dir: Path,
    large_size_mib: int,
    force: bool = False,
) -> list[Path]:
    """Generate all test fixtures and return their paths."""
    ensure_output_directory(output_dir)

    generated_files: list[Path] = []

    for filename, content in SAMPLE_FILES.items():
        generated_files.append(
            write_file(
                output_dir=output_dir,
                filename=filename,
                content=content,
                force=force,
            )
        )

    generated_files.append(
        write_large_binary_file(
            output_dir=output_dir,
            size_mib=large_size_mib,
            force=force,
        )
    )

    generated_files.append(
        build_manifest(
            output_dir=output_dir,
            generated_files=generated_files,
        )
    )

    return generated_files


def main() -> int:
    """Execute the test fixture generation workflow."""
    args = parse_args()
    configure_logging(args.verbose)

    try:
        validate_arguments(args)

        generated_files = create_test_files(
            output_dir=args.output_dir,
            large_size_mib=args.large_size_mib,
            force=args.force,
        )

    except (OSError, ValueError) as exc:
        LOGGER.error("%s", exc)
        return 1

    LOGGER.info(
        "Successfully generated %d test files in %s",
        len(generated_files),
        args.output_dir.resolve(),
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())