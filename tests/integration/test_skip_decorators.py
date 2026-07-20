"""Integration tests for behave_kit.skip.decorators."""

import platform
import unittest
from types import SimpleNamespace

import pytest

from behave_kit.skip.decorators import (
    skip_if_env,
    skip_if_missing,
    skip_if_no_browser,
    skip_on_os,
)


def test_skip_if_env_active_raises_skip_test() -> None:
    context = SimpleNamespace(config=SimpleNamespace(env="ci"))

    @skip_if_env("ci")
    def step(context: SimpleNamespace) -> str:
        return "executed"

    with pytest.raises(unittest.SkipTest):
        step(context)


def test_skip_if_env_inactive_calls_function() -> None:
    context = SimpleNamespace(config=SimpleNamespace(env="staging"))

    @skip_if_env("ci")
    def step(context: SimpleNamespace) -> str:
        return "executed"

    assert step(context) == "executed"


def test_skip_on_os_active_raises_skip_test() -> None:
    context = SimpleNamespace()
    current_os = platform.system()

    @skip_on_os(current_os)
    def step(context: SimpleNamespace) -> str:
        return "executed"

    with pytest.raises(unittest.SkipTest):
        step(context)


def test_skip_on_os_inactive_calls_function() -> None:
    context = SimpleNamespace()

    @skip_on_os("not-a-real-os")
    def step(context: SimpleNamespace) -> str:
        return "executed"

    assert step(context) == "executed"


def test_skip_if_missing_active_raises_skip_test() -> None:
    context = SimpleNamespace()

    @skip_if_missing("this_module_does_not_exist_anywhere")
    def step(context: SimpleNamespace) -> str:
        return "executed"

    with pytest.raises(unittest.SkipTest):
        step(context)


def test_skip_if_missing_inactive_calls_function() -> None:
    context = SimpleNamespace()

    @skip_if_missing("json")
    def step(context: SimpleNamespace) -> str:
        return "executed"

    assert step(context) == "executed"


def test_skip_if_no_browser_is_applied_directly() -> None:
    context = SimpleNamespace()

    @skip_if_no_browser
    def step(context: SimpleNamespace) -> str:
        return "executed"

    try:
        result = step(context)
    except unittest.SkipTest:
        pass
    else:
        assert result == "executed"


def test_functools_wraps_preserves_metadata() -> None:
    @skip_if_env("ci")
    def my_named_step(context: SimpleNamespace) -> str:
        """My docstring."""
        return "executed"

    assert my_named_step.__name__ == "my_named_step"
    assert my_named_step.__doc__ == "My docstring."
