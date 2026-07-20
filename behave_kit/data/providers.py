"""`@data_provider` — register named functions that produce test data on demand.

Uses the shared `Registry` backbone (see `behave_kit._core.registry`), so
registration/lookup errors surface as the same `FixtureError` used by
fixtures and parameter types.
"""

from __future__ import annotations

from collections.abc import Callable

from behave_kit._core.registry import Registry

_registry: Registry[Callable[..., object]] = Registry()


def data_provider(name: str) -> Callable[[Callable[..., object]], Callable[..., object]]:
    """Register ``func`` as the data provider named ``name``."""

    def decorator(func: Callable[..., object]) -> Callable[..., object]:
        _registry.register(name, func)
        return func

    return decorator


def get_provider(name: str) -> Callable[..., object]:
    """Return the provider function registered under ``name``."""
    return _registry.get(name)
