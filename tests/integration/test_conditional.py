"""Integration tests for behave_kit.steps.conditional."""

import unittest
from types import SimpleNamespace

import pytest

from behave_kit.steps.conditional import when_if


def test_when_if_condition_true_calls_function() -> None:
    context = SimpleNamespace(env="staging")

    @when_if(lambda ctx: ctx.env == "staging")
    def step(context: SimpleNamespace) -> str:
        return "executed"

    assert step(context) == "executed"


def test_when_if_condition_false_raises_skip_test() -> None:
    context = SimpleNamespace(env="production")

    @when_if(lambda ctx: ctx.env == "staging")
    def step(context: SimpleNamespace) -> str:
        return "executed"

    with pytest.raises(unittest.SkipTest):
        step(context)


def test_when_if_with_named_condition_function() -> None:
    def is_staging(ctx: SimpleNamespace) -> bool:
        return bool(ctx.env == "staging")

    context = SimpleNamespace(env="staging")

    @when_if(is_staging)
    def step(context: SimpleNamespace) -> str:
        return "executed"

    assert step(context) == "executed"


def test_functools_wraps_preserves_name_and_doc() -> None:
    @when_if(lambda ctx: True)
    def my_named_step(context: SimpleNamespace) -> str:
        """My docstring."""
        return "executed"

    assert my_named_step.__name__ == "my_named_step"
    assert my_named_step.__doc__ == "My docstring."


def test_when_if_detects_missing_parentheses() -> None:
    from behave_kit._core.errors import BehaveKitError

    @when_if
    def step(context: SimpleNamespace) -> str:
        return "executed"

    with pytest.raises(BehaveKitError, match="without parentheses"):
        step(SimpleNamespace())


def test_when_if_tolerates_array_like_condition() -> None:
    try:
        import numpy as np  # type: ignore[import-not-found]
    except ImportError:
        pytest.skip("numpy not installed")

    context = SimpleNamespace(env="staging")

    @when_if(lambda ctx: np.array([True, True]))
    def step(context: SimpleNamespace) -> str:
        return "executed"

    assert step(context) == "executed"
