"""Tests for assert_soft_raises in behave_kit.assertions.soft."""

import pytest

from behave_kit.assertions.soft import assert_soft_raises, soft_asserts


def test_assert_soft_raises_passes_when_expected_exception_raised() -> None:
    with soft_asserts() as sa:
        sa.assert_soft_raises(ValueError, lambda: int("abc"))
    assert sa.report().failure_count == 0


def test_assert_soft_raises_fails_when_no_exception_raised() -> None:
    with pytest.raises(AssertionError, match="no exception"), soft_asserts() as sa:
        sa.assert_soft_raises(ValueError, lambda: None)
    assert sa.report().failure_count == 1


def test_assert_soft_raises_fails_when_wrong_exception_raised() -> None:
    def raise_type_error() -> None:
        raise TypeError("wrong")

    with pytest.raises(AssertionError, match="TypeError"), soft_asserts() as sa:
        sa.assert_soft_raises(ValueError, raise_type_error)
    assert sa.report().failure_count == 1
    assert "TypeError" in sa.report().failures[0].actual


def test_assert_soft_raises_accepts_tuple_of_exception_types() -> None:
    def raise_key_error() -> None:
        raise KeyError("k")

    with soft_asserts() as sa:
        sa.assert_soft_raises((ValueError, KeyError), raise_key_error)
    assert sa.report().failure_count == 0


def test_assert_soft_raises_tuple_no_exception_raised() -> None:
    with pytest.raises(AssertionError, match="ValueError or KeyError"), soft_asserts() as sa:
        sa.assert_soft_raises((ValueError, KeyError), lambda: None)
    assert sa.report().failure_count == 1
    assert "ValueError or KeyError" in sa.report().failures[0].expected


def test_assert_soft_raises_tuple_wrong_exception_raised() -> None:
    def raise_type_error() -> None:
        raise TypeError("wrong")

    with pytest.raises(AssertionError, match="TypeError"), soft_asserts() as sa:
        sa.assert_soft_raises((ValueError, KeyError), raise_type_error)
    assert sa.report().failure_count == 1
    assert "ValueError or KeyError" in sa.report().failures[0].expected
    assert "TypeError" in sa.report().failures[0].actual


def test_module_level_assert_soft_raises_works() -> None:
    with pytest.raises(AssertionError, match="Soft assertion failures"), soft_asserts():
        assert_soft_raises(ValueError, lambda: None)


def test_assert_soft_raises_custom_message() -> None:
    with pytest.raises(AssertionError, match="custom msg"), soft_asserts() as sa:
        sa.assert_soft_raises(ValueError, lambda: None, msg="custom msg")
    assert sa.report().failure_count == 1


def test_assert_soft_raises_lets_system_exit_propagate() -> None:
    def raise_system_exit() -> None:
        raise SystemExit(1)

    with pytest.raises(SystemExit), soft_asserts() as sa:
        sa.assert_soft_raises(ValueError, raise_system_exit)
    assert sa.report().failure_count == 0


def test_assert_soft_raises_lets_keyboard_interrupt_propagate() -> None:
    def raise_keyboard_interrupt() -> None:
        raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt), soft_asserts() as sa:
        sa.assert_soft_raises(ValueError, raise_keyboard_interrupt)
    assert sa.report().failure_count == 0


def test_assert_soft_raises_rejects_empty_tuple() -> None:
    from behave_kit._core.errors import BehaveKitError

    with pytest.raises(BehaveKitError, match="must not be empty"), soft_asserts() as sa:
        sa.assert_soft_raises((), lambda: None)
