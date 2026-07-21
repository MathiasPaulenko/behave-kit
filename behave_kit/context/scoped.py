"""Automatic cleanup of context attributes registered via `@scoped`.

Prevents leaks between scenarios: an attribute set with `@scoped("driver")`
is deleted from the context once its scope ends, instead of silently
surviving into the next scenario.
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Concatenate, ParamSpec, TypeVar, cast

from behave_kit._core.logging import get_logger
from behave_kit._core.types import Context, Scope

logger = get_logger("context.scoped")

_TRACK_KEY = "_behave_kit_scoped"

P = ParamSpec("P")
R = TypeVar("R")


def _tracked(context: Context) -> list[tuple[str, Scope]]:
    return list(getattr(context, _TRACK_KEY, None) or [])


def _track(context: Context, name: str, scope: Scope) -> None:
    tracked = _tracked(context)
    if (name, scope) not in tracked:
        tracked.append((name, scope))
    setattr(context, _TRACK_KEY, tracked)


def scoped(
    name: str,
    scope: Scope = Scope.SCENARIO,
) -> Callable[
    [Callable[Concatenate[Context, P], R]],
    Callable[Concatenate[Context, P], R],
]:
    """Decorator: track ``context.<name>`` so it is cleaned up automatically.

    After the wrapped step function runs, ``name`` is registered for
    cleanup at the given ``scope`` (see `cleanup_scoped`).
    """

    def decorator(
        func: Callable[Concatenate[Context, P], R],
    ) -> Callable[Concatenate[Context, P], R]:
        """Wrap ``func`` to register ``name`` for cleanup after it runs."""
        @functools.wraps(func)
        def wrapper(context: Context, *args: P.args, **kwargs: P.kwargs) -> R:
            """Run the wrapped function and track ``name`` for cleanup."""
            try:
                return func(context, *args, **kwargs)
            finally:
                _track(context, name, scope)

        return cast("Callable[Concatenate[Context, P], R]", wrapper)

    return decorator


def cleanup_scoped(context: Context, scope: Scope = Scope.SCENARIO) -> None:
    """Delete every attribute tracked with `@scoped` at the given ``scope``."""
    remaining: list[tuple[str, Scope]] = []
    for tracked_name, tracked_scope in _tracked(context):
        if tracked_scope != scope:
            remaining.append((tracked_name, tracked_scope))
            continue
        try:
            delattr(context, tracked_name)
        except AttributeError:
            logger.warning("Scoped attribute '%s' was already removed or never set", tracked_name)
    setattr(context, _TRACK_KEY, remaining)
