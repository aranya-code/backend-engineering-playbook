import numpy as np
import pytest

from src.statistics import (
    describe,
    maximum,
    mean,
    median,
    minimum,
    percentiles,
    standard_deviation,
    variance,
)


@pytest.fixture
def values() -> np.ndarray:
    return np.array(
        [10.0, 20.0, 30.0, 40.0, 50.0],
        dtype=np.float64,
    )


def test_mean(values: np.ndarray) -> None:
    assert mean(values) == pytest.approx(30.0)


def test_median(values: np.ndarray) -> None:
    assert median(values) == pytest.approx(30.0)


def test_minimum(values: np.ndarray) -> None:
    assert minimum(values) == pytest.approx(10.0)


def test_maximum(values: np.ndarray) -> None:
    assert maximum(values) == pytest.approx(50.0)


def test_standard_deviation(values: np.ndarray) -> None:
    assert standard_deviation(values) == pytest.approx(
        np.sqrt(200.0)
    )


def test_variance(values: np.ndarray) -> None:
    assert variance(values) == pytest.approx(200.0)


def test_percentiles(values: np.ndarray) -> None:
    actual = percentiles(
        values,
        percentages=(25.0, 50.0, 75.0),
    )

    assert actual == {
        25.0: 20.0,
        50.0: 30.0,
        75.0: 40.0,
    }


def test_percentiles_supports_single_percentage(
    values: np.ndarray,
) -> None:
    actual = percentiles(
        values,
        percentages=(50.0,),
    )

    assert actual == {50.0: 30.0}


def test_percentiles_returns_empty_mapping_for_no_percentages(
    values: np.ndarray,
) -> None:
    assert percentiles(
        values,
        percentages=(),
    ) == {}


@pytest.mark.parametrize(
    "percentage",
    [-1.0, 100.1],
)
def test_percentiles_rejects_invalid_percentage(
    values: np.ndarray,
    percentage: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="between 0 and 100",
    ):
        percentiles(
            values,
            percentages=(percentage,),
        )


@pytest.mark.parametrize(
    "function",
    [
        mean,
        median,
        minimum,
        maximum,
        standard_deviation,
        variance,
        describe,
    ],
)
def test_statistics_reject_empty_input(
    function,
) -> None:
    values = np.array([], dtype=np.float64)

    with pytest.raises(
        ValueError,
        match="empty array",
    ):
        function(values)


@pytest.mark.parametrize(
    "function",
    [
        mean,
        median,
        minimum,
        maximum,
        standard_deviation,
        variance,
        describe,
    ],
)
def test_statistics_reject_non_finite_input(
    function,
) -> None:
    values = np.array(
        [10.0, np.nan, 30.0],
        dtype=np.float64,
    )

    with pytest.raises(
        ValueError,
        match="finite numerical values",
    ):
        function(values)


def test_statistics_reject_non_one_dimensional_input() -> None:
    values = np.array(
        [
            [10.0, 20.0],
            [30.0, 40.0],
        ],
        dtype=np.float64,
    )

    with pytest.raises(
        ValueError,
        match="one-dimensional",
    ):
        mean(values)


def test_statistics_convert_integer_input_to_float() -> None:
    values = np.array(
        [10, 20, 30],
        dtype=np.int32,
    )

    assert mean(values) == pytest.approx(20.0)


def test_describe_returns_expected_statistics(
    values: np.ndarray,
) -> None:
    actual = describe(values)

    assert actual["count"] == 5.0
    assert actual["mean"] == pytest.approx(30.0)
    assert actual["median"] == pytest.approx(30.0)
    assert actual["minimum"] == pytest.approx(10.0)
    assert actual["maximum"] == pytest.approx(50.0)
    assert actual["variance"] == pytest.approx(200.0)
    assert actual["standard_deviation"] == pytest.approx(
        np.sqrt(200.0)
    )
    assert actual["p25"] == pytest.approx(20.0)
    assert actual["p75"] == pytest.approx(40.0)


def test_describe_preserves_expected_statistical_relationships() -> None:
    values = np.array(
        [5.0, 5.0, 5.0, 5.0],
        dtype=np.float64,
    )

    actual = describe(values)

    assert actual["mean"] == 5.0
    assert actual["median"] == 5.0
    assert actual["minimum"] == 5.0
    assert actual["maximum"] == 5.0
    assert actual["variance"] == 0.0
    assert actual["standard_deviation"] == 0.0
    assert actual["p25"] == 5.0
    assert actual["p75"] == 5.0

import numpy as np
import pytest

from src.statistics import (
    describe,
    maximum,
    mean,
    median,
    minimum,
    percentiles,
    standard_deviation,
    variance,
)


@pytest.fixture
def values() -> np.ndarray:
    return np.array(
        [10.0, 20.0, 30.0, 40.0, 50.0],
        dtype=np.float64,
    )


def test_mean(values: np.ndarray) -> None:
    assert mean(values) == pytest.approx(30.0)


def test_median(values: np.ndarray) -> None:
    assert median(values) == pytest.approx(30.0)


def test_minimum(values: np.ndarray) -> None:
    assert minimum(values) == pytest.approx(10.0)


def test_maximum(values: np.ndarray) -> None:
    assert maximum(values) == pytest.approx(50.0)


def test_standard_deviation(values: np.ndarray) -> None:
    assert standard_deviation(values) == pytest.approx(
        np.sqrt(200.0)
    )


def test_variance(values: np.ndarray) -> None:
    assert variance(values) == pytest.approx(200.0)


def test_percentiles(values: np.ndarray) -> None:
    actual = percentiles(
        values,
        percentages=(25.0, 50.0, 75.0),
    )

    assert actual == {
        25.0: 20.0,
        50.0: 30.0,
        75.0: 40.0,
    }


def test_percentiles_supports_single_percentage(
    values: np.ndarray,
) -> None:
    actual = percentiles(
        values,
        percentages=(50.0,),
    )

    assert actual == {50.0: 30.0}


def test_percentiles_returns_empty_mapping_for_no_percentages(
    values: np.ndarray,
) -> None:
    assert percentiles(
        values,
        percentages=(),
    ) == {}


@pytest.mark.parametrize(
    "percentage",
    [-1.0, 100.1],
)
def test_percentiles_rejects_invalid_percentage(
    values: np.ndarray,
    percentage: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="between 0 and 100",
    ):
        percentiles(
            values,
            percentages=(percentage,),
        )


@pytest.mark.parametrize(
    "function",
    [
        mean,
        median,
        minimum,
        maximum,
        standard_deviation,
        variance,
        describe,
    ],
)
def test_statistics_reject_empty_input(
    function,
) -> None:
    values = np.array([], dtype=np.float64)

    with pytest.raises(
        ValueError,
        match="empty array",
    ):
        function(values)


@pytest.mark.parametrize(
    "function",
    [
        mean,
        median,
        minimum,
        maximum,
        standard_deviation,
        variance,
        describe,
    ],
)
def test_statistics_reject_non_finite_input(
    function,
) -> None:
    values = np.array(
        [10.0, np.nan, 30.0],
        dtype=np.float64,
    )

    with pytest.raises(
        ValueError,
        match="finite numerical values",
    ):
        function(values)


def test_statistics_reject_non_one_dimensional_input() -> None:
    values = np.array(
        [
            [10.0, 20.0],
            [30.0, 40.0],
        ],
        dtype=np.float64,
    )

    with pytest.raises(
        ValueError,
        match="one-dimensional",
    ):
        mean(values)


def test_statistics_convert_integer_input_to_float() -> None:
    values = np.array(
        [10, 20, 30],
        dtype=np.int32,
    )

    assert mean(values) == pytest.approx(20.0)


def test_describe_returns_expected_statistics(
    values: np.ndarray,
) -> None:
    actual = describe(values)

    assert actual["count"] == 5.0
    assert actual["mean"] == pytest.approx(30.0)
    assert actual["median"] == pytest.approx(30.0)
    assert actual["minimum"] == pytest.approx(10.0)
    assert actual["maximum"] == pytest.approx(50.0)
    assert actual["variance"] == pytest.approx(200.0)
    assert actual["standard_deviation"] == pytest.approx(
        np.sqrt(200.0)
    )
    assert actual["p25"] == pytest.approx(20.0)
    assert actual["p75"] == pytest.approx(40.0)


def test_describe_preserves_expected_statistical_relationships() -> None:
    values = np.array(
        [5.0, 5.0, 5.0, 5.0],
        dtype=np.float64,
    )

    actual = describe(values)

    assert actual["mean"] == 5.0
    assert actual["median"] == 5.0
    assert actual["minimum"] == 5.0
    assert actual["maximum"] == 5.0
    assert actual["variance"] == 0.0
    assert actual["standard_deviation"] == 0.0
    assert actual["p25"] == 5.0
    assert actual["p75"] == 5.0