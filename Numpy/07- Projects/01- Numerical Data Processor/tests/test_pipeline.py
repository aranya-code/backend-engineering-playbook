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
import json
from pathlib import Path

import numpy as np
import pytest

from src.pipeline import process_values, run_pipeline


def test_process_values_validates_and_processes_in_memory() -> None:
    values = np.array(
        [10.0, 20.0, 30.0],
        dtype=np.float64,
    )

    normalized, statistics = process_values(values)

    np.testing.assert_allclose(
        normalized,
        np.array([0.0, 0.5, 1.0]),
    )

    assert statistics["count"] == 3.0
    assert statistics["sum"] == 60.0
    assert statistics["mean"] == 20.0
    assert statistics["minimum"] == 10.0
    assert statistics["maximum"] == 30.0


def test_process_values_rejects_invalid_input() -> None:
    values = np.array(
        [10.0, np.nan, 30.0],
        dtype=np.float64,
    )

    with pytest.raises(
        ValueError,
        match="NaN or infinite",
    ):
        process_values(values)


def test_process_values_rejects_empty_input() -> None:
    values = np.array([], dtype=np.float64)

    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        process_values(values)


def test_run_pipeline_processes_and_exports_outputs(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.npy"
    output_array_path = tmp_path / "processed.npy"
    output_statistics_path = tmp_path / "statistics.json"

    values = np.array(
        [10.0, 20.0, 30.0],
        dtype=np.float64,
    )

    np.save(input_path, values)

    array_path, statistics_path = run_pipeline(
        input_path,
        output_array_path=output_array_path,
        output_statistics_path=output_statistics_path,
    )

    assert array_path == output_array_path
    assert statistics_path == output_statistics_path
    assert output_array_path.is_file()
    assert output_statistics_path.is_file()

    processed = np.load(
        output_array_path,
        allow_pickle=False,
    )

    np.testing.assert_allclose(
        processed,
        np.array([0.0, 0.5, 1.0]),
    )

    statistics = json.loads(
        output_statistics_path.read_text(
            encoding="utf-8",
        )
    )

    assert statistics["count"] == 3.0
    assert statistics["sum"] == 60.0
    assert statistics["mean"] == 20.0
    assert statistics["minimum"] == 10.0
    assert statistics["maximum"] == 30.0


def test_run_pipeline_uses_default_output_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_path = tmp_path / "input.npy"
    output_dir = tmp_path / "output"

    values = np.array(
        [10.0, 20.0, 30.0],
        dtype=np.float64,
    )

    np.save(input_path, values)

    monkeypatch.setattr(
        "src.pipeline.OUTPUT_DIR",
        output_dir,
    )
    monkeypatch.setattr(
        "src.pipeline.DEFAULT_OUTPUT_FILENAME",
        "normalized.npy",
    )

    array_path, statistics_path = run_pipeline(
        input_path,
    )

    assert array_path == output_dir / "normalized.npy"
    assert statistics_path == output_dir / "statistics.json"
    assert array_path.is_file()
    assert statistics_path.is_file()


def test_run_pipeline_rejects_invalid_source(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "invalid.npy"

    np.save(
        input_path,
        np.array(
            [10.0, np.nan, 30.0],
            dtype=np.float64,
        ),
    )

    with pytest.raises(
        ValueError,
        match="NaN or infinite",
    ):
        run_pipeline(input_path)


def test_run_pipeline_preserves_input_file(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.npy"
    original = np.array(
        [10.0, 20.0, 30.0],
        dtype=np.float64,
    )

    np.save(input_path, original)

    run_pipeline(input_path)

    loaded = np.load(
        input_path,
        allow_pickle=False,
    )

    np.testing.assert_array_equal(
        loaded,
        original,
    )


def test_run_pipeline_rejects_missing_input(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "missing.npy"

    with pytest.raises(FileNotFoundError):
        run_pipeline(input_path)

import json
from pathlib import Path

import numpy as np
import pytest

from src.pipeline import process_values, run_pipeline


def test_process_values_validates_and_processes_in_memory() -> None:
    values = np.array(
        [10.0, 20.0, 30.0],
        dtype=np.float64,
    )

    normalized, statistics = process_values(values)

    np.testing.assert_allclose(
        normalized,
        np.array([0.0, 0.5, 1.0]),
    )

    assert statistics["count"] == 3.0
    assert statistics["sum"] == 60.0
    assert statistics["mean"] == 20.0
    assert statistics["minimum"] == 10.0
    assert statistics["maximum"] == 30.0


def test_process_values_rejects_invalid_input() -> None:
    values = np.array(
        [10.0, np.nan, 30.0],
        dtype=np.float64,
    )

    with pytest.raises(
        ValueError,
        match="NaN or infinite",
    ):
        process_values(values)


def test_process_values_rejects_empty_input() -> None:
    values = np.array([], dtype=np.float64)

    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        process_values(values)


def test_run_pipeline_processes_and_exports_outputs(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.npy"
    output_array_path = tmp_path / "processed.npy"
    output_statistics_path = tmp_path / "statistics.json"

    values = np.array(
        [10.0, 20.0, 30.0],
        dtype=np.float64,
    )

    np.save(input_path, values)

    array_path, statistics_path = run_pipeline(
        input_path,
        output_array_path=output_array_path,
        output_statistics_path=output_statistics_path,
    )

    assert array_path == output_array_path
    assert statistics_path == output_statistics_path
    assert output_array_path.is_file()
    assert output_statistics_path.is_file()

    processed = np.load(
        output_array_path,
        allow_pickle=False,
    )

    np.testing.assert_allclose(
        processed,
        np.array([0.0, 0.5, 1.0]),
    )

    statistics = json.loads(
        output_statistics_path.read_text(
            encoding="utf-8",
        )
    )

    assert statistics["count"] == 3.0
    assert statistics["sum"] == 60.0
    assert statistics["mean"] == 20.0
    assert statistics["minimum"] == 10.0
    assert statistics["maximum"] == 30.0


def test_run_pipeline_uses_default_output_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_path = tmp_path / "input.npy"
    output_dir = tmp_path / "output"

    values = np.array(
        [10.0, 20.0, 30.0],
        dtype=np.float64,
    )

    np.save(input_path, values)

    monkeypatch.setattr(
        "src.pipeline.OUTPUT_DIR",
        output_dir,
    )
    monkeypatch.setattr(
        "src.pipeline.DEFAULT_OUTPUT_FILENAME",
        "normalized.npy",
    )

    array_path, statistics_path = run_pipeline(
        input_path,
    )

    assert array_path == output_dir / "normalized.npy"
    assert statistics_path == output_dir / "statistics.json"
    assert array_path.is_file()
    assert statistics_path.is_file()


def test_run_pipeline_rejects_invalid_source(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "invalid.npy"

    np.save(
        input_path,
        np.array(
            [10.0, np.nan, 30.0],
            dtype=np.float64,
        ),
    )

    with pytest.raises(
        ValueError,
        match="NaN or infinite",
    ):
        run_pipeline(input_path)


def test_run_pipeline_preserves_input_file(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.npy"
    original = np.array(
        [10.0, 20.0, 30.0],
        dtype=np.float64,
    )

    np.save(input_path, original)

    run_pipeline(input_path)

    loaded = np.load(
        input_path,
        allow_pickle=False,
    )

    np.testing.assert_array_equal(
        loaded,
        original,
    )


def test_run_pipeline_rejects_missing_input(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "missing.npy"

    with pytest.raises(FileNotFoundError):
        run_pipeline(input_path)
from pathlib import Path

import numpy as np
import pytest

from src.pipeline import process_values, run_pipeline


def test_process_values_returns_normalized_data_and_statistics() -> None:
    values = np.array(
        [10.0, 20.0, 30.0],
        dtype=np.float64,
    )

    normalized, statistics = process_values(values)

    np.testing.assert_allclose(
        normalized,
        np.array([0.0, 0.5, 1.0]),
    )
    assert statistics["count"] == 3.0
    assert statistics["sum"] == pytest.approx(60.0)
    assert statistics["mean"] == pytest.approx(20.0)
    assert statistics["median"] == pytest.approx(20.0)
    assert statistics["minimum"] == pytest.approx(10.0)
    assert statistics["maximum"] == pytest.approx(30.0)


def test_process_values_accepts_integer_input() -> None:
    values = np.array(
        [10, 20, 30],
        dtype=np.int32,
    )

    normalized, statistics = process_values(values)

    np.testing.assert_allclose(
        normalized,
        np.array([0.0, 0.5, 1.0]),
    )
    assert statistics["mean"] == pytest.approx(20.0)


def test_process_values_rejects_non_finite_values() -> None:
    values = np.array(
        [10.0, np.nan, 30.0],
        dtype=np.float64,
    )

    with pytest.raises(
        ValueError,
        match="NaN or infinite",
    ):
        process_values(values)


def test_process_values_rejects_empty_input() -> None:
    values = np.array([], dtype=np.float64)

    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        process_values(values)


def test_run_pipeline_creates_array_and_statistics_outputs(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.npy"
    output_array_path = tmp_path / "processed.npy"
    output_statistics_path = tmp_path / "statistics.json"

    values = np.array(
        [10.0, 20.0, 30.0],
        dtype=np.float64,
    )
    np.save(input_path, values)

    array_path, statistics_path = run_pipeline(
        input_path,
        output_array_path=output_array_path,
        output_statistics_path=output_statistics_path,
    )

    assert array_path == output_array_path
    assert statistics_path == output_statistics_path
    assert output_array_path.is_file()
    assert output_statistics_path.is_file()


def test_run_pipeline_exports_normalized_array(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.npy"
    output_array_path = tmp_path / "processed.npy"
    output_statistics_path = tmp_path / "statistics.json"

    np.save(
        input_path,
        np.array(
            [10.0, 20.0, 30.0],
            dtype=np.float64,
        ),
    )

    run_pipeline(
        input_path,
        output_array_path=output_array_path,
        output_statistics_path=output_statistics_path,
    )

    actual = np.load(
        output_array_path,
        allow_pickle=False,
    )

    np.testing.assert_allclose(
        actual,
        np.array([0.0, 0.5, 1.0]),
    )


def test_run_pipeline_creates_statistics_file(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.npy"
    output_array_path = tmp_path / "processed.npy"
    output_statistics_path = tmp_path / "statistics.json"

    np.save(
        input_path,
        np.array(
            [10.0, 20.0, 30.0],
            dtype=np.float64,
        ),
    )

    run_pipeline(
        input_path,
        output_array_path=output_array_path,
        output_statistics_path=output_statistics_path,
    )

    content = output_statistics_path.read_text(
        encoding="utf-8",
    )

    assert '"count": 3.0' in content
    assert '"maximum": 30.0' in content
    assert '"mean": 20.0' in content
    assert '"minimum": 10.0' in content
    assert '"sum": 60.0' in content


def test_run_pipeline_creates_missing_output_directories(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.npy"
    output_array_path = (
        tmp_path / "nested" / "arrays" / "processed.npy"
    )
    output_statistics_path = (
        tmp_path / "nested" / "reports" / "statistics.json"
    )

    np.save(
        input_path,
        np.array(
            [10.0, 20.0, 30.0],
            dtype=np.float64,
        ),
    )

    run_pipeline(
        input_path,
        output_array_path=output_array_path,
        output_statistics_path=output_statistics_path,
    )

    assert output_array_path.is_file()
    assert output_statistics_path.is_file()


def test_run_pipeline_preserves_input_data(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.npy"
    output_array_path = tmp_path / "processed.npy"
    output_statistics_path = tmp_path / "statistics.json"

    original = np.array(
        [10.0, 20.0, 30.0],
        dtype=np.float64,
    )
    np.save(input_path, original)

    run_pipeline(
        input_path,
        output_array_path=output_array_path,
        output_statistics_path=output_statistics_path,
    )

    actual = np.load(
        input_path,
        allow_pickle=False,
    )

    np.testing.assert_array_equal(
        actual,
        original,
    )


def test_run_pipeline_rejects_missing_input_file(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "missing.npy"

    with pytest.raises(FileNotFoundError):
        run_pipeline(input_path)


def test_run_pipeline_rejects_invalid_input_data(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.npy"

    np.save(
        input_path,
        np.array(
            [10.0, np.inf, 30.0],
            dtype=np.float64,
        ),
    )

    with pytest.raises(
        ValueError,
        match="NaN or infinite",
    ):
        run_pipeline(input_path)


def test_run_pipeline_rejects_unsupported_input_format(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.csv"
    input_path.write_text(
        "10,20,30\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported input format",
    ):
        run_pipeline(input_path)


def test_process_values_does_not_mutate_input() -> None:
    values = np.array(
        [10.0, 20.0, 30.0],
        dtype=np.float64,
    )
    original = values.copy()

    process_values(values)

    np.testing.assert_array_equal(
        values,
        original,
    )

from pathlib import Path

import numpy as np
import pytest

from src.pipeline import process_values, run_pipeline


def test_process_values_returns_normalized_data_and_statistics() -> None:
    values = np.array(
        [10.0, 20.0, 30.0],
        dtype=np.float64,
    )

    normalized, statistics = process_values(values)

    np.testing.assert_allclose(
        normalized,
        np.array([0.0, 0.5, 1.0]),
    )
    assert statistics["count"] == 3.0
    assert statistics["sum"] == pytest.approx(60.0)
    assert statistics["mean"] == pytest.approx(20.0)
    assert statistics["median"] == pytest.approx(20.0)
    assert statistics["minimum"] == pytest.approx(10.0)
    assert statistics["maximum"] == pytest.approx(30.0)


def test_process_values_accepts_integer_input() -> None:
    values = np.array(
        [10, 20, 30],
        dtype=np.int32,
    )

    normalized, statistics = process_values(values)

    np.testing.assert_allclose(
        normalized,
        np.array([0.0, 0.5, 1.0]),
    )
    assert statistics["mean"] == pytest.approx(20.0)


def test_process_values_rejects_non_finite_values() -> None:
    values = np.array(
        [10.0, np.nan, 30.0],
        dtype=np.float64,
    )

    with pytest.raises(
        ValueError,
        match="NaN or infinite",
    ):
        process_values(values)


def test_process_values_rejects_empty_input() -> None:
    values = np.array([], dtype=np.float64)

    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        process_values(values)


def test_run_pipeline_creates_array_and_statistics_outputs(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.npy"
    output_array_path = tmp_path / "processed.npy"
    output_statistics_path = tmp_path / "statistics.json"

    values = np.array(
        [10.0, 20.0, 30.0],
        dtype=np.float64,
    )
    np.save(input_path, values)

    array_path, statistics_path = run_pipeline(
        input_path,
        output_array_path=output_array_path,
        output_statistics_path=output_statistics_path,
    )

    assert array_path == output_array_path
    assert statistics_path == output_statistics_path
    assert output_array_path.is_file()
    assert output_statistics_path.is_file()


def test_run_pipeline_exports_normalized_array(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.npy"
    output_array_path = tmp_path / "processed.npy"
    output_statistics_path = tmp_path / "statistics.json"

    np.save(
        input_path,
        np.array(
            [10.0, 20.0, 30.0],
            dtype=np.float64,
        ),
    )

    run_pipeline(
        input_path,
        output_array_path=output_array_path,
        output_statistics_path=output_statistics_path,
    )

    actual = np.load(
        output_array_path,
        allow_pickle=False,
    )

    np.testing.assert_allclose(
        actual,
        np.array([0.0, 0.5, 1.0]),
    )


def test_run_pipeline_creates_statistics_file(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.npy"
    output_array_path = tmp_path / "processed.npy"
    output_statistics_path = tmp_path / "statistics.json"

    np.save(
        input_path,
        np.array(
            [10.0, 20.0, 30.0],
            dtype=np.float64,
        ),
    )

    run_pipeline(
        input_path,
        output_array_path=output_array_path,
        output_statistics_path=output_statistics_path,
    )

    content = output_statistics_path.read_text(
        encoding="utf-8",
    )

    assert '"count": 3.0' in content
    assert '"maximum": 30.0' in content
    assert '"mean": 20.0' in content
    assert '"minimum": 10.0' in content
    assert '"sum": 60.0' in content


def test_run_pipeline_creates_missing_output_directories(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.npy"
    output_array_path = (
        tmp_path / "nested" / "arrays" / "processed.npy"
    )
    output_statistics_path = (
        tmp_path / "nested" / "reports" / "statistics.json"
    )

    np.save(
        input_path,
        np.array(
            [10.0, 20.0, 30.0],
            dtype=np.float64,
        ),
    )

    run_pipeline(
        input_path,
        output_array_path=output_array_path,
        output_statistics_path=output_statistics_path,
    )

    assert output_array_path.is_file()
    assert output_statistics_path.is_file()


def test_run_pipeline_preserves_input_data(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.npy"
    output_array_path = tmp_path / "processed.npy"
    output_statistics_path = tmp_path / "statistics.json"

    original = np.array(
        [10.0, 20.0, 30.0],
        dtype=np.float64,
    )
    np.save(input_path, original)

    run_pipeline(
        input_path,
        output_array_path=output_array_path,
        output_statistics_path=output_statistics_path,
    )

    actual = np.load(
        input_path,
        allow_pickle=False,
    )

    np.testing.assert_array_equal(
        actual,
        original,
    )


def test_run_pipeline_rejects_missing_input_file(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "missing.npy"

    with pytest.raises(FileNotFoundError):
        run_pipeline(input_path)


def test_run_pipeline_rejects_invalid_input_data(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.npy"

    np.save(
        input_path,
        np.array(
            [10.0, np.inf, 30.0],
            dtype=np.float64,
        ),
    )

    with pytest.raises(
        ValueError,
        match="NaN or infinite",
    ):
        run_pipeline(input_path)


def test_run_pipeline_rejects_unsupported_input_format(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.csv"
    input_path.write_text(
        "10,20,30\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported input format",
    ):
        run_pipeline(input_path)


def test_process_values_does_not_mutate_input() -> None:
    values = np.array(
        [10.0, 20.0, 30.0],
        dtype=np.float64,
    )
    original = values.copy()

    process_values(values)

    np.testing.assert_array_equal(
        values,
        original,
    )