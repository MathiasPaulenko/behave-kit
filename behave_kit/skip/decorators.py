"""Conditional skip decorators for Behave step functions.

Behave has no `step.skip()` API. The idiomatic way to skip a step (and have
Behave report it as skipped, not failed) is to raise `unittest.SkipTest`
from within the step. Every decorator here checks its condition at call
time, not at decoration time, so `context` (and `context.config`) can be
inspected.
"""

from __future__ import annotations

import functools
import unittest
from collections.abc import Callable
from typing import Concatenate, ParamSpec, TypeVar, cast

from behave_kit._core.errors import BehaveKitError
from behave_kit._core.types import Context
from behave_kit.skip.conditions import is_env, is_missing, is_no_browser, is_os

P = ParamSpec("P")
R = TypeVar("R")


def _validate_str(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise BehaveKitError(
            f"{label} must be a string, got {type(value).__name__}",
            suggestion=f'Use @{label.lower().replace(" ", "_")}("value")',
        )
    return value


def skip_if_env(
    env_name: str,
) -> Callable[[Callable[Concatenate[Context, P], R]], Callable[Concatenate[Context, P], R]]:
    """Skip the step when ``context.config.env == env_name``."""
    _validate_str(env_name, "skip_if_env")

    def decorator(
        func: Callable[Concatenate[Context, P], R],
    ) -> Callable[Concatenate[Context, P], R]:
        @functools.wraps(func)
        def wrapper(context: Context, *args: P.args, **kwargs: P.kwargs) -> R:
            if is_env(context, env_name):
                raise unittest.SkipTest(f"Skipped on env={env_name}")
            return func(context, *args, **kwargs)

        return cast("Callable[Concatenate[Context, P], R]", wrapper)

    return decorator


def skip_on_os(
    os_name: str,
) -> Callable[[Callable[Concatenate[Context, P], R]], Callable[Concatenate[Context, P], R]]:
    """Skip the step when running on ``os_name``."""
    _validate_str(os_name, "skip_on_os")

    def decorator(
        func: Callable[Concatenate[Context, P], R],
    ) -> Callable[Concatenate[Context, P], R]:
        @functools.wraps(func)
        def wrapper(context: Context, *args: P.args, **kwargs: P.kwargs) -> R:
            if is_os(os_name):
                raise unittest.SkipTest(f"Skipped on os={os_name}")
            return func(context, *args, **kwargs)

        return cast("Callable[Concatenate[Context, P], R]", wrapper)

    return decorator


def skip_if_missing(
    module_name: str,
) -> Callable[[Callable[Concatenate[Context, P], R]], Callable[Concatenate[Context, P], R]]:
    """Skip the step when ``module_name`` cannot be imported."""
    _validate_str(module_name, "skip_if_missing")

    def decorator(
        func: Callable[Concatenate[Context, P], R],
    ) -> Callable[Concatenate[Context, P], R]:
        @functools.wraps(func)
        def wrapper(context: Context, *args: P.args, **kwargs: P.kwargs) -> R:
            if is_missing(module_name):
                raise unittest.SkipTest(f"Skipped: module '{module_name}' is not installed")
            return func(context, *args, **kwargs)

        return cast("Callable[Concatenate[Context, P], R]", wrapper)

    return decorator


def skip_if_no_browser(
    func: Callable[Concatenate[Context, P], R] | None = None,
) -> (
    Callable[Concatenate[Context, P], R]
    | Callable[[Callable[Concatenate[Context, P], R]], Callable[Concatenate[Context, P], R]]
):
    """Skip the step when Selenium is not installed.

    Can be applied directly (``@skip_if_no_browser``) or called as a
    decorator factory (``@skip_if_no_browser()``).
    """

    def decorator(
        f: Callable[Concatenate[Context, P], R],
    ) -> Callable[Concatenate[Context, P], R]:
        @functools.wraps(f)
        def wrapper(context: Context, *args: P.args, **kwargs: P.kwargs) -> R:
            if is_no_browser():
                raise unittest.SkipTest("Skipped: selenium is not installed")
            return f(context, *args, **kwargs)

        return cast("Callable[Concatenate[Context, P], R]", wrapper)

    if func is not None:
        return decorator(func)
    return decorator
