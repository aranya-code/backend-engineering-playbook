"""Output helpers for the Numerical Data Processor."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Mapping

import numpy as np

from .config import DEFAULT_OUTPUT_FILENAME, OUTPUT_DIR


def _atomic_replace(
    temporary_path: Path,
    target_path: Path,
) -> None:
    """Atomically replace the target file with a prepared temporary file."""
    os.replace(temporary_path, target_path)


def export_array(
    values: np.ndarray,
    path: str | Path | None = None,
) -> Path:
    """Persist a numerical array as a .npy file."""
    output_path = (
        Path(path)
        if path is not None
        else OUTPUT_DIR / DEFAULT_OUTPUT_FILENAME
    )

    if output_path.suffix.lower() != ".npy":
        raise ValueError(
            f"Array output must use .npy format: {output_path}"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    values = np.asarray(values)

    temporary_path = output_path.with_suffix(
        output_path.suffix + ".tmp"
    )

    try:
        np.save(
            temporary_path,
            values,
            allow_pickle=False,
        )

        generated_path = Path(f"{temporary_path}.npy")

        if not generated_path.is_file():
            raise RuntimeError(
                f"NumPy failed to create output file: {generated_path}"
            )

        _atomic_replace(
            generated_path,
            output_path,
        )
    finally:
        for candidate in (
            temporary_path,
            Path(f"{temporary_path}.npy"),
        ):
            candidate.unlink(
                missing_ok=True,
            )

    return output_path


def export_statistics(
    statistics: Mapping[str, float],
    path: str | Path,
) -> Path:
    """Persist calculated statistics as UTF-8 JSON."""
    output_path = Path(path)

    if output_path.suffix.lower() != ".json":
        raise ValueError(
            f"Statistics output must use .json format: {output_path}"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        str(key): float(value)
        for key, value in statistics.items()
    }

    temporary_path = output_path.with_suffix(
        output_path.suffix + ".tmp"
    )

    try:
        with temporary_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                payload,
                file,
                indent=2,
                sort_keys=True,
            )
            file.write("\n")

        _atomic_replace(
            temporary_path,
            output_path,
        )
    finally:
        temporary_path.unlink(
            missing_ok=True,
        )

    return output_path

"""Output helpers for the Numerical Data Processor."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Mapping

import numpy as np

from .config import DEFAULT_OUTPUT_FILENAME, OUTPUT_DIR


def _atomic_replace(
    temporary_path: Path,
    target_path: Path,
) -> None:
    """Atomically replace the target file with a prepared temporary file."""
    os.replace(temporary_path, target_path)


def export_array(
    values: np.ndarray,
    path: str | Path | None = None,
) -> Path:
    """Persist a numerical array as a .npy file."""
    output_path = (
        Path(path)
        if path is not None
        else OUTPUT_DIR / DEFAULT_OUTPUT_FILENAME
    )

    if output_path.suffix.lower() != ".npy":
        raise ValueError(
            f"Array output must use .npy format: {output_path}"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    values = np.asarray(values)

    temporary_path = output_path.with_suffix(
        output_path.suffix + ".tmp"
    )

    try:
        np.save(
            temporary_path,
            values,
            allow_pickle=False,
        )

        generated_path = Path(f"{temporary_path}.npy")

        if not generated_path.is_file():
            raise RuntimeError(
                f"NumPy failed to create output file: {generated_path}"
            )

        _atomic_replace(
            generated_path,
            output_path,
        )
    finally:
        for candidate in (
            temporary_path,
            Path(f"{temporary_path}.npy"),
        ):
            candidate.unlink(
                missing_ok=True,
            )

    return output_path


def export_statistics(
    statistics: Mapping[str, float],
    path: str | Path,
) -> Path:
    """Persist calculated statistics as UTF-8 JSON."""
    output_path = Path(path)

    if output_path.suffix.lower() != ".json":
        raise ValueError(
            f"Statistics output must use .json format: {output_path}"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        str(key): float(value)
        for key, value in statistics.items()
    }

    temporary_path = output_path.with_suffix(
        output_path.suffix + ".tmp"
    )

    try:
        with temporary_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                payload,
                file,
                indent=2,
                sort_keys=True,
            )
            file.write("\n")

        _atomic_replace(
            temporary_path,
            output_path,
        )
    finally:
        temporary_path.unlink(
            missing_ok=True,
        )

    return output_path