"""Integration tests for behave_kit.assertions.soft."""

from types import SimpleNamespace

import pytest

from behave_kit._core.errors import BehaveKitError
from behave_kit.assertions.soft import (
    assert_soft,
    assert_soft_equals,
    assert_soft_is_none,
    assert_soft_true,
    soft_asserts,
    use_soft_asserts,
)


def test_assert_soft_without_active_collector_raises() -> None:
    with pytest.raises(BehaveKitError):
        assert_soft(True)


def test_use_soft_asserts_attaches_collector_to_context() -> None:
    context = SimpleNamespace()
    collector = use_soft_asserts(context)
    assert context._behave_kit_soft is collector
    assert_soft(True)
    assert_soft(False, "boom")
    report = collector.report()
    assert report.failure_count == 1


def test_soft_asserts_context_manager_collects_multiple_failures() -> None:
    with (
        pytest.raises(AssertionError, match=r"Soft assertion failures \(2\)"),
        soft_asserts() as sa,
    ):
        sa.assert_soft(True, "should pass")
        sa.assert_soft(False, "first failure")
        sa.assert_soft_equals(1, 2, "second failure")


def test_soft_asserts_context_manager_passes_when_no_failures() -> None:
    with soft_asserts() as sa:
        sa.assert_soft(True)
        sa.assert_soft_true(1)
        sa.assert_soft_is_none(None)


def test_soft_asserts_module_level_functions_inside_context_manager() -> None:
    with pytest.raises(AssertionError), soft_asserts():
        assert_soft(False, "module level failure")
        assert_soft_equals(1, 2)
        assert_soft_true(0)
        assert_soft_is_none("not none")


def test_report_format_includes_expected_and_actual() -> None:
    with pytest.raises(AssertionError) as exc_info, soft_asserts() as sa:
        sa.assert_soft_equals(1, 2, "mismatch")
    text = str(exc_info.value)
    assert "Soft assertion failures (1)" in text
    assert "Expected: 2, Got: 1" in text


def test_raise_if_failed_raises_when_there_are_failures() -> None:
    with soft_asserts() as sa:
        pass
    sa.assert_soft(False, "delayed failure")
    with pytest.raises(AssertionError):
        sa.raise_if_failed()


def test_collector_reset_between_soft_asserts_blocks() -> None:
    with soft_asserts() as first:
        first.assert_soft(True)
    with soft_asserts() as second:
        second.assert_soft(True)
    assert first.report().failure_count == 0
    assert second.report().failure_count == 0


def test_assert_soft_tolerates_array_like_conditions() -> None:
    try:
        import numpy as np  # type: ignore[import-not-found]
    except ImportError:
        pytest.skip("numpy not installed")
    with soft_asserts() as sa:
        sa.assert_soft(np.array([True, True]))
        sa.assert_soft_true(np.array([True, True]))
        sa.assert_soft_equals(np.array([1, 2]), np.array([1, 2]))
    assert sa.report().failure_count == 0


def test_teardown_resets_soft_collector() -> None:
    from behave_kit.hooks import setup, teardown

    context = SimpleNamespace()
    setup(context)
    collector = context._behave_kit_soft
    assert_soft(False, "failure")
    with pytest.raises(AssertionError):
        teardown(context)
    assert context._behave_kit_soft is not collector
    assert context._behave_kit_soft.report().failure_count == 0
