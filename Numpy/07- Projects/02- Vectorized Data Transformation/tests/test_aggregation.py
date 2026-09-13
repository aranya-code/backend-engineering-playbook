"""Tests for numerical aggregation utilities."""

from __future__ import annotations

import numpy as np
import pytest

from src.aggregation import (
    finite_statistics,
    max_value,
    mean_values,
    median_value,
    min_value,
    nanmean_values,
    percentile_value,
    sum_values,
)


def test_sum_values_returns_total() -> None:
    values = np.array([10.0, 20.0, 30.0])

    result = sum_values(values)

    assert result == pytest.approx(60.0)


def test_sum_values_supports_axis() -> None:
    values = np.array(
        [
            [1.0, 2.0],
            [3.0, 4.0],
        ]
    )

    result = sum_values(values, axis=0)

    np.testing.assert_allclose(
        result,
        np.array([4.0, 6.0]),
    )


def test_sum_values_supports_explicit_dtype() -> None:
    values = np.array(
        [1, 2, 3],
        dtype=np.int16,
    )

    result = sum_values(
        values,
        dtype=np.int64,
    )

    assert result == 6
    assert np.asarray(result).dtype == np.dtype(np.int64)


def test_sum_values_handles_empty_array() -> None:
    values = np.array([], dtype=np.float64)

    result = sum_values(values)

    assert result == pytest.approx(0.0)


def test_sum_values_rejects_non_numeric_array() -> None:
    values = np.array(["10", "20", "30"])

    with pytest.raises(TypeError, match="Expected a numeric array"):
        sum_values(values)


def test_mean_values_returns_arithmetic_mean() -> None:
    values = np.array([10.0, 20.0, 30.0])

    result = mean_values(values)

    assert result == pytest.approx(20.0)


def test_mean_values_supports_axis() -> None:
    values = np.array(
        [
            [1.0, 2.0],
            [3.0, 4.0],
        ]
    )

    result = mean_values(values, axis=1)

    np.testing.assert_allclose(
        result,
        np.array([1.5, 3.5]),
    )


def test_mean_values_rejects_empty_array() -> None:
    values = np.array([], dtype=np.float64)

    with pytest.raises(
        ValueError,
        match="Cannot calculate the mean of an empty array",
    ):
        mean_values(values)


def test_min_value_returns_smallest_value() -> None:
    values = np.array([8.0, 3.0, 5.0, 1.0])

    result = min_value(values)

    assert result == pytest.approx(1.0)


def test_min_value_supports_axis() -> None:
    values = np.array(
        [
            [8.0, 3.0],
            [5.0, 1.0],
        ]
    )

    result = min_value(values, axis=0)

    np.testing.assert_allclose(
        result,
        np.array([5.0, 1.0]),
    )


def test_min_value_rejects_empty_array() -> None:
    values = np.array([], dtype=np.float64)

    with pytest.raises(
        ValueError,
        match="Cannot calculate the minimum of an empty array",
    ):
        min_value(values)


def test_max_value_returns_largest_value() -> None:
    values = np.array([8.0, 3.0, 5.0, 1.0])

    result = max_value(values)

    assert result == pytest.approx(8.0)


def test_max_value_supports_axis() -> None:
    values = np.array(
        [
            [8.0, 3.0],
            [5.0, 1.0],
        ]
    )

    result = max_value(values, axis=1)

    np.testing.assert_allclose(
        result,
        np.array([8.0, 5.0]),
    )


def test_max_value_rejects_empty_array() -> None:
    values = np.array([], dtype=np.float64)

    with pytest.raises(
        ValueError,
        match="Cannot calculate the maximum of an empty array",
    ):
        max_value(values)


def test_median_value_returns_middle_value() -> None:
    values = np.array([30.0, 10.0, 20.0])

    result = median_value(values)

    assert result == pytest.approx(20.0)


def test_median_value_handles_even_number_of_values() -> None:
    values = np.array([10.0, 20.0, 30.0, 40.0])

    result = median_value(values)

    assert result == pytest.approx(25.0)


def test_median_value_supports_axis() -> None:
    values = np.array(
        [
            [1.0, 9.0],
            [5.0, 3.0],
        ]
    )

    result = median_value(values, axis=0)

    np.testing.assert_allclose(
        result,
        np.array([3.0, 6.0]),
    )


def test_median_value_rejects_empty_array() -> None:
    values = np.array([], dtype=np.float64)

    with pytest.raises(
        ValueError,
        match="Cannot calculate the median of an empty array",
    ):
        median_value(values)


@pytest.mark.parametrize("percentile", [0.0, 25.0, 50.0, 75.0, 100.0])
def test_percentile_value_accepts_valid_percentiles(
    percentile: float,
) -> None:
    values = np.array([10.0, 20.0, 30.0, 40.0])

    result = percentile_value(
        values,
        percentile,
    )

    expected = np.percentile(
        values,
        percentile,
    )

    assert result == pytest.approx(expected)


@pytest.mark.parametrize(
    "percentile",
    [-1.0, 100.1, np.nan, np.inf],
)
def test_percentile_value_rejects_invalid_percentile(
    percentile: float,
) -> None:
    values = np.array([10.0, 20.0, 30.0])

    with pytest.raises(ValueError):
        percentile_value(
            values,
            percentile,
        )


def test_percentile_value_supports_axis() -> None:
    values = np.array(
        [
            [1.0, 2.0],
            [3.0, 4.0],
        ]
    )

    result = percentile_value(
        values,
        50.0,
        axis=0,
    )

    np.testing.assert_allclose(
        result,
        np.array([2.0, 3.0]),
    )


def test_percentile_value_rejects_empty_array() -> None:
    values = np.array([], dtype=np.float64)

    with pytest.raises(
        ValueError,
        match="Cannot calculate a percentile of an empty array",
    ):
        percentile_value(
            values,
            50.0,
        )


def test_nanmean_values_ignores_nan_values() -> None:
    values = np.array([10.0, np.nan, 20.0, 30.0])

    result = nanmean_values(values)

    assert result == pytest.approx(20.0)


def test_nanmean_values_supports_axis() -> None:
    values = np.array(
        [
            [1.0, np.nan],
            [3.0, 5.0],
        ]
    )

    result = nanmean_values(values, axis=0)

    np.testing.assert_allclose(
        result,
        np.array([2.0, 5.0]),
    )


def test_nanmean_values_rejects_empty_array() -> None:
    values = np.array([], dtype=np.float64)

    with pytest.raises(
        ValueError,
        match="Cannot calculate the mean of an empty array",
    ):
        nanmean_values(values)


def test_finite_statistics_returns_expected_metrics() -> None:
    values = np.array(
        [1.0, 2.0, 3.0, np.nan, np.inf, -np.inf]
    )

    result = finite_statistics(values)

    assert result["count"] == 3
    assert result["sum"] == pytest.approx(6.0)
    assert result["mean"] == pytest.approx(2.0)
    assert result["minimum"] == pytest.approx(1.0)
    assert result["maximum"] == pytest.approx(3.0)
    assert result["median"] == pytest.approx(2.0)
    assert result["standard_deviation"] == pytest.approx(
        np.std(np.array([1.0, 2.0, 3.0]))
    )


def test_finite_statistics_ignores_non_finite_values() -> None:
    values = np.array(
        [np.nan, np.inf, -np.inf, 5.0, 15.0]
    )

    result = finite_statistics(values)

    assert result["count"] == 2
    assert result["mean"] == pytest.approx(10.0)
    assert result["minimum"] == pytest.approx(5.0)
    assert result["maximum"] == pytest.approx(15.0)


def test_finite_statistics_rejects_array_without_finite_values() -> None:
    values = np.array(
        [np.nan, np.inf, -np.inf]
    )

    with pytest.raises(
        ValueError,
        match="Input does not contain finite numerical values",
    ):
        finite_statistics(values)


def test_finite_statistics_accepts_integer_input() -> None:
    values = np.array([1, 2, 3], dtype=np.int64)

    result = finite_statistics(values)

    assert result["count"] == 3
    assert result["sum"] == pytest.approx(6.0)
    assert result["mean"] == pytest.approx(2.0)

"""Tests for numerical aggregation utilities."""

from __future__ import annotations

import numpy as np
import pytest

from src.aggregation import (
    finite_statistics,
    max_value,
    mean_values,
    median_value,
    min_value,
    nanmean_values,
    percentile_value,
    sum_values,
)


def test_sum_values_returns_total() -> None:
    values = np.array([10.0, 20.0, 30.0])

    result = sum_values(values)

    assert result == pytest.approx(60.0)


def test_sum_values_supports_axis() -> None:
    values = np.array(
        [
            [1.0, 2.0],
            [3.0, 4.0],
        ]
    )

    result = sum_values(values, axis=0)

    np.testing.assert_allclose(
        result,
        np.array([4.0, 6.0]),
    )


def test_sum_values_supports_explicit_dtype() -> None:
    values = np.array(
        [1, 2, 3],
        dtype=np.int16,
    )

    result = sum_values(
        values,
        dtype=np.int64,
    )

    assert result == 6
    assert np.asarray(result).dtype == np.dtype(np.int64)


def test_sum_values_handles_empty_array() -> None:
    values = np.array([], dtype=np.float64)

    result = sum_values(values)

    assert result == pytest.approx(0.0)


def test_sum_values_rejects_non_numeric_array() -> None:
    values = np.array(["10", "20", "30"])

    with pytest.raises(TypeError, match="Expected a numeric array"):
        sum_values(values)


def test_mean_values_returns_arithmetic_mean() -> None:
    values = np.array([10.0, 20.0, 30.0])

    result = mean_values(values)

    assert result == pytest.approx(20.0)


def test_mean_values_supports_axis() -> None:
    values = np.array(
        [
            [1.0, 2.0],
            [3.0, 4.0],
        ]
    )

    result = mean_values(values, axis=1)

    np.testing.assert_allclose(
        result,
        np.array([1.5, 3.5]),
    )


def test_mean_values_rejects_empty_array() -> None:
    values = np.array([], dtype=np.float64)

    with pytest.raises(
        ValueError,
        match="Cannot calculate the mean of an empty array",
    ):
        mean_values(values)


def test_min_value_returns_smallest_value() -> None:
    values = np.array([8.0, 3.0, 5.0, 1.0])

    result = min_value(values)

    assert result == pytest.approx(1.0)


def test_min_value_supports_axis() -> None:
    values = np.array(
        [
            [8.0, 3.0],
            [5.0, 1.0],
        ]
    )

    result = min_value(values, axis=0)

    np.testing.assert_allclose(
        result,
        np.array([5.0, 1.0]),
    )


def test_min_value_rejects_empty_array() -> None:
    values = np.array([], dtype=np.float64)

    with pytest.raises(
        ValueError,
        match="Cannot calculate the minimum of an empty array",
    ):
        min_value(values)


def test_max_value_returns_largest_value() -> None:
    values = np.array([8.0, 3.0, 5.0, 1.0])

    result = max_value(values)

    assert result == pytest.approx(8.0)


def test_max_value_supports_axis() -> None:
    values = np.array(
        [
            [8.0, 3.0],
            [5.0, 1.0],
        ]
    )

    result = max_value(values, axis=1)

    np.testing.assert_allclose(
        result,
        np.array([8.0, 5.0]),
    )


def test_max_value_rejects_empty_array() -> None:
    values = np.array([], dtype=np.float64)

    with pytest.raises(
        ValueError,
        match="Cannot calculate the maximum of an empty array",
    ):
        max_value(values)


def test_median_value_returns_middle_value() -> None:
    values = np.array([30.0, 10.0, 20.0])

    result = median_value(values)

    assert result == pytest.approx(20.0)


def test_median_value_handles_even_number_of_values() -> None:
    values = np.array([10.0, 20.0, 30.0, 40.0])

    result = median_value(values)

    assert result == pytest.approx(25.0)


def test_median_value_supports_axis() -> None:
    values = np.array(
        [
            [1.0, 9.0],
            [5.0, 3.0],
        ]
    )

    result = median_value(values, axis=0)

    np.testing.assert_allclose(
        result,
        np.array([3.0, 6.0]),
    )


def test_median_value_rejects_empty_array() -> None:
    values = np.array([], dtype=np.float64)

    with pytest.raises(
        ValueError,
        match="Cannot calculate the median of an empty array",
    ):
        median_value(values)


@pytest.mark.parametrize("percentile", [0.0, 25.0, 50.0, 75.0, 100.0])
def test_percentile_value_accepts_valid_percentiles(
    percentile: float,
) -> None:
    values = np.array([10.0, 20.0, 30.0, 40.0])

    result = percentile_value(
        values,
        percentile,
    )

    expected = np.percentile(
        values,
        percentile,
    )

    assert result == pytest.approx(expected)


@pytest.mark.parametrize(
    "percentile",
    [-1.0, 100.1, np.nan, np.inf],
)
def test_percentile_value_rejects_invalid_percentile(
    percentile: float,
) -> None:
    values = np.array([10.0, 20.0, 30.0])

    with pytest.raises(ValueError):
        percentile_value(
            values,
            percentile,
        )


def test_percentile_value_supports_axis() -> None:
    values = np.array(
        [
            [1.0, 2.0],
            [3.0, 4.0],
        ]
    )

    result = percentile_value(
        values,
        50.0,
        axis=0,
    )

    np.testing.assert_allclose(
        result,
        np.array([2.0, 3.0]),
    )


def test_percentile_value_rejects_empty_array() -> None:
    values = np.array([], dtype=np.float64)

    with pytest.raises(
        ValueError,
        match="Cannot calculate a percentile of an empty array",
    ):
        percentile_value(
            values,
            50.0,
        )


def test_nanmean_values_ignores_nan_values() -> None:
    values = np.array([10.0, np.nan, 20.0, 30.0])

    result = nanmean_values(values)

    assert result == pytest.approx(20.0)


def test_nanmean_values_supports_axis() -> None:
    values = np.array(
        [
            [1.0, np.nan],
            [3.0, 5.0],
        ]
    )

    result = nanmean_values(values, axis=0)

    np.testing.assert_allclose(
        result,
        np.array([2.0, 5.0]),
    )


def test_nanmean_values_rejects_empty_array() -> None:
    values = np.array([], dtype=np.float64)

    with pytest.raises(
        ValueError,
        match="Cannot calculate the mean of an empty array",
    ):
        nanmean_values(values)


def test_finite_statistics_returns_expected_metrics() -> None:
    values = np.array(
        [1.0, 2.0, 3.0, np.nan, np.inf, -np.inf]
    )

    result = finite_statistics(values)

    assert result["count"] == 3
    assert result["sum"] == pytest.approx(6.0)
    assert result["mean"] == pytest.approx(2.0)
    assert result["minimum"] == pytest.approx(1.0)
    assert result["maximum"] == pytest.approx(3.0)
    assert result["median"] == pytest.approx(2.0)
    assert result["standard_deviation"] == pytest.approx(
        np.std(np.array([1.0, 2.0, 3.0]))
    )


def test_finite_statistics_ignores_non_finite_values() -> None:
    values = np.array(
        [np.nan, np.inf, -np.inf, 5.0, 15.0]
    )

    result = finite_statistics(values)

    assert result["count"] == 2
    assert result["mean"] == pytest.approx(10.0)
    assert result["minimum"] == pytest.approx(5.0)
    assert result["maximum"] == pytest.approx(15.0)


def test_finite_statistics_rejects_array_without_finite_values() -> None:
    values = np.array(
        [np.nan, np.inf, -np.inf]
    )

    with pytest.raises(
        ValueError,
        match="Input does not contain finite numerical values",
    ):
        finite_statistics(values)


def test_finite_statistics_accepts_integer_input() -> None:
    values = np.array([1, 2, 3], dtype=np.int64)

    result = finite_statistics(values)

    assert result["count"] == 3
    assert result["sum"] == pytest.approx(6.0)
    assert result["mean"] == pytest.approx(2.0)