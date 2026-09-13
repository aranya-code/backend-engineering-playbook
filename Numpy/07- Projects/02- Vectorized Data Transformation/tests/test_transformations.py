"""Tests for vectorized numerical transformation utilities."""

from __future__ import annotations

import numpy as np
import pytest

from src.transformations import (
    clip,
    normalize,
    offset,
    scale,
    scale_and_offset,
    threshold,
)


def test_scale_applies_factor_vectorized() -> None:
    values = np.array([1.0, 2.0, 3.0])

    result = scale(values, factor=2.5)

    np.testing.assert_allclose(
        result,
        np.array([2.5, 5.0, 7.5]),
    )


def test_scale_rejects_non_finite_factor() -> None:
    values = np.array([1.0, 2.0])

    with pytest.raises(ValueError, match="factor must be finite"):
        scale(values, factor=np.inf)


def test_offset_applies_amount_vectorized() -> None:
    values = np.array([10.0, 20.0, 30.0])

    result = offset(values, amount=-5.0)

    np.testing.assert_allclose(
        result,
        np.array([5.0, 15.0, 25.0]),
    )


def test_offset_rejects_non_finite_amount() -> None:
    values = np.array([1.0, 2.0])

    with pytest.raises(ValueError, match="amount must be finite"):
        offset(values, amount=np.nan)


def test_scale_and_offset_composes_operations() -> None:
    values = np.array([1.0, 2.0, 3.0])

    result = scale_and_offset(
        values,
        factor=3.0,
        amount=2.0,
    )

    np.testing.assert_allclose(
        result,
        np.array([5.0, 8.0, 11.0]),
    )


def test_clip_restricts_values_to_range() -> None:
    values = np.array([-10.0, 5.0, 100.0])

    result = clip(
        values,
        minimum=0.0,
        maximum=10.0,
    )

    np.testing.assert_allclose(
        result,
        np.array([0.0, 5.0, 10.0]),
    )


def test_clip_rejects_invalid_range() -> None:
    values = np.array([1.0, 2.0])

    with pytest.raises(ValueError, match="minimum must not exceed maximum"):
        clip(
            values,
            minimum=10.0,
            maximum=0.0,
        )


def test_normalize_maps_values_to_requested_range() -> None:
    values = np.array([10.0, 20.0, 30.0])

    result = normalize(
        values,
        minimum=-1.0,
        maximum=1.0,
    )

    np.testing.assert_allclose(
        result,
        np.array([-1.0, 0.0, 1.0]),
    )


def test_normalize_returns_constant_minimum_for_constant_input() -> None:
    values = np.array([7.0, 7.0, 7.0])

    result = normalize(
        values,
        minimum=2.0,
        maximum=5.0,
    )

    np.testing.assert_allclose(
        result,
        np.array([2.0, 2.0, 2.0]),
    )


def test_normalize_preserves_empty_input() -> None:
    values = np.array([], dtype=np.float64)

    result = normalize(values)

    np.testing.assert_array_equal(
        result,
        values,
    )


def test_normalize_rejects_invalid_output_range() -> None:
    values = np.array([1.0, 2.0])

    with pytest.raises(
        ValueError,
        match="normalization minimum must be less than maximum",
    ):
        normalize(
            values,
            minimum=1.0,
            maximum=1.0,
        )


def test_threshold_returns_inclusive_boolean_mask() -> None:
    values = np.array([-1.0, 0.0, 5.0, 10.0, 11.0])

    result = threshold(
        values,
        minimum=0.0,
        maximum=10.0,
    )

    np.testing.assert_array_equal(
        result,
        np.array([False, True, True, True, False]),
    )


def test_transform_applies_pipeline_in_order() -> None:
    values = np.array([-2.0, 1.0, 10.0])

    result = transform(
        values,
        factor=2.0,
        amount=1.0,
        minimum=0.0,
        maximum=10.0,
        normalize_output=False,
    )

    np.testing.assert_allclose(
        result,
        np.array([0.0, 3.0, 10.0]),
    )


def test_transform_can_normalize_output() -> None:
    values = np.array([0.0, 5.0, 10.0])

    result = transform(
        values,
        factor=1.0,
        amount=0.0,
        minimum=0.0,
        maximum=10.0,
        normalize_output=True,
    )

    np.testing.assert_allclose(
        result,
        np.array([0.0, 0.5, 1.0]),
    )

"""Tests for vectorized numerical transformation utilities."""

from __future__ import annotations

import numpy as np
import pytest

from src.transformations import (
    clip,
    normalize,
    offset,
    scale,
    scale_and_offset,
    threshold,
)


def test_scale_applies_factor_vectorized() -> None:
    values = np.array([1.0, 2.0, 3.0])

    result = scale(values, factor=2.5)

    np.testing.assert_allclose(
        result,
        np.array([2.5, 5.0, 7.5]),
    )


def test_scale_rejects_non_finite_factor() -> None:
    values = np.array([1.0, 2.0])

    with pytest.raises(ValueError, match="factor must be finite"):
        scale(values, factor=np.inf)


def test_offset_applies_amount_vectorized() -> None:
    values = np.array([10.0, 20.0, 30.0])

    result = offset(values, amount=-5.0)

    np.testing.assert_allclose(
        result,
        np.array([5.0, 15.0, 25.0]),
    )


def test_offset_rejects_non_finite_amount() -> None:
    values = np.array([1.0, 2.0])

    with pytest.raises(ValueError, match="amount must be finite"):
        offset(values, amount=np.nan)


def test_scale_and_offset_composes_operations() -> None:
    values = np.array([1.0, 2.0, 3.0])

    result = scale_and_offset(
        values,
        factor=3.0,
        amount=2.0,
    )

    np.testing.assert_allclose(
        result,
        np.array([5.0, 8.0, 11.0]),
    )


def test_clip_restricts_values_to_range() -> None:
    values = np.array([-10.0, 5.0, 100.0])

    result = clip(
        values,
        minimum=0.0,
        maximum=10.0,
    )

    np.testing.assert_allclose(
        result,
        np.array([0.0, 5.0, 10.0]),
    )


def test_clip_rejects_invalid_range() -> None:
    values = np.array([1.0, 2.0])

    with pytest.raises(ValueError, match="minimum must not exceed maximum"):
        clip(
            values,
            minimum=10.0,
            maximum=0.0,
        )


def test_normalize_maps_values_to_requested_range() -> None:
    values = np.array([10.0, 20.0, 30.0])

    result = normalize(
        values,
        minimum=-1.0,
        maximum=1.0,
    )

    np.testing.assert_allclose(
        result,
        np.array([-1.0, 0.0, 1.0]),
    )


def test_normalize_returns_constant_minimum_for_constant_input() -> None:
    values = np.array([7.0, 7.0, 7.0])

    result = normalize(
        values,
        minimum=2.0,
        maximum=5.0,
    )

    np.testing.assert_allclose(
        result,
        np.array([2.0, 2.0, 2.0]),
    )


def test_normalize_preserves_empty_input() -> None:
    values = np.array([], dtype=np.float64)

    result = normalize(values)

    np.testing.assert_array_equal(
        result,
        values,
    )


def test_normalize_rejects_invalid_output_range() -> None:
    values = np.array([1.0, 2.0])

    with pytest.raises(
        ValueError,
        match="normalization minimum must be less than maximum",
    ):
        normalize(
            values,
            minimum=1.0,
            maximum=1.0,
        )


def test_threshold_returns_inclusive_boolean_mask() -> None:
    values = np.array([-1.0, 0.0, 5.0, 10.0, 11.0])

    result = threshold(
        values,
        minimum=0.0,
        maximum=10.0,
    )

    np.testing.assert_array_equal(
        result,
        np.array([False, True, True, True, False]),
    )


def test_transform_applies_pipeline_in_order() -> None:
    values = np.array([-2.0, 1.0, 10.0])

    result = transform(
        values,
        factor=2.0,
        amount=1.0,
        minimum=0.0,
        maximum=10.0,
        normalize_output=False,
    )

    np.testing.assert_allclose(
        result,
        np.array([0.0, 3.0, 10.0]),
    )


def test_transform_can_normalize_output() -> None:
    values = np.array([0.0, 5.0, 10.0])

    result = transform(
        values,
        factor=1.0,
        amount=0.0,
        minimum=0.0,
        maximum=10.0,
        normalize_output=True,
    )

    np.testing.assert_allclose(
        result,
        np.array([0.0, 0.5, 1.0]),
    )