"""`assert_under` and `@timed` — time-based assertions for performance checks.

`assert_under` verifies that a callable completes within a deadline.
`@timed` is a decorator that asserts a step finishes within a time limit.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from functools import wraps
from typing import Concatenate, ParamSpec, TypeVar, cast

from behave_kit._core.errors import BehaveKitError
from behave_kit._core.types import Context

P = ParamSpec("P")
R = TypeVar("R")


class TimeoutExceededError(BehaveKitError):
    """Raised when a callable takes longer than the allowed time."""


def assert_under(
    seconds: float,
    func: Callable[[], R],
    *,
    message: str = "",
) -> R:
    """Run ``func`` and assert it completes within ``seconds``.

    Args:
        seconds: Maximum allowed execution time.
        func: Zero-argument callable to time.
        message: Custom message for the timeout error.

    Returns:
        The return value of ``func``.

    Raises:
        TimeoutExceededError: If ``func`` takes longer than ``seconds``.
    """
    if seconds < 0:
        raise BehaveKitError(
            f"seconds must be non-negative, got {seconds}",
            suggestion="Use a positive float for the time limit",
        )

    start = time.monotonic()
    result = func()
    elapsed = time.monotonic() - start
    if elapsed > seconds:
        raise TimeoutExceededError(
            message or f"Execution took {elapsed:.3f}s, expected under {seconds}s",
            suggestion="Optimize the operation or increase the time limit",
        )
    return result


def timed(
    seconds: float,
) -> Callable[
    [Callable[Concatenate[Context, P], R]],
    Callable[Concatenate[Context, P], R],
]:
    """Decorator: assert a step function completes within ``seconds``.

    Usage::

        @timed(2.0)
        @when("I fetch the data")
        def step(context): ...

    Raises:
        BehaveKitError: If ``seconds`` is negative.
    """
    if seconds < 0:
        raise BehaveKitError(
            f"seconds must be non-negative, got {seconds}",
            suggestion="Use a positive float for the time limit",
        )

    def decorator(
        func: Callable[Concatenate[Context, P], R],
    ) -> Callable[Concatenate[Context, P], R]:
        """Wrap ``func`` to assert it finishes within the time limit."""

        @wraps(func)
        def wrapper(context: Context, *args: P.args, **kwargs: P.kwargs) -> R:
            """Time the step and raise if it exceeds the limit."""
            start = time.monotonic()
            result = func(context, *args, **kwargs)
            elapsed = time.monotonic() - start
            if elapsed > seconds:
                raise TimeoutExceededError(
                    f"Step '{func.__name__}' took {elapsed:.3f}s, expected under {seconds}s",
                    suggestion="Optimize the step or increase the time limit",
                )
            return result

        return cast("Callable[Concatenate[Context, P], R]", wrapper)

    return decorator
