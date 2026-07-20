"""Tests for behave_kit.context.typed."""

from types import SimpleNamespace

import pytest

from behave_kit._core.errors import ScopeError
from behave_kit.context.typed import TypedContext


class MySchema:
    driver: object
    base_url: str


def test_getattr_delegates_to_real_context() -> None:
    context = SimpleNamespace(driver="chrome-driver", base_url="https://x.com")
    typed = TypedContext(context, MySchema)
    assert typed.driver == "chrome-driver"
    assert typed.base_url == "https://x.com"


def test_getattr_undeclared_raises_scope_error() -> None:
    context = SimpleNamespace(driver="chrome-driver")
    typed = TypedContext(context, MySchema)
    with pytest.raises(ScopeError):
        typed.not_declared  # noqa: B018


def test_setup_with_declared_keys_sets_real_context() -> None:
    context = SimpleNamespace()
    typed = TypedContext(context, MySchema)
    typed.setup(driver="chrome-driver", base_url="https://x.com")
    assert context.driver == "chrome-driver"
    assert context.base_url == "https://x.com"


def test_setup_with_undeclared_key_raises_scope_error() -> None:
    context = SimpleNamespace()
    typed = TypedContext(context, MySchema)
    with pytest.raises(ScopeError):
        typed.setup(unknown_field="value")


def test_setup_partial_failure_does_not_raise_for_valid_keys_check_first() -> None:
    context = SimpleNamespace()
    typed = TypedContext(context, MySchema)
    with pytest.raises(ScopeError):
        typed.setup(driver="chrome-driver", unknown_field="value")
    # Validation happens before assignment: nothing should have been set.
    assert not hasattr(context, "driver")


def test_dunder_attribute_access_raises_attribute_error_not_scope_error() -> None:
    context = SimpleNamespace()
    typed = TypedContext(context, MySchema)
    with pytest.raises(AttributeError):
        typed.__wrapped__  # noqa: B018
