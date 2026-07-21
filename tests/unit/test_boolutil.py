"""Tests for behave_kit._core.boolutil."""

from behave_kit._core.boolutil import as_bool


def test_as_bool_returns_true_for_truthy_scalar() -> None:
    assert as_bool(True) is True
    assert as_bool(1) is True
    assert as_bool("yes") is True


def test_as_bool_returns_false_for_falsy_scalar() -> None:
    assert as_bool(False) is False
    assert as_bool(0) is False
    assert as_bool("") is False
    assert as_bool(None) is False


def test_as_bool_tolerates_array_like_with_all_true() -> None:
    try:
        import numpy as np  # type: ignore[import-not-found]
    except ImportError:
        return
    assert as_bool(np.array([True, True])) is True


def test_as_bool_returns_false_for_array_like_with_any_false() -> None:
    try:
        import numpy as np  # type: ignore[import-not-found]
    except ImportError:
        return
    assert as_bool(np.array([True, False])) is False


def test_as_bool_returns_false_for_object_with_failing_bool() -> None:
    class FailingBool:
        def __bool__(self) -> bool:
            raise ValueError("no scalar bool")

    assert as_bool(FailingBool()) is False
