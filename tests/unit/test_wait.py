"""Tests for behave_kit.wait."""

import pytest

from behave_kit._core.errors import BehaveKitError
from behave_kit.wait import wait_until


def test_wait_until_returns_immediately_when_condition_is_true() -> None:
    wait_until(lambda: True, timeout=1, interval=0.1)


def test_wait_until_times_out_when_condition_never_true() -> None:
    with pytest.raises(TimeoutError, match="timed out"):
        wait_until(lambda: False, timeout=0.3, interval=0.1)


def test_wait_until_polls_until_condition_becomes_true() -> None:
    counter = {"n": 0}

    def condition() -> bool:
        counter["n"] += 1
        return counter["n"] >= 3

    wait_until(condition, timeout=2, interval=0.05)
    assert counter["n"] == 3


def test_wait_until_rejects_negative_timeout() -> None:
    with pytest.raises(BehaveKitError, match="non-negative"):
        wait_until(lambda: True, timeout=-1)


def test_wait_until_rejects_zero_interval() -> None:
    with pytest.raises(BehaveKitError, match="positive"):
        wait_until(lambda: True, timeout=1, interval=0)


def test_wait_until_custom_message_in_timeout_error() -> None:
    with pytest.raises(TimeoutError, match="custom message"):
        wait_until(lambda: False, timeout=0.2, interval=0.1, message="custom message")


def test_wait_until_tolerates_array_like_truthy() -> None:
    try:
        import numpy as np  # type: ignore[import-not-found]
    except ImportError:
        pytest.skip("numpy not installed")
    wait_until(lambda: np.array([True, True]), timeout=1, interval=0.1)


def test_wait_until_timeout_zero_checks_once_then_raises() -> None:
    with pytest.raises(TimeoutError, match="timed out"):
        wait_until(lambda: False, timeout=0, interval=0.1)
