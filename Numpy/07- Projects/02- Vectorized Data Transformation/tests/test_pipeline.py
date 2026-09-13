"""Tests for the vectorized numerical transformation pipeline."""

from __future__ import annotations

import numpy as np
import pytest

from src.pipeline import (
    PipelineConfig,
    PipelineResult,
    run_pipeline,
    transform_batch,
    validate_input,
)


def test_pipeline_config_accepts_valid_configuration() -> None:
    config = PipelineConfig(
        factor=2.0,
        offset=1.0,
        minimum=0.0,
        maximum=100.0,
        max_elements=1_000,
        batch_size=100,
    )

    config.validate()


@pytest.mark.parametrize(
    "config, error_message",
    [
        (
            PipelineConfig(factor=np.nan),
            "factor must be finite",
        ),
        (
            PipelineConfig(offset=np.inf),
            "offset must be finite",
        ),
        (
            PipelineConfig(minimum=np.nan),
            "minimum must be finite",
        ),
        (
            PipelineConfig(maximum=np.inf),
            "maximum must be finite",
        ),
        (
            PipelineConfig(minimum=10.0, maximum=0.0),
            "minimum must not exceed maximum",
        ),
        (
            PipelineConfig(max_elements=0),
            "max_elements must be positive",
        ),
        (
            PipelineConfig(batch_size=0),
            "batch_size must be positive",
        ),
    ],
)
def test_pipeline_config_rejects_invalid_configuration(
    config: PipelineConfig,
    error_message: str,
) -> None:
    with pytest.raises(ValueError, match=error_message):
        config.validate()


def test_validate_input_converts_numeric_values_to_float64() -> None:
    values = np.array([1, 2, 3], dtype=np.int32)

    result = validate_input(
        values,
        max_elements=10,
    )

    assert result.dtype == np.dtype(np.float64)
    np.testing.assert_allclose(
        result,
        np.array([1.0, 2.0, 3.0]),
    )


def test_validate_input_rejects_scalar_input() -> None:
    values = np.array(10.0)

    with pytest.raises(
        ValueError,
        match="Expected an array with at least one dimension",
    ):
        validate_input(
            values,
            max_elements=10,
        )


def test_validate_input_rejects_oversized_input() -> None:
    values = np.arange(10, dtype=np.float64)

    with pytest.raises(
        ValueError,
        match="maximum allowed is 5",
    ):
        validate_input(
            values,
            max_elements=5,
        )


@pytest.mark.parametrize(
    "values",
    [
        np.array([1.0, np.nan]),
        np.array([1.0, np.inf]),
        np.array([-np.inf, 2.0]),
    ],
)
def test_validate_input_rejects_non_finite_values(
    values: np.ndarray,
) -> None:
    with pytest.raises(
        ValueError,
        match="Input contains NaN or infinite values",
    ):
        validate_input(
            values,
            max_elements=10,
        )


def test_validate_input_accepts_multidimensional_numeric_data() -> None:
    values = np.array(
        [
            [1.0, 2.0],
            [3.0, 4.0],
        ]
    )

    result = validate_input(
        values,
        max_elements=10,
    )

    np.testing.assert_allclose(
        result,
        values,
    )
    assert result.shape == (2, 2)


def test_transform_batch_applies_transformation_and_range_filter() -> None:
    values = np.array(
        [-10.0, 1.0, 5.0, 20.0]
    )
    config = PipelineConfig(
        factor=2.0,
        offset=0.0,
        minimum=0.0,
        maximum=10.0,
        normalize_output=False,
        batch_size=10,
    )

    result = transform_batch(
        values,
        config=config,
    )

    np.testing.assert_allclose(
        result,
        np.array([0.0, 2.0, 10.0]),
    )


def test_transform_batch_supports_normalized_output() -> None:
    values = np.array(
        [0.0, 5.0, 10.0]
    )
    config = PipelineConfig(
        factor=1.0,
        offset=0.0,
        minimum=0.0,
        maximum=10.0,
        normalize_output=True,
        batch_size=10,
    )

    result = transform_batch(
        values,
        config=config,
    )

    np.testing.assert_allclose(
        result,
        np.array([0.0, 0.5, 1.0]),
    )


def test_run_pipeline_processes_input_in_batches(
    tmp_path,
) -> None:
    input_path = tmp_path / "input.npy"
    output_path = tmp_path / "output.npy"

    source = np.array(
        [-5.0, 1.0, 2.0, 3.0, 20.0],
    )
    np.save(
        input_path,
        source,
        allow_pickle=False,
    )

    config = PipelineConfig(
        factor=2.0,
        offset=1.0,
        minimum=0.0,
        maximum=10.0,
        normalize_output=False,
        max_elements=100,
        batch_size=2,
    )

    result = run_pipeline(
        input_path,
        output_path,
        config=config,
    )

    assert isinstance(result, PipelineResult)
    assert result.output_path == output_path
    assert result.input_elements == 5
    assert result.output_elements == 4

    saved = np.load(
        output_path,
        allow_pickle=False,
    )

    np.testing.assert_allclose(
        saved,
        np.array([3.0, 5.0, 7.0, 10.0]),
    )


def test_run_pipeline_flattens_multidimensional_input(
    tmp_path,
) -> None:
    input_path = tmp_path / "input.npy"
    output_path = tmp_path / "output.npy"

    source = np.array(
        [
            [1.0, 2.0],
            [3.0, 4.0],
        ]
    )
    np.save(
        input_path,
        source,
        allow_pickle=False,
    )

    config = PipelineConfig(
        factor=1.0,
        offset=0.0,
        minimum=0.0,
        maximum=10.0,
        batch_size=2,
    )

    result = run_pipeline(
        input_path,
        output_path,
        config=config,
    )

    assert result.input_elements == 4
    assert result.output_elements == 4

    saved = np.load(
        output_path,
        allow_pickle=False,
    )

    np.testing.assert_allclose(
        saved,
        np.array([1.0, 2.0, 3.0, 4.0]),
    )


def test_run_pipeline_returns_operational_statistics(
    tmp_path,
) -> None:
    input_path = tmp_path / "input.npy"
    output_path = tmp_path / "output.npy"

    source = np.array(
        [1.0, 2.0, 3.0],
    )
    np.save(
        input_path,
        source,
        allow_pickle=False,
    )

    result = run_pipeline(
        input_path,
        output_path,
        config=PipelineConfig(
            minimum=0.0,
            maximum=10.0,
            batch_size=2,
        ),
    )

    assert result.statistics["count"] == 3
    assert result.statistics["sum"] == pytest.approx(6.0)
    assert result.statistics["mean"] == pytest.approx(2.0)
    assert result.statistics["minimum"] == pytest.approx(1.0)
    assert result.statistics["maximum"] == pytest.approx(3.0)
    assert result.statistics["median"] == pytest.approx(2.0)


def test_run_pipeline_handles_empty_input(
    tmp_path,
) -> None:
    input_path = tmp_path / "input.npy"
    output_path = tmp_path / "output.npy"

    source = np.array([], dtype=np.float64)
    np.save(
        input_path,
        source,
        allow_pickle=False,
    )

    result = run_pipeline(
        input_path,
        output_path,
    )

    assert result.input_elements == 0
    assert result.output_elements == 0
    assert result.input_nbytes == 0
    assert result.output_nbytes == 0
    assert result.statistics["count"] == 0

    saved = np.load(
        output_path,
        allow_pickle=False,
    )

    assert saved.dtype == np.dtype(np.float64)
    assert saved.size == 0


def test_run_pipeline_creates_missing_output_directories(
    tmp_path,
) -> None:
    input_path = tmp_path / "input.npy"
    output_path = tmp_path / "nested" / "results" / "output.npy"

    source = np.array([1.0, 2.0])
    np.save(
        input_path,
        source,
        allow_pickle=False,
    )

    run_pipeline(
        input_path,
        output_path,
    )

    assert output_path.is_file()


def test_run_pipeline_respects_max_elements(
    tmp_path,
) -> None:
    input_path = tmp_path / "input.npy"
    output_path = tmp_path / "output.npy"

    source = np.arange(10, dtype=np.float64)
    np.save(
        input_path,
        source,
        allow_pickle=False,
    )

    config = PipelineConfig(
        max_elements=5,
    )

    with pytest.raises(
        ValueError,
        match="maximum allowed is 5",
    ):
        run_pipeline(
            input_path,
            output_path,
            config=config,
        )


def test_run_pipeline_requires_existing_input_file(
    tmp_path,
) -> None:
    input_path = tmp_path / "missing.npy"
    output_path = tmp_path / "output.npy"

    with pytest.raises(
        FileNotFoundError,
        match="Input file does not exist",
    ):
        run_pipeline(
            input_path,
            output_path,
        )

"""Tests for the vectorized numerical transformation pipeline."""

from __future__ import annotations

import numpy as np
import pytest

from src.pipeline import (
    PipelineConfig,
    PipelineResult,
    run_pipeline,
    transform_batch,
    validate_input,
)


def test_pipeline_config_accepts_valid_configuration() -> None:
    config = PipelineConfig(
        factor=2.0,
        offset=1.0,
        minimum=0.0,
        maximum=100.0,
        max_elements=1_000,
        batch_size=100,
    )

    config.validate()


@pytest.mark.parametrize(
    "config, error_message",
    [
        (
            PipelineConfig(factor=np.nan),
            "factor must be finite",
        ),
        (
            PipelineConfig(offset=np.inf),
            "offset must be finite",
        ),
        (
            PipelineConfig(minimum=np.nan),
            "minimum must be finite",
        ),
        (
            PipelineConfig(maximum=np.inf),
            "maximum must be finite",
        ),
        (
            PipelineConfig(minimum=10.0, maximum=0.0),
            "minimum must not exceed maximum",
        ),
        (
            PipelineConfig(max_elements=0),
            "max_elements must be positive",
        ),
        (
            PipelineConfig(batch_size=0),
            "batch_size must be positive",
        ),
    ],
)
def test_pipeline_config_rejects_invalid_configuration(
    config: PipelineConfig,
    error_message: str,
) -> None:
    with pytest.raises(ValueError, match=error_message):
        config.validate()


def test_validate_input_converts_numeric_values_to_float64() -> None:
    values = np.array([1, 2, 3], dtype=np.int32)

    result = validate_input(
        values,
        max_elements=10,
    )

    assert result.dtype == np.dtype(np.float64)
    np.testing.assert_allclose(
        result,
        np.array([1.0, 2.0, 3.0]),
    )


def test_validate_input_rejects_scalar_input() -> None:
    values = np.array(10.0)

    with pytest.raises(
        ValueError,
        match="Expected an array with at least one dimension",
    ):
        validate_input(
            values,
            max_elements=10,
        )


def test_validate_input_rejects_oversized_input() -> None:
    values = np.arange(10, dtype=np.float64)

    with pytest.raises(
        ValueError,
        match="maximum allowed is 5",
    ):
        validate_input(
            values,
            max_elements=5,
        )


@pytest.mark.parametrize(
    "values",
    [
        np.array([1.0, np.nan]),
        np.array([1.0, np.inf]),
        np.array([-np.inf, 2.0]),
    ],
)
def test_validate_input_rejects_non_finite_values(
    values: np.ndarray,
) -> None:
    with pytest.raises(
        ValueError,
        match="Input contains NaN or infinite values",
    ):
        validate_input(
            values,
            max_elements=10,
        )


def test_validate_input_accepts_multidimensional_numeric_data() -> None:
    values = np.array(
        [
            [1.0, 2.0],
            [3.0, 4.0],
        ]
    )

    result = validate_input(
        values,
        max_elements=10,
    )

    np.testing.assert_allclose(
        result,
        values,
    )
    assert result.shape == (2, 2)


def test_transform_batch_applies_transformation_and_range_filter() -> None:
    values = np.array(
        [-10.0, 1.0, 5.0, 20.0]
    )
    config = PipelineConfig(
        factor=2.0,
        offset=0.0,
        minimum=0.0,
        maximum=10.0,
        normalize_output=False,
        batch_size=10,
    )

    result = transform_batch(
        values,
        config=config,
    )

    np.testing.assert_allclose(
        result,
        np.array([0.0, 2.0, 10.0]),
    )


def test_transform_batch_supports_normalized_output() -> None:
    values = np.array(
        [0.0, 5.0, 10.0]
    )
    config = PipelineConfig(
        factor=1.0,
        offset=0.0,
        minimum=0.0,
        maximum=10.0,
        normalize_output=True,
        batch_size=10,
    )

    result = transform_batch(
        values,
        config=config,
    )

    np.testing.assert_allclose(
        result,
        np.array([0.0, 0.5, 1.0]),
    )


def test_run_pipeline_processes_input_in_batches(
    tmp_path,
) -> None:
    input_path = tmp_path / "input.npy"
    output_path = tmp_path / "output.npy"

    source = np.array(
        [-5.0, 1.0, 2.0, 3.0, 20.0],
    )
    np.save(
        input_path,
        source,
        allow_pickle=False,
    )

    config = PipelineConfig(
        factor=2.0,
        offset=1.0,
        minimum=0.0,
        maximum=10.0,
        normalize_output=False,
        max_elements=100,
        batch_size=2,
    )

    result = run_pipeline(
        input_path,
        output_path,
        config=config,
    )

    assert isinstance(result, PipelineResult)
    assert result.output_path == output_path
    assert result.input_elements == 5
    assert result.output_elements == 4

    saved = np.load(
        output_path,
        allow_pickle=False,
    )

    np.testing.assert_allclose(
        saved,
        np.array([3.0, 5.0, 7.0, 10.0]),
    )


def test_run_pipeline_flattens_multidimensional_input(
    tmp_path,
) -> None:
    input_path = tmp_path / "input.npy"
    output_path = tmp_path / "output.npy"

    source = np.array(
        [
            [1.0, 2.0],
            [3.0, 4.0],
        ]
    )
    np.save(
        input_path,
        source,
        allow_pickle=False,
    )

    config = PipelineConfig(
        factor=1.0,
        offset=0.0,
        minimum=0.0,
        maximum=10.0,
        batch_size=2,
    )

    result = run_pipeline(
        input_path,
        output_path,
        config=config,
    )

    assert result.input_elements == 4
    assert result.output_elements == 4

    saved = np.load(
        output_path,
        allow_pickle=False,
    )

    np.testing.assert_allclose(
        saved,
        np.array([1.0, 2.0, 3.0, 4.0]),
    )


def test_run_pipeline_returns_operational_statistics(
    tmp_path,
) -> None:
    input_path = tmp_path / "input.npy"
    output_path = tmp_path / "output.npy"

    source = np.array(
        [1.0, 2.0, 3.0],
    )
    np.save(
        input_path,
        source,
        allow_pickle=False,
    )

    result = run_pipeline(
        input_path,
        output_path,
        config=PipelineConfig(
            minimum=0.0,
            maximum=10.0,
            batch_size=2,
        ),
    )

    assert result.statistics["count"] == 3
    assert result.statistics["sum"] == pytest.approx(6.0)
    assert result.statistics["mean"] == pytest.approx(2.0)
    assert result.statistics["minimum"] == pytest.approx(1.0)
    assert result.statistics["maximum"] == pytest.approx(3.0)
    assert result.statistics["median"] == pytest.approx(2.0)


def test_run_pipeline_handles_empty_input(
    tmp_path,
) -> None:
    input_path = tmp_path / "input.npy"
    output_path = tmp_path / "output.npy"

    source = np.array([], dtype=np.float64)
    np.save(
        input_path,
        source,
        allow_pickle=False,
    )

    result = run_pipeline(
        input_path,
        output_path,
    )

    assert result.input_elements == 0
    assert result.output_elements == 0
    assert result.input_nbytes == 0
    assert result.output_nbytes == 0
    assert result.statistics["count"] == 0

    saved = np.load(
        output_path,
        allow_pickle=False,
    )

    assert saved.dtype == np.dtype(np.float64)
    assert saved.size == 0


def test_run_pipeline_creates_missing_output_directories(
    tmp_path,
) -> None:
    input_path = tmp_path / "input.npy"
    output_path = tmp_path / "nested" / "results" / "output.npy"

    source = np.array([1.0, 2.0])
    np.save(
        input_path,
        source,
        allow_pickle=False,
    )

    run_pipeline(
        input_path,
        output_path,
    )

    assert output_path.is_file()


def test_run_pipeline_respects_max_elements(
    tmp_path,
) -> None:
    input_path = tmp_path / "input.npy"
    output_path = tmp_path / "output.npy"

    source = np.arange(10, dtype=np.float64)
    np.save(
        input_path,
        source,
        allow_pickle=False,
    )

    config = PipelineConfig(
        max_elements=5,
    )

    with pytest.raises(
        ValueError,
        match="maximum allowed is 5",
    ):
        run_pipeline(
            input_path,
            output_path,
            config=config,
        )


def test_run_pipeline_requires_existing_input_file(
    tmp_path,
) -> None:
    input_path = tmp_path / "missing.npy"
    output_path = tmp_path / "output.npy"

    with pytest.raises(
        FileNotFoundError,
        match="Input file does not exist",
    ):
        run_pipeline(
            input_path,
            output_path,
        )