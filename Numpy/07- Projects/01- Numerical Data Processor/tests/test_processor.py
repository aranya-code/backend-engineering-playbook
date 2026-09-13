import numpy as np
import pytest

from src.processor import aggregate, clean_values, normalize, process


def test_clean_values_converts_to_float64() -> None:
    values = np.array([10, 20, 30], dtype=np.int32)

    actual = clean_values(values)

    np.testing.assert_array_equal(
        actual,
        np.array([10.0, 20.0, 30.0]),
    )
    assert actual.dtype == np.float64


def test_clean_values_clips_to_minimum() -> None:
    values = np.array([-10.0, 5.0, 20.0])

    actual = clean_values(
        values,
        minimum=0.0,
    )

    np.testing.assert_array_equal(
        actual,
        values,
    )


def test_clean_values_applies_positive_minimum() -> None:
    values = np.array([10.0, 20.0, 30.0])

    actual = clean_values(
        values,
        minimum=15.0,
    )

    np.testing.assert_array_equal(
        actual,
        np.array([15.0, 20.0, 30.0]),
    )


def test_clean_values_applies_maximum() -> None:
    values = np.array([10.0, 50.0, 100.0])

    actual = clean_values(
        values,
        maximum=60.0,
    )

    np.testing.assert_array_equal(
        actual,
        np.array([10.0, 50.0, 60.0]),
    )


def test_clean_values_rejects_non_finite_values() -> None:
    values = np.array([10.0, np.nan, 30.0])

    with pytest.raises(
        ValueError,
        match="NaN or infinite",
    ):
        clean_values(values)


def test_clean_values_rejects_invalid_bounds() -> None:
    values = np.array([10.0, 20.0, 30.0])

    with pytest.raises(
        ValueError,
        match="minimum must not exceed maximum",
    ):
        clean_values(
            values,
            minimum=100.0,
            maximum=50.0,
        )


def test_clean_values_rejects_non_one_dimensional_input() -> None:
    values = np.array(
        [[10.0, 20.0]],
        dtype=np.float64,
    )

    with pytest.raises(
        ValueError,
        match="one-dimensional",
    ):
        clean_values(values)


def test_normalize_maps_values_to_zero_one_range() -> None:
    values = np.array([10.0, 20.0, 30.0])

    actual = normalize(values)

    np.testing.assert_allclose(
        actual,
        np.array([0.0, 0.5, 1.0]),
    )


def test_normalize_handles_constant_values() -> None:
    values = np.array([10.0, 10.0, 10.0])

    actual = normalize(values)

    np.testing.assert_array_equal(
        actual,
        np.zeros(3),
    )


def test_normalize_handles_empty_array() -> None:
    values = np.array([], dtype=np.float64)

    actual = normalize(values)

    assert actual.size == 0
    assert actual.dtype == np.float64


def test_aggregate_returns_expected_statistics() -> None:
    values = np.array(
        [10.0, 20.0, 30.0, 40.0],
        dtype=np.float64,
    )

    actual = aggregate(values)

    assert actual["count"] == 4.0
    assert actual["sum"] == 100.0
    assert actual["mean"] == 25.0
    assert actual["median"] == 25.0
    assert actual["minimum"] == 10.0
    assert actual["maximum"] == 40.0
    assert actual["standard_deviation"] == pytest.approx(
        np.sqrt(125.0)
    )


def test_aggregate_rejects_empty_array() -> None:
    values = np.array([], dtype=np.float64)

    with pytest.raises(
        ValueError,
        match="empty array",
    ):
        aggregate(values)


def test_aggregate_rejects_non_finite_values() -> None:
    values = np.array(
        [10.0, np.inf, 30.0],
        dtype=np.float64,
    )

    with pytest.raises(
        ValueError,
        match="non-finite",
    ):
        aggregate(values)


def test_process_returns_normalized_values_and_statistics() -> None:
    values = np.array(
        [10.0, 20.0, 30.0],
        dtype=np.float64,
    )

    normalized, statistics = process(values)

    np.testing.assert_allclose(
        normalized,
        np.array([0.0, 0.5, 1.0]),
    )

    assert statistics["count"] == 3.0
    assert statistics["sum"] == 60.0
    assert statistics["mean"] == 20.0
    assert statistics["minimum"] == 10.0
    assert statistics["maximum"] == 30.0


def test_process_applies_processing_bounds() -> None:
    values = np.array(
        [10.0, 50.0, 100.0],
        dtype=np.float64,
    )

    normalized, statistics = process(
        values,
        minimum=20.0,
        maximum=80.0,
    )

    np.testing.assert_allclose(
        normalized,
        np.array([0.0, 0.5, 1.0]),
    )

    assert statistics["minimum"] == 20.0
    assert statistics["maximum"] == 80.0
    assert statistics["sum"] == 150.0


def test_process_rejects_invalid_input() -> None:
    values = np.array(
        [10.0, np.nan, 30.0],
        dtype=np.float64,
    )

    with pytest.raises(
        ValueError,
        match="NaN or infinite",
    ):
        process(values)

import numpy as np
import pytest

from src.processor import aggregate, clean_values, normalize, process


def test_clean_values_converts_to_float64() -> None:
    values = np.array([10, 20, 30], dtype=np.int32)

    actual = clean_values(values)

    np.testing.assert_array_equal(
        actual,
        np.array([10.0, 20.0, 30.0]),
    )
    assert actual.dtype == np.float64


def test_clean_values_clips_to_minimum() -> None:
    values = np.array([-10.0, 5.0, 20.0])

    actual = clean_values(
        values,
        minimum=0.0,
    )

    np.testing.assert_array_equal(
        actual,
        values,
    )


def test_clean_values_applies_positive_minimum() -> None:
    values = np.array([10.0, 20.0, 30.0])

    actual = clean_values(
        values,
        minimum=15.0,
    )

    np.testing.assert_array_equal(
        actual,
        np.array([15.0, 20.0, 30.0]),
    )


def test_clean_values_applies_maximum() -> None:
    values = np.array([10.0, 50.0, 100.0])

    actual = clean_values(
        values,
        maximum=60.0,
    )

    np.testing.assert_array_equal(
        actual,
        np.array([10.0, 50.0, 60.0]),
    )


def test_clean_values_rejects_non_finite_values() -> None:
    values = np.array([10.0, np.nan, 30.0])

    with pytest.raises(
        ValueError,
        match="NaN or infinite",
    ):
        clean_values(values)


def test_clean_values_rejects_invalid_bounds() -> None:
    values = np.array([10.0, 20.0, 30.0])

    with pytest.raises(
        ValueError,
        match="minimum must not exceed maximum",
    ):
        clean_values(
            values,
            minimum=100.0,
            maximum=50.0,
        )


def test_clean_values_rejects_non_one_dimensional_input() -> None:
    values = np.array(
        [[10.0, 20.0]],
        dtype=np.float64,
    )

    with pytest.raises(
        ValueError,
        match="one-dimensional",
    ):
        clean_values(values)


def test_normalize_maps_values_to_zero_one_range() -> None:
    values = np.array([10.0, 20.0, 30.0])

    actual = normalize(values)

    np.testing.assert_allclose(
        actual,
        np.array([0.0, 0.5, 1.0]),
    )


def test_normalize_handles_constant_values() -> None:
    values = np.array([10.0, 10.0, 10.0])

    actual = normalize(values)

    np.testing.assert_array_equal(
        actual,
        np.zeros(3),
    )


def test_normalize_handles_empty_array() -> None:
    values = np.array([], dtype=np.float64)

    actual = normalize(values)

    assert actual.size == 0
    assert actual.dtype == np.float64


def test_aggregate_returns_expected_statistics() -> None:
    values = np.array(
        [10.0, 20.0, 30.0, 40.0],
        dtype=np.float64,
    )

    actual = aggregate(values)

    assert actual["count"] == 4.0
    assert actual["sum"] == 100.0
    assert actual["mean"] == 25.0
    assert actual["median"] == 25.0
    assert actual["minimum"] == 10.0
    assert actual["maximum"] == 40.0
    assert actual["standard_deviation"] == pytest.approx(
        np.sqrt(125.0)
    )


def test_aggregate_rejects_empty_array() -> None:
    values = np.array([], dtype=np.float64)

    with pytest.raises(
        ValueError,
        match="empty array",
    ):
        aggregate(values)


def test_aggregate_rejects_non_finite_values() -> None:
    values = np.array(
        [10.0, np.inf, 30.0],
        dtype=np.float64,
    )

    with pytest.raises(
        ValueError,
        match="non-finite",
    ):
        aggregate(values)


def test_process_returns_normalized_values_and_statistics() -> None:
    values = np.array(
        [10.0, 20.0, 30.0],
        dtype=np.float64,
    )

    normalized, statistics = process(values)

    np.testing.assert_allclose(
        normalized,
        np.array([0.0, 0.5, 1.0]),
    )

    assert statistics["count"] == 3.0
    assert statistics["sum"] == 60.0
    assert statistics["mean"] == 20.0
    assert statistics["minimum"] == 10.0
    assert statistics["maximum"] == 30.0


def test_process_applies_processing_bounds() -> None:
    values = np.array(
        [10.0, 50.0, 100.0],
        dtype=np.float64,
    )

    normalized, statistics = process(
        values,
        minimum=20.0,
        maximum=80.0,
    )

    np.testing.assert_allclose(
        normalized,
        np.array([0.0, 0.5, 1.0]),
    )

    assert statistics["minimum"] == 20.0
    assert statistics["maximum"] == 80.0
    assert statistics["sum"] == 150.0


def test_process_rejects_invalid_input() -> None:
    values = np.array(
        [10.0, np.nan, 30.0],
        dtype=np.float64,
    )

    with pytest.raises(
        ValueError,
        match="NaN or infinite",
    ):
        process(values)