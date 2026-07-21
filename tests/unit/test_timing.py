"""Tests for behave_kit.timing."""

import time

import pytest

from behave_kit._core.errors import BehaveKitError
from behave_kit.timing import TimeoutExceededError, assert_under, timed


def test_assert_under_passes_when_fast_enough() -> None:
    result = assert_under(1.0, lambda: 42)
    assert result == 42


def test_assert_under_raises_when_too_slow() -> None:
    def slow_func() -> None:
        time.sleep(0.3)

    with pytest.raises(TimeoutExceededError, match="took"):
        assert_under(0.1, slow_func)


def test_assert_under_custom_message() -> None:
    with pytest.raises(TimeoutExceededError, match="too slow"):
        assert_under(0.1, lambda: time.sleep(0.3), message="too slow")


def test_assert_under_rejects_negative_seconds() -> None:
    with pytest.raises(BehaveKitError, match="non-negative"):
        assert_under(-1, lambda: None)


def test_timed_decorator_passes_when_fast() -> None:
    @timed(1.0)
    def step(context: object) -> int:
        return 7

    assert step(object()) == 7


def test_timed_decorator_raises_when_slow() -> None:
    @timed(0.05)
    def step(context: object) -> None:
        time.sleep(0.2)

    with pytest.raises(TimeoutExceededError, match="took"):
        step(object())


def test_timed_preserves_function_name() -> None:
    @timed(1.0)
    def my_step(context: object) -> None:
        pass

    assert my_step.__name__ == "my_step"


def test_timed_rejects_negative_seconds() -> None:
    with pytest.raises(BehaveKitError, match="non-negative"):
        timed(-1.0)  # type: ignore[unused-coro]


def test_timed_accepts_zero_seconds() -> None:
    @timed(0.0)
    def fast_step(context: object) -> int:
        return 42

    assert fast_step.__name__ == "fast_step"
