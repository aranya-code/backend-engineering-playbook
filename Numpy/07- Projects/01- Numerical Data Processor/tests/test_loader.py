"""Tests for numerical data loading."""

from pathlib import Path

import numpy as np
import pytest

from src.loader import load_array


def test_load_array_reads_npy_file(tmp_path: Path) -> None:
    input_path = tmp_path / "input.npy"
    expected = np.array(
        [10.0, 20.0, 30.0],
        dtype=np.float64,
    )

    np.save(input_path, expected)

    actual = load_array(input_path)

    np.testing.assert_array_equal(actual, expected)
    assert actual.dtype == np.float64


def test_load_array_converts_dtype(tmp_path: Path) -> None:
    input_path = tmp_path / "input.npy"
    values = np.array([1, 2, 3], dtype=np.int32)

    np.save(input_path, values)

    actual = load_array(
        input_path,
        dtype="float64",
    )

    np.testing.assert_array_equal(actual, values)
    assert actual.dtype == np.float64


def test_load_array_rejects_missing_file(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.npy"

    with pytest.raises(FileNotFoundError):
        load_array(missing_path)


def test_load_array_rejects_unsupported_extension(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.csv"
    input_path.write_text(
        "1,2,3\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unsupported input format"):
        load_array(input_path)


def test_load_array_rejects_too_many_elements(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.npy"
    values = np.arange(10)

    np.save(input_path, values)

    with pytest.raises(ValueError, match="maximum allowed"):
        load_array(
            input_path,
            max_elements=5,
        )


def test_load_array_does_not_allow_pickle(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "objects.npy"
    values = np.array(
        [{"value": 1}],
        dtype=object,
    )

    np.save(
        input_path,
        values,
        allow_pickle=True,
    )

    with pytest.raises(ValueError):
        load_array(input_path)

"""Tests for numerical data loading."""

from pathlib import Path

import numpy as np
import pytest

from src.loader import load_array


def test_load_array_reads_npy_file(tmp_path: Path) -> None:
    input_path = tmp_path / "input.npy"
    expected = np.array(
        [10.0, 20.0, 30.0],
        dtype=np.float64,
    )

    np.save(input_path, expected)

    actual = load_array(input_path)

    np.testing.assert_array_equal(actual, expected)
    assert actual.dtype == np.float64


def test_load_array_converts_dtype(tmp_path: Path) -> None:
    input_path = tmp_path / "input.npy"
    values = np.array([1, 2, 3], dtype=np.int32)

    np.save(input_path, values)

    actual = load_array(
        input_path,
        dtype="float64",
    )

    np.testing.assert_array_equal(actual, values)
    assert actual.dtype == np.float64


def test_load_array_rejects_missing_file(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.npy"

    with pytest.raises(FileNotFoundError):
        load_array(missing_path)


def test_load_array_rejects_unsupported_extension(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.csv"
    input_path.write_text(
        "1,2,3\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unsupported input format"):
        load_array(input_path)


def test_load_array_rejects_too_many_elements(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.npy"
    values = np.arange(10)

    np.save(input_path, values)

    with pytest.raises(ValueError, match="maximum allowed"):
        load_array(
            input_path,
            max_elements=5,
        )


def test_load_array_does_not_allow_pickle(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "objects.npy"
    values = np.array(
        [{"value": 1}],
        dtype=object,
    )

    np.save(
        input_path,
        values,
        allow_pickle=True,
    )

    with pytest.raises(ValueError):
        load_array(input_path)