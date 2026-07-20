"""Generic registry with dependency resolution.

Backbone for fixtures, parameter types and data providers. A single
`Registry[T]` handles registration, lookup, scope filtering and dependency
resolution (including circular-dependency detection) for all three.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

from behave_kit._core.errors import FixtureError
from behave_kit._core.types import Scope

T = TypeVar("T")


@dataclass
class _Entry(Generic[T]):
    item: T
    scope: Scope
    requires: list[str] = field(default_factory=list)


class Registry(Generic[T]):
    """Named registry of items with scopes and dependencies."""

    def __init__(self) -> None:
        self._entries: dict[str, _Entry[T]] = {}

    def register(
        self,
        name: str,
        item: T,
        *,
        scope: Scope = Scope.SCENARIO,
        requires: list[str] | None = None,
    ) -> None:
        """Register ``item`` under ``name``.

        Raises:
            FixtureError: if ``name`` is already registered.
        """
        if not isinstance(name, str):
            raise FixtureError(
                f"Registry name must be a string, got {type(name).__name__}",
                suggestion="Use a string identifier",
            )
        if not isinstance(scope, Scope):
            raise FixtureError(
                f"Registry scope must be a Scope value, got {scope!r}",
                suggestion="Use Scope.SCENARIO, Scope.FEATURE, or Scope.GLOBAL",
            )
        if requires is not None and not (
            isinstance(requires, list) and all(isinstance(dep, str) for dep in requires)
        ):
            raise FixtureError(
                "Registry requires must be a list of strings",
                suggestion="Pass a list of dependency names",
            )
        if name in self._entries:
            raise FixtureError(
                f"'{name}' is already registered",
                suggestion=f"Use a different name or unregister '{name}' first",
            )
        self._entries[name] = _Entry(item=item, scope=scope, requires=list(requires or []))

    def get(self, name: str) -> T:
        """Return the item registered under ``name``.

        Raises:
            FixtureError: if ``name`` is not registered.
        """
        entry = self._entries.get(name)
        if entry is None:
            raise FixtureError(
                f"'{name}' is not registered",
                suggestion=f"Available: {', '.join(sorted(self._entries)) or '(none)'}",
            )
        return entry.item

    def scope_of(self, name: str) -> Scope:
        """Return the scope of the item registered under ``name``."""
        entry = self._entries.get(name)
        if entry is None:
            raise FixtureError(f"'{name}' is not registered")
        return entry.scope

    def resolve_dependencies(self, name: str) -> list[str]:
        """Return the dependency chain for ``name`` in setup order.

        The returned list contains ``name``'s dependencies followed by
        ``name`` itself, each dependency appearing before anything that
        requires it.

        Raises:
            FixtureError: if ``name`` (or a transitive dependency) is not
                registered, or if a circular dependency is detected.
        """
        order: list[str] = []
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(current: str) -> None:
            if current in visited:
                return
            if current in visiting:
                raise FixtureError(
                    f"Circular dependency detected involving '{current}'",
                    suggestion="Break the cycle by removing one of the 'requires' entries",
                )
            entry = self._entries.get(current)
            if entry is None:
                raise FixtureError(
                    f"'{current}' is not registered",
                    suggestion=f"Available: {', '.join(sorted(self._entries)) or '(none)'}",
                )
            visiting.add(current)
            for dependency in entry.requires:
                visit(dependency)
            visiting.discard(current)
            visited.add(current)
            order.append(current)

        visit(name)
        return order

    def names(self, scope: Scope | None = None) -> list[str]:
        """Return registered names, optionally filtered by ``scope``."""
        if scope is None:
            return list(self._entries)
        return [name for name, entry in self._entries.items() if entry.scope == scope]
