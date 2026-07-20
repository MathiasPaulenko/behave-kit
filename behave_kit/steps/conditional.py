"""`@when_if` — run a step only when a condition holds, skip silently otherwise."""

from __future__ import annotations

import functools
import unittest
from collections.abc import Callable
from typing import Concatenate, ParamSpec, TypeVar, cast

from behave_kit._core.errors import BehaveKitError
from behave_kit._core.types import Context

P = ParamSpec("P")
R = TypeVar("R")


def _as_bool(value: object) -> bool:
    """Return a scalar bool, tolerating array-like objects."""
    try:
        return bool(value)
    except (ValueError, TypeError):
        pass
    try:
        return bool(value.all())  # type: ignore[attr-defined]
    except (AttributeError, ValueError, TypeError):
        pass
    return False


def when_if(
    condition: Callable[[Context], object],
) -> Callable[
    [Callable[Concatenate[Context, P], R]],
    Callable[Concatenate[Context, P], R],
]:
    """Decorator: execute the step only if ``condition(context)`` is true.

    When the condition is false, the step is skipped (via
    `unittest.SkipTest`) rather than executed or failed.
    """

    def decorator(
        func: Callable[Concatenate[Context, P], R],
    ) -> Callable[Concatenate[Context, P], R]:
        if not callable(func):
            raise BehaveKitError(
                "@when_if was applied without parentheses",
                suggestion="Use @when_if(lambda ctx: ...) or @when_if(my_condition)",
            )

        @functools.wraps(func)
        def wrapper(context: Context, *args: P.args, **kwargs: P.kwargs) -> R:
            if not _as_bool(condition(context)):
                raise unittest.SkipTest("Skipped: when_if condition was false")
            return func(context, *args, **kwargs)

        return cast("Callable[Concatenate[Context, P], R]", wrapper)

    return decorator
