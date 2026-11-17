"""`@data_provider` — register named functions that produce test data on demand.

Uses the shared `Registry` backbone (see `behave_kit._core.registry`), so
registration/lookup errors surface as the same `FixtureError` used by
fixtures and parameter types.
"""

from __future__ import annotations

from collections.abc import Callable

from behave_kit._core.errors import FixtureError
from behave_kit._core.registry import Registry, validate_registration
from behave_kit._core.types import Scope

_registry: Registry[Callable[..., object]] = Registry()


def data_provider(name: str) -> Callable[[Callable[..., object]], Callable[..., object]]:
    """Register ``func`` as the data provider named ``name``."""
    # Fail fast at decoration time — matches ``fixture`` and ``parameter_type``.
    validate_registration(name, Scope.SCENARIO)

    def decorator(func: Callable[..., object]) -> Callable[..., object]:
        """Register ``func`` as the data provider named ``name``."""
        if not callable(func):
            raise FixtureError(
                f"@data_provider('{name}') applied to non-callable {type(func).__name__}",
                suggestion="Apply @data_provider to a function",
            )
        _registry.register(name, func)
        return func

    return decorator


def get_provider(name: str) -> Callable[..., object]:
    """Return the provider function registered under ``name``."""
    return _registry.get(name)
