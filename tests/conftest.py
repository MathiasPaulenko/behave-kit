"""Shared pytest fixtures for behave-kit tests."""

from __future__ import annotations

from collections.abc import Iterator

import pytest


@pytest.fixture(autouse=True)
def _reset_soft_assert_contextvar() -> Iterator[None]:
    """Reset the soft-assert contextvar between tests to prevent leaks."""
    from behave_kit.assertions.soft import _collector_var

    token = _collector_var.set(None)  # type: ignore[arg-type]
    try:
        yield
    finally:
        _collector_var.reset(token)
