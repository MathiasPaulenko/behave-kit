"""Tests for behave_kit.continue_after_failed."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from behave.model import Scenario

from behave_kit.continue_after_failed import continue_after_failed, continue_on_failure


@pytest.fixture(autouse=True)
def _reset_scenario_continue_after_failed() -> Iterator[None]:
    original = getattr(Scenario, "continue_after_failed_step", False)
    Scenario.continue_after_failed_step = False
    yield
    Scenario.continue_after_failed_step = original


# ---------------------------------------------------------------------------
# Basic functionality
# ---------------------------------------------------------------------------


def test_continue_after_failed_sets_class_attribute() -> None:
    continue_after_failed(True)
    assert Scenario.continue_after_failed_step is True


def test_continue_after_failed_false_restores_default() -> None:
    continue_after_failed(True)
    assert Scenario.continue_after_failed_step is True
    continue_after_failed(False)
    assert Scenario.continue_after_failed_step is False


def test_continue_on_failure_enables_temporarily() -> None:
    assert Scenario.continue_after_failed_step is False
    with continue_on_failure():
        assert Scenario.continue_after_failed_step is True
    assert Scenario.continue_after_failed_step is False


def test_continue_on_failure_restores_previous_true_value() -> None:
    continue_after_failed(True)
    with continue_on_failure():
        assert Scenario.continue_after_failed_step is True
    assert Scenario.continue_after_failed_step is True


def test_continue_on_failure_restores_on_exception() -> None:
    assert Scenario.continue_after_failed_step is False
    with pytest.raises(RuntimeError, match="boom"), continue_on_failure():
        raise RuntimeError("boom")
    assert Scenario.continue_after_failed_step is False


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_continue_on_failure_nested_restores_inner_then_outer() -> None:
    """Nested context managers restore values in LIFO order."""
    continue_after_failed(False)
    with continue_on_failure():
        assert Scenario.continue_after_failed_step is True
        with continue_on_failure():
            assert Scenario.continue_after_failed_step is True
        assert Scenario.continue_after_failed_step is True
    assert Scenario.continue_after_failed_step is False


def test_continue_on_failure_with_generator_exception_restores() -> None:
    """Exception from a generator inside the block still restores."""

    def _boom() -> Iterator[int]:
        yield 1
        raise ValueError("generator boom")

    assert Scenario.continue_after_failed_step is False
    with pytest.raises(ValueError, match="generator boom"), continue_on_failure():
        list(_boom())
    assert Scenario.continue_after_failed_step is False


def test_continue_on_failure_keyboard_interrupt_restores() -> None:
    """BaseException subclasses like KeyboardInterrupt also restore."""
    assert Scenario.continue_after_failed_step is False
    with pytest.raises(KeyboardInterrupt), continue_on_failure():
        raise KeyboardInterrupt
    assert Scenario.continue_after_failed_step is False


def test_continue_after_failed_idempotent_on_repeated_calls() -> None:
    """Calling the function multiple times with the same value is safe."""
    for _ in range(5):
        continue_after_failed(True)
    assert Scenario.continue_after_failed_step is True
    for _ in range(5):
        continue_after_failed(False)
    assert Scenario.continue_after_failed_step is False


def test_continue_on_failure_yields_none() -> None:
    """The context manager yields nothing (no value assigned)."""
    with continue_on_failure() as value:
        assert value is None


def test_continue_after_failed_does_not_affect_other_class_attributes() -> None:
    """Setting continue_after_failed_step should not touch other Scenario attrs."""
    original_name = Scenario.__name__
    continue_after_failed(True)
    assert Scenario.__name__ == original_name


def test_continue_on_failure_restores_when_already_true_before_block() -> None:
    """If the attribute was True before entering, it stays True after."""
    continue_after_failed(True)
    with continue_on_failure():
        pass
    assert Scenario.continue_after_failed_step is True


def test_continue_after_failed_default_parameter_is_true() -> None:
    """Calling without arguments defaults to True."""
    continue_after_failed()
    assert Scenario.continue_after_failed_step is True


def test_continue_on_failure_can_be_entered_and_exited_multiple_times() -> None:
    """The factory can be called repeatedly to create fresh CMs."""
    for _ in range(3):
        with continue_on_failure():
            assert Scenario.continue_after_failed_step is True
        assert Scenario.continue_after_failed_step is False


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def test_continue_after_failed_rejects_non_bool_int() -> None:
    """Passing an int should raise BehaveKitError."""
    from behave_kit._core.errors import BehaveKitError

    with pytest.raises(BehaveKitError, match="must be a bool"):
        continue_after_failed(1)  # type: ignore[arg-type]


def test_continue_after_failed_rejects_non_bool_none() -> None:
    """Passing None should raise BehaveKitError, not silently set falsy."""
    from behave_kit._core.errors import BehaveKitError

    with pytest.raises(BehaveKitError, match="must be a bool"):
        continue_after_failed(None)  # type: ignore[arg-type]


def test_continue_after_failed_rejects_non_bool_string() -> None:
    """Passing a string should raise BehaveKitError."""
    from behave_kit._core.errors import BehaveKitError

    with pytest.raises(BehaveKitError, match="must be a bool"):
        continue_after_failed("yes")  # type: ignore[arg-type]
