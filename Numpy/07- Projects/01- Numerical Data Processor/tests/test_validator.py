"""Tests for numerical array validation."""

import numpy as np
import pytest

from src.validator import validate_array


def test_validate_array_accepts_valid_input() -> None:
    values = np.array(
        [10.0, 25.0, 100.0],
        dtype=np.float64,
    )

    actual = validate_array(values)

    np.testing.assert_array_equal(actual, values)


def test_validate_array_rejects_empty_array() -> None:
    values = np.array([], dtype=np.float64)

    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        validate_array(values)


def test_validate_array_rejects_non_one_dimensional_input() -> None:
    values = np.array(
        [[10.0, 20.0]],
        dtype=np.float64,
    )

    with pytest.raises(
        ValueError,
        match="one-dimensional",
    ):
        validate_array(values)


def test_validate_array_rejects_non_numeric_dtype() -> None:
    values = np.array(
        ["10", "20", "30"],
        dtype="<U2",
    )

    with pytest.raises(
        TypeError,
        match="Expected numeric dtype",
    ):
        validate_array(values)


@pytest.mark.parametrize(
    "values",
    [
        np.array([10.0, np.nan]),
        np.array([10.0, np.inf]),
        np.array([-np.inf, 10.0]),
    ],
)
def test_validate_array_rejects_non_finite_values(
    values: np.ndarray,
) -> None:
    with pytest.raises(
        ValueError,
        match="NaN or infinite",
    ):
        validate_array(values)


def test_validate_array_can_allow_non_finite_values() -> None:
    values = np.array(
        [10.0, np.nan, 20.0],
        dtype=np.float64,
    )

    actual = validate_array(
        values,
        reject_non_finite=False,
    )

    np.testing.assert_array_equal(
        actual,
        values,
        equal_nan=True,
    )


def test_validate_array_rejects_values_below_minimum() -> None:
    values = np.array(
        [10.0, -1.0, 20.0],
        dtype=np.float64,
    )

    with pytest.raises(
        ValueError,
        match="below the minimum",
    ):
        validate_array(
            values,
            minimum=0.0,
        )


def test_validate_array_rejects_values_above_maximum() -> None:
    values = np.array(
        [10.0, 100.0, 150.0],
        dtype=np.float64,
    )

    with pytest.raises(
        ValueError,
        match="above the maximum",
    ):
        validate_array(
            values,
            maximum=100.0,
        )


def test_validate_array_rejects_too_many_elements() -> None:
    values = np.arange(
        11,
        dtype=np.float64,
    )

    with pytest.raises(
        ValueError,
        match="maximum allowed",
    ):
        validate_array(
            values,
            max_elements=10,
        )


def test_validate_array_accepts_custom_bounds() -> None:
    values = np.array(
        [10.0, 20.0, 30.0],
        dtype=np.float64,
    )

    actual = validate_array(
        values,
        minimum=10.0,
        maximum=30.0,
    )

    np.testing.assert_array_equal(actual, values)

"""Tests for numerical array validation."""

import numpy as np
import pytest

from src.validator import validate_array


def test_validate_array_accepts_valid_input() -> None:
    values = np.array(
        [10.0, 25.0, 100.0],
        dtype=np.float64,
    )

    actual = validate_array(values)

    np.testing.assert_array_equal(actual, values)


def test_validate_array_rejects_empty_array() -> None:
    values = np.array([], dtype=np.float64)

    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        validate_array(values)


def test_validate_array_rejects_non_one_dimensional_input() -> None:
    values = np.array(
        [[10.0, 20.0]],
        dtype=np.float64,
    )

    with pytest.raises(
        ValueError,
        match="one-dimensional",
    ):
        validate_array(values)


def test_validate_array_rejects_non_numeric_dtype() -> None:
    values = np.array(
        ["10", "20", "30"],
        dtype="<U2",
    )

    with pytest.raises(
        TypeError,
        match="Expected numeric dtype",
    ):
        validate_array(values)


@pytest.mark.parametrize(
    "values",
    [
        np.array([10.0, np.nan]),
        np.array([10.0, np.inf]),
        np.array([-np.inf, 10.0]),
    ],
)
def test_validate_array_rejects_non_finite_values(
    values: np.ndarray,
) -> None:
    with pytest.raises(
        ValueError,
        match="NaN or infinite",
    ):
        validate_array(values)


def test_validate_array_can_allow_non_finite_values() -> None:
    values = np.array(
        [10.0, np.nan, 20.0],
        dtype=np.float64,
    )

    actual = validate_array(
        values,
        reject_non_finite=False,
    )

    np.testing.assert_array_equal(
        actual,
        values,
        equal_nan=True,
    )


def test_validate_array_rejects_values_below_minimum() -> None:
    values = np.array(
        [10.0, -1.0, 20.0],
        dtype=np.float64,
    )

    with pytest.raises(
        ValueError,
        match="below the minimum",
    ):
        validate_array(
            values,
            minimum=0.0,
        )


def test_validate_array_rejects_values_above_maximum() -> None:
    values = np.array(
        [10.0, 100.0, 150.0],
        dtype=np.float64,
    )

    with pytest.raises(
        ValueError,
        match="above the maximum",
    ):
        validate_array(
            values,
            maximum=100.0,
        )


def test_validate_array_rejects_too_many_elements() -> None:
    values = np.arange(
        11,
        dtype=np.float64,
    )

    with pytest.raises(
        ValueError,
        match="maximum allowed",
    ):
        validate_array(
            values,
            max_elements=10,
        )


def test_validate_array_accepts_custom_bounds() -> None:
    values = np.array(
        [10.0, 20.0, 30.0],
        dtype=np.float64,
    )

    actual = validate_array(
        values,
        minimum=10.0,
        maximum=30.0,
    )

    np.testing.assert_array_equal(actual, values)