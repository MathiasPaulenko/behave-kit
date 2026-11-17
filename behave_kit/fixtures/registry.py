"""`@fixture` — register tag-based fixtures with scope and dependencies.

A fixture is a callable ``(context) -> FixtureResult`` where
``FixtureResult`` is either:

- ``None`` — the function performed setup directly, no teardown needed.
- ``(setup_fn, teardown_fn)`` — two callables, both receiving ``context``.
  ``setup_fn`` is called immediately; ``teardown_fn`` is deferred until
  the scope ends.

Fixture names match Behave tags: a scenario tagged ``@database``
triggers the fixture named ``"database"``.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from behave_kit._core.errors import FixtureError
from behave_kit._core.registry import Registry, validate_registration
from behave_kit._core.types import Context, Scope

FixtureSetup = Callable[[Context], None]
FixtureTeardown = Callable[[Context], None]
FixtureResult = tuple[FixtureSetup, FixtureTeardown] | None
FixtureFactory = Callable[[Context], FixtureResult]

_registry: Registry[FixtureFactory] = Registry()


def _normalize_requires(requires: str | list[str] | None) -> list[str]:
    if requires is None:
        return []
    if isinstance(requires, str):
        return [requires]
    if not isinstance(requires, Iterable):
        raise FixtureError(
            f"requires must be a string or a list of strings, got {type(requires).__name__}",
            suggestion="Pass a dependency name or a list of names",
        )
    return list(requires)


def fixture(
    name: str,
    scope: Scope = Scope.SCENARIO,
    requires: str | list[str] | None = None,
) -> Callable[[FixtureFactory], FixtureFactory]:
    """Register ``func`` as the fixture named ``name``.

    :param name: Fixture name (matches a Behave tag).
    :param scope: Lifetime of the fixture (scenario or feature).
    :param requires: Other fixture names this one depends on.
        Accepts a single string or a list of strings.
    """

    # Validate eagerly so bad arguments fail at decoration time,
    # not when the inner decorator is applied.
    validate_registration(name, scope)
    normalized_requires = _normalize_requires(requires)

    def decorator(func: FixtureFactory) -> FixtureFactory:
        """Register ``func`` as the fixture named ``name``."""
        if not callable(func):
            raise FixtureError(
                f"@fixture('{name}') applied to non-callable {type(func).__name__}",
                suggestion="Apply @fixture to a function",
            )
        _registry.register(name, func, scope=scope, requires=normalized_requires)
        return func

    return decorator


def get_fixture(name: str) -> FixtureFactory:
    """Return the fixture factory registered under ``name``."""
    return _registry.get(name)


def fixture_names(scope: Scope | None = None) -> list[str]:
    """Return registered fixture names, optionally filtered by ``scope``."""
    return _registry.names(scope)


def fixture_scope(name: str) -> Scope:
    """Return the scope of the fixture registered under ``name``."""
    return _registry.scope_of(name)


def resolve_fixture_order(name: str) -> list[str]:
    """Return the dependency chain for ``name`` in setup order."""
    return _registry.resolve_dependencies(name)
