"""Tests for boolean masking and conditional selection utilities."""

from __future__ import annotations

import numpy as np
import pytest

from src.masking import (
    filter_finite,
    filter_range,
    finite_mask,
    positive_mask,
    range_mask,
    replace_where,
    select,
)


def test_finite_mask_selects_only_finite_values() -> None:
    values = np.array(
        [1.0, np.nan, 2.0, np.inf, -np.inf, 3.0]
    )

    result = finite_mask(values)

    np.testing.assert_array_equal(
        result,
        np.array(
            [True, False, True, False, False, True]
        ),
    )


def test_finite_mask_rejects_non_numeric_dtype() -> None:
    values = np.array(["1", "2", "3"])

    with pytest.raises(TypeError, match="Expected numeric dtype"):
        finite_mask(values)


def test_range_mask_selects_inclusive_range() -> None:
    values = np.array([-1.0, 0.0, 5.0, 10.0, 11.0])

    result = range_mask(
        values,
        minimum=0.0,
        maximum=10.0,
    )

    np.testing.assert_array_equal(
        result,
        np.array([False, True, True, True, False]),
    )


def test_range_mask_rejects_invalid_bounds() -> None:
    values = np.array([1.0, 2.0, 3.0])

    with pytest.raises(
        ValueError,
        match="minimum must not exceed maximum",
    ):
        range_mask(
            values,
            minimum=10.0,
            maximum=0.0,
        )


def test_positive_mask_selects_strictly_positive_values() -> None:
    values = np.array([-2.0, 0.0, 1.0, 3.5])

    result = positive_mask(values)

    np.testing.assert_array_equal(
        result,
        np.array([False, False, True, True]),
    )


def test_select_returns_values_matching_boolean_mask() -> None:
    values = np.array([10.0, 20.0, 30.0, 40.0])
    mask = np.array([True, False, True, False])

    result = select(values, mask)

    np.testing.assert_array_equal(
        result,
        np.array([10.0, 30.0]),
    )


def test_select_rejects_non_boolean_mask() -> None:
    values = np.array([10.0, 20.0])
    mask = np.array([1, 0])

    with pytest.raises(TypeError, match="Expected Boolean mask"):
        select(values, mask)


def test_select_rejects_mismatched_mask_shape() -> None:
    values = np.array([10.0, 20.0, 30.0])
    mask = np.array([True, False])

    with pytest.raises(
        ValueError,
        match="Mask shape .* does not match",
    ):
        select(values, mask)


def test_filter_finite_returns_only_finite_values() -> None:
    values = np.array(
        [1.0, np.nan, 2.5, np.inf, 4.0]
    )

    result = filter_finite(values)

    np.testing.assert_allclose(
        result,
        np.array([1.0, 2.5, 4.0]),
    )


def test_filter_range_returns_values_inside_bounds() -> None:
    values = np.array([-5.0, 0.0, 2.5, 10.0, 15.0])

    result = filter_range(
        values,
        minimum=0.0,
        maximum=10.0,
    )

    np.testing.assert_allclose(
        result,
        np.array([0.0, 2.5, 10.0]),
    )


def test_replace_where_replaces_selected_values() -> None:
    values = np.array([1.0, -2.0, 3.0, -4.0])
    predicate = values < 0.0

    result = replace_where(
        values,
        replacement=0.0,
        predicate=predicate,
    )

    np.testing.assert_allclose(
        result,
        np.array([1.0, 0.0, 3.0, 0.0]),
    )


def test_replace_where_does_not_mutate_input() -> None:
    values = np.array([1.0, -2.0, 3.0])
    predicate = values < 0.0

    replace_where(
        values,
        replacement=0.0,
        predicate=predicate,
    )

    np.testing.assert_allclose(
        values,
        np.array([1.0, -2.0, 3.0]),
    )


def test_replace_where_rejects_non_boolean_predicate() -> None:
    values = np.array([1.0, 2.0])
    predicate = np.array([1, 0])

    with pytest.raises(
        TypeError,
        match="Expected Boolean predicate",
    ):
        replace_where(
            values,
            replacement=0.0,
            predicate=predicate,
        )


def test_replace_where_rejects_mismatched_predicate_shape() -> None:
    values = np.array([1.0, 2.0, 3.0])
    predicate = np.array([True, False])

    with pytest.raises(
        ValueError,
        match="Predicate shape .* does not match",
    ):
        replace_where(
            values,
            replacement=0.0,
            predicate=predicate,
        )


def test_replace_where_rejects_non_finite_replacement() -> None:
    values = np.array([1.0, -2.0])
    predicate = values < 0.0

    with pytest.raises(
        ValueError,
        match="replacement must be finite",
    ):
        replace_where(
            values,
            replacement=np.nan,
            predicate=predicate,
        )

"""Tests for boolean masking and conditional selection utilities."""

from __future__ import annotations

import numpy as np
import pytest

from src.masking import (
    filter_finite,
    filter_range,
    finite_mask,
    positive_mask,
    range_mask,
    replace_where,
    select,
)


def test_finite_mask_selects_only_finite_values() -> None:
    values = np.array(
        [1.0, np.nan, 2.0, np.inf, -np.inf, 3.0]
    )

    result = finite_mask(values)

    np.testing.assert_array_equal(
        result,
        np.array(
            [True, False, True, False, False, True]
        ),
    )


def test_finite_mask_rejects_non_numeric_dtype() -> None:
    values = np.array(["1", "2", "3"])

    with pytest.raises(TypeError, match="Expected numeric dtype"):
        finite_mask(values)


def test_range_mask_selects_inclusive_range() -> None:
    values = np.array([-1.0, 0.0, 5.0, 10.0, 11.0])

    result = range_mask(
        values,
        minimum=0.0,
        maximum=10.0,
    )

    np.testing.assert_array_equal(
        result,
        np.array([False, True, True, True, False]),
    )


def test_range_mask_rejects_invalid_bounds() -> None:
    values = np.array([1.0, 2.0, 3.0])

    with pytest.raises(
        ValueError,
        match="minimum must not exceed maximum",
    ):
        range_mask(
            values,
            minimum=10.0,
            maximum=0.0,
        )


def test_positive_mask_selects_strictly_positive_values() -> None:
    values = np.array([-2.0, 0.0, 1.0, 3.5])

    result = positive_mask(values)

    np.testing.assert_array_equal(
        result,
        np.array([False, False, True, True]),
    )


def test_select_returns_values_matching_boolean_mask() -> None:
    values = np.array([10.0, 20.0, 30.0, 40.0])
    mask = np.array([True, False, True, False])

    result = select(values, mask)

    np.testing.assert_array_equal(
        result,
        np.array([10.0, 30.0]),
    )


def test_select_rejects_non_boolean_mask() -> None:
    values = np.array([10.0, 20.0])
    mask = np.array([1, 0])

    with pytest.raises(TypeError, match="Expected Boolean mask"):
        select(values, mask)


def test_select_rejects_mismatched_mask_shape() -> None:
    values = np.array([10.0, 20.0, 30.0])
    mask = np.array([True, False])

    with pytest.raises(
        ValueError,
        match="Mask shape .* does not match",
    ):
        select(values, mask)


def test_filter_finite_returns_only_finite_values() -> None:
    values = np.array(
        [1.0, np.nan, 2.5, np.inf, 4.0]
    )

    result = filter_finite(values)

    np.testing.assert_allclose(
        result,
        np.array([1.0, 2.5, 4.0]),
    )


def test_filter_range_returns_values_inside_bounds() -> None:
    values = np.array([-5.0, 0.0, 2.5, 10.0, 15.0])

    result = filter_range(
        values,
        minimum=0.0,
        maximum=10.0,
    )

    np.testing.assert_allclose(
        result,
        np.array([0.0, 2.5, 10.0]),
    )


def test_replace_where_replaces_selected_values() -> None:
    values = np.array([1.0, -2.0, 3.0, -4.0])
    predicate = values < 0.0

    result = replace_where(
        values,
        replacement=0.0,
        predicate=predicate,
    )

    np.testing.assert_allclose(
        result,
        np.array([1.0, 0.0, 3.0, 0.0]),
    )


def test_replace_where_does_not_mutate_input() -> None:
    values = np.array([1.0, -2.0, 3.0])
    predicate = values < 0.0

    replace_where(
        values,
        replacement=0.0,
        predicate=predicate,
    )

    np.testing.assert_allclose(
        values,
        np.array([1.0, -2.0, 3.0]),
    )


def test_replace_where_rejects_non_boolean_predicate() -> None:
    values = np.array([1.0, 2.0])
    predicate = np.array([1, 0])

    with pytest.raises(
        TypeError,
        match="Expected Boolean predicate",
    ):
        replace_where(
            values,
            replacement=0.0,
            predicate=predicate,
        )


def test_replace_where_rejects_mismatched_predicate_shape() -> None:
    values = np.array([1.0, 2.0, 3.0])
    predicate = np.array([True, False])

    with pytest.raises(
        ValueError,
        match="Predicate shape .* does not match",
    ):
        replace_where(
            values,
            replacement=0.0,
            predicate=predicate,
        )


def test_replace_where_rejects_non_finite_replacement() -> None:
    values = np.array([1.0, -2.0])
    predicate = values < 0.0

    with pytest.raises(
        ValueError,
        match="replacement must be finite",
    ):
        replace_where(
            values,
            replacement=np.nan,
            predicate=predicate,
        )