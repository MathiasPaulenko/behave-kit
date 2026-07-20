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

from behave_kit._core.types import Context
from behave_kit.skip.conditions import is_env, is_missing, is_no_browser, is_os

P = ParamSpec("P")
R = TypeVar("R")


def skip_if_env(
    env_name: str,
) -> Callable[[Callable[Concatenate[Context, P], R]], Callable[Concatenate[Context, P], R]]:
    """Skip the step when ``context.config.env == env_name``."""

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
    func: Callable[Concatenate[Context, P], R],
) -> Callable[Concatenate[Context, P], R]:
    """Skip the step when Selenium is not installed.

    Not a decorator factory -- apply directly: ``@skip_if_no_browser``.
    """

    @functools.wraps(func)
    def wrapper(context: Context, *args: P.args, **kwargs: P.kwargs) -> R:
        if is_no_browser():
            raise unittest.SkipTest("Skipped: selenium is not installed")
        return func(context, *args, **kwargs)

    return cast("Callable[Concatenate[Context, P], R]", wrapper)
