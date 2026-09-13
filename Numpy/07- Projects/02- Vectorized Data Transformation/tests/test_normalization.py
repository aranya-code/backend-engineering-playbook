"""Tests for numerical normalization utilities."""

from __future__ import annotations

import numpy as np
import pytest

from src.normalization import (
    min_max_normalize,
    normalize_by_max_abs,
    normalize_columns,
    standardize,
)


def test_min_max_normalize_maps_values_to_default_range() -> None:
    values = np.array([10.0, 20.0, 30.0])

    result = min_max_normalize(values)

    np.testing.assert_allclose(
        result,
        np.array([0.0, 0.5, 1.0]),
    )


def test_min_max_normalize_supports_custom_output_range() -> None:
    values = np.array([10.0, 20.0, 30.0])

    result = min_max_normalize(
        values,
        output_min=-1.0,
        output_max=1.0,
    )

    np.testing.assert_allclose(
        result,
        np.array([-1.0, 0.0, 1.0]),
    )


def test_min_max_normalize_constant_input_returns_output_minimum() -> None:
    values = np.array([5.0, 5.0, 5.0])

    result = min_max_normalize(
        values,
        output_min=2.0,
        output_max=8.0,
    )

    np.testing.assert_allclose(
        result,
        np.array([2.0, 2.0, 2.0]),
    )


def test_min_max_normalize_preserves_empty_input() -> None:
    values = np.array([], dtype=np.float64)

    result = min_max_normalize(values)

    np.testing.assert_array_equal(
        result,
        values,
    )


def test_min_max_normalize_rejects_invalid_output_range() -> None:
    values = np.array([1.0, 2.0, 3.0])

    with pytest.raises(
        ValueError,
        match="output_min must be less than output_max",
    ):
        min_max_normalize(
            values,
            output_min=1.0,
            output_max=1.0,
        )


@pytest.mark.parametrize(
    "output_min, output_max",
    [
        (np.nan, 1.0),
        (0.0, np.inf),
        (-np.inf, 1.0),
    ],
)
def test_min_max_normalize_rejects_non_finite_output_bounds(
    output_min: float,
    output_max: float,
) -> None:
    values = np.array([1.0, 2.0, 3.0])

    with pytest.raises(
        ValueError,
        match="Normalization bounds must be finite",
    ):
        min_max_normalize(
            values,
            output_min=output_min,
            output_max=output_max,
        )


def test_min_max_normalize_rejects_non_finite_input() -> None:
    values = np.array([1.0, np.nan, 3.0])

    with pytest.raises(
        ValueError,
        match="Input contains NaN or infinite values",
    ):
        min_max_normalize(values)


def test_standardize_produces_zero_mean_and_unit_standard_deviation() -> None:
    values = np.array([10.0, 20.0, 30.0, 40.0])

    result = standardize(values)

    np.testing.assert_allclose(
        result.mean(),
        0.0,
    )
    np.testing.assert_allclose(
        result.std(),
        1.0,
    )


def test_standardize_supports_sample_standard_deviation() -> None:
    values = np.array([10.0, 20.0, 30.0])

    result = standardize(
        values,
        ddof=1,
    )

    np.testing.assert_allclose(
        result.mean(),
        0.0,
    )
    np.testing.assert_allclose(
        result.std(ddof=1),
        1.0,
    )


def test_standardize_constant_input_returns_zeros() -> None:
    values = np.array([7.0, 7.0, 7.0])

    result = standardize(values)

    np.testing.assert_array_equal(
        result,
        np.zeros_like(values),
    )


def test_standardize_preserves_empty_input() -> None:
    values = np.array([], dtype=np.float64)

    result = standardize(values)

    np.testing.assert_array_equal(
        result,
        values,
    )


def test_standardize_rejects_negative_ddof() -> None:
    values = np.array([1.0, 2.0, 3.0])

    with pytest.raises(ValueError, match="ddof must be non-negative"):
        standardize(
            values,
            ddof=-1,
        )


def test_standardize_rejects_non_finite_input() -> None:
    values = np.array([1.0, np.inf, 3.0])

    with pytest.raises(
        ValueError,
        match="Input contains NaN or infinite values",
    ):
        standardize(values)


def test_normalize_by_max_abs_scales_to_unit_magnitude() -> None:
    values = np.array([-10.0, -5.0, 0.0, 5.0, 10.0])

    result = normalize_by_max_abs(values)

    np.testing.assert_allclose(
        result,
        np.array([-1.0, -0.5, 0.0, 0.5, 1.0]),
    )


def test_normalize_by_max_abs_handles_zero_input() -> None:
    values = np.zeros(4, dtype=np.float64)

    result = normalize_by_max_abs(values)

    np.testing.assert_array_equal(
        result,
        values,
    )


def test_normalize_by_max_abs_preserves_empty_input() -> None:
    values = np.array([], dtype=np.float64)

    result = normalize_by_max_abs(values)

    np.testing.assert_array_equal(
        result,
        values,
    )


def test_normalize_by_max_abs_rejects_non_finite_input() -> None:
    values = np.array([1.0, np.nan, 3.0])

    with pytest.raises(
        ValueError,
        match="Input contains NaN or infinite values",
    ):
        normalize_by_max_abs(values)


def test_normalize_columns_normalizes_each_column() -> None:
    values = np.array(
        [
            [10.0, 100.0],
            [20.0, 200.0],
            [30.0, 300.0],
        ]
    )

    result = normalize_columns(values)

    expected = np.array(
        [
            [0.0, 0.0],
            [0.5, 0.5],
            [1.0, 1.0],
        ]
    )

    np.testing.assert_allclose(
        result,
        expected,
    )


def test_normalize_columns_normalizes_each_row_when_axis_one() -> None:
    values = np.array(
        [
            [10.0, 20.0, 30.0],
            [100.0, 200.0, 300.0],
        ]
    )

    result = normalize_columns(
        values,
        axis=1,
    )

    expected = np.array(
        [
            [0.0, 0.5, 1.0],
            [0.0, 0.5, 1.0],
        ]
    )

    np.testing.assert_allclose(
        result,
        expected,
    )


def test_normalize_columns_maps_constant_columns_to_zero() -> None:
    values = np.array(
        [
            [10.0, 5.0],
            [10.0, 10.0],
            [10.0, 15.0],
        ]
    )

    result = normalize_columns(values)

    expected = np.array(
        [
            [0.0, 0.0],
            [0.0, 0.5],
            [0.0, 1.0],
        ]
    )

    np.testing.assert_allclose(
        result,
        expected,
    )


def test_normalize_columns_rejects_one_dimensional_input() -> None:
    values = np.array([1.0, 2.0, 3.0])

    with pytest.raises(
        ValueError,
        match="requires a two-dimensional array",
    ):
        normalize_columns(values)


def test_normalize_columns_rejects_invalid_axis() -> None:
    values = np.ones((2, 3))

    with pytest.raises(
        ValueError,
        match="axis must be 0 or 1",
    ):
        normalize_columns(
            values,
            axis=2,
        )


def test_normalize_columns_rejects_non_finite_input() -> None:
    values = np.array(
        [
            [1.0, 2.0],
            [3.0, np.inf],
        ]
    )

    with pytest.raises(
        ValueError,
        match="Input contains NaN or infinite values",
    ):
        normalize_columns(values)

"""Tests for numerical normalization utilities."""

from __future__ import annotations

import numpy as np
import pytest

from src.normalization import (
    min_max_normalize,
    normalize_by_max_abs,
    normalize_columns,
    standardize,
)


def test_min_max_normalize_maps_values_to_default_range() -> None:
    values = np.array([10.0, 20.0, 30.0])

    result = min_max_normalize(values)

    np.testing.assert_allclose(
        result,
        np.array([0.0, 0.5, 1.0]),
    )


def test_min_max_normalize_supports_custom_output_range() -> None:
    values = np.array([10.0, 20.0, 30.0])

    result = min_max_normalize(
        values,
        output_min=-1.0,
        output_max=1.0,
    )

    np.testing.assert_allclose(
        result,
        np.array([-1.0, 0.0, 1.0]),
    )


def test_min_max_normalize_constant_input_returns_output_minimum() -> None:
    values = np.array([5.0, 5.0, 5.0])

    result = min_max_normalize(
        values,
        output_min=2.0,
        output_max=8.0,
    )

    np.testing.assert_allclose(
        result,
        np.array([2.0, 2.0, 2.0]),
    )


def test_min_max_normalize_preserves_empty_input() -> None:
    values = np.array([], dtype=np.float64)

    result = min_max_normalize(values)

    np.testing.assert_array_equal(
        result,
        values,
    )


def test_min_max_normalize_rejects_invalid_output_range() -> None:
    values = np.array([1.0, 2.0, 3.0])

    with pytest.raises(
        ValueError,
        match="output_min must be less than output_max",
    ):
        min_max_normalize(
            values,
            output_min=1.0,
            output_max=1.0,
        )


@pytest.mark.parametrize(
    "output_min, output_max",
    [
        (np.nan, 1.0),
        (0.0, np.inf),
        (-np.inf, 1.0),
    ],
)
def test_min_max_normalize_rejects_non_finite_output_bounds(
    output_min: float,
    output_max: float,
) -> None:
    values = np.array([1.0, 2.0, 3.0])

    with pytest.raises(
        ValueError,
        match="Normalization bounds must be finite",
    ):
        min_max_normalize(
            values,
            output_min=output_min,
            output_max=output_max,
        )


def test_min_max_normalize_rejects_non_finite_input() -> None:
    values = np.array([1.0, np.nan, 3.0])

    with pytest.raises(
        ValueError,
        match="Input contains NaN or infinite values",
    ):
        min_max_normalize(values)


def test_standardize_produces_zero_mean_and_unit_standard_deviation() -> None:
    values = np.array([10.0, 20.0, 30.0, 40.0])

    result = standardize(values)

    np.testing.assert_allclose(
        result.mean(),
        0.0,
    )
    np.testing.assert_allclose(
        result.std(),
        1.0,
    )


def test_standardize_supports_sample_standard_deviation() -> None:
    values = np.array([10.0, 20.0, 30.0])

    result = standardize(
        values,
        ddof=1,
    )

    np.testing.assert_allclose(
        result.mean(),
        0.0,
    )
    np.testing.assert_allclose(
        result.std(ddof=1),
        1.0,
    )


def test_standardize_constant_input_returns_zeros() -> None:
    values = np.array([7.0, 7.0, 7.0])

    result = standardize(values)

    np.testing.assert_array_equal(
        result,
        np.zeros_like(values),
    )


def test_standardize_preserves_empty_input() -> None:
    values = np.array([], dtype=np.float64)

    result = standardize(values)

    np.testing.assert_array_equal(
        result,
        values,
    )


def test_standardize_rejects_negative_ddof() -> None:
    values = np.array([1.0, 2.0, 3.0])

    with pytest.raises(ValueError, match="ddof must be non-negative"):
        standardize(
            values,
            ddof=-1,
        )


def test_standardize_rejects_non_finite_input() -> None:
    values = np.array([1.0, np.inf, 3.0])

    with pytest.raises(
        ValueError,
        match="Input contains NaN or infinite values",
    ):
        standardize(values)


def test_normalize_by_max_abs_scales_to_unit_magnitude() -> None:
    values = np.array([-10.0, -5.0, 0.0, 5.0, 10.0])

    result = normalize_by_max_abs(values)

    np.testing.assert_allclose(
        result,
        np.array([-1.0, -0.5, 0.0, 0.5, 1.0]),
    )


def test_normalize_by_max_abs_handles_zero_input() -> None:
    values = np.zeros(4, dtype=np.float64)

    result = normalize_by_max_abs(values)

    np.testing.assert_array_equal(
        result,
        values,
    )


def test_normalize_by_max_abs_preserves_empty_input() -> None:
    values = np.array([], dtype=np.float64)

    result = normalize_by_max_abs(values)

    np.testing.assert_array_equal(
        result,
        values,
    )


def test_normalize_by_max_abs_rejects_non_finite_input() -> None:
    values = np.array([1.0, np.nan, 3.0])

    with pytest.raises(
        ValueError,
        match="Input contains NaN or infinite values",
    ):
        normalize_by_max_abs(values)


def test_normalize_columns_normalizes_each_column() -> None:
    values = np.array(
        [
            [10.0, 100.0],
            [20.0, 200.0],
            [30.0, 300.0],
        ]
    )

    result = normalize_columns(values)

    expected = np.array(
        [
            [0.0, 0.0],
            [0.5, 0.5],
            [1.0, 1.0],
        ]
    )

    np.testing.assert_allclose(
        result,
        expected,
    )


def test_normalize_columns_normalizes_each_row_when_axis_one() -> None:
    values = np.array(
        [
            [10.0, 20.0, 30.0],
            [100.0, 200.0, 300.0],
        ]
    )

    result = normalize_columns(
        values,
        axis=1,
    )

    expected = np.array(
        [
            [0.0, 0.5, 1.0],
            [0.0, 0.5, 1.0],
        ]
    )

    np.testing.assert_allclose(
        result,
        expected,
    )


def test_normalize_columns_maps_constant_columns_to_zero() -> None:
    values = np.array(
        [
            [10.0, 5.0],
            [10.0, 10.0],
            [10.0, 15.0],
        ]
    )

    result = normalize_columns(values)

    expected = np.array(
        [
            [0.0, 0.0],
            [0.0, 0.5],
            [0.0, 1.0],
        ]
    )

    np.testing.assert_allclose(
        result,
        expected,
    )


def test_normalize_columns_rejects_one_dimensional_input() -> None:
    values = np.array([1.0, 2.0, 3.0])

    with pytest.raises(
        ValueError,
        match="requires a two-dimensional array",
    ):
        normalize_columns(values)


def test_normalize_columns_rejects_invalid_axis() -> None:
    values = np.ones((2, 3))

    with pytest.raises(
        ValueError,
        match="axis must be 0 or 1",
    ):
        normalize_columns(
            values,
            axis=2,
        )


def test_normalize_columns_rejects_non_finite_input() -> None:
    values = np.array(
        [
            [1.0, 2.0],
            [3.0, np.inf],
        ]
    )

    with pytest.raises(
        ValueError,
        match="Input contains NaN or infinite values",
    ):
        normalize_columns(values)