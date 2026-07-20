"""Per-scope cache for loaded test data.

Avoids re-reading the same file multiple times within a scenario (or
feature, if requested). Keys are ``(path, scope)`` pairs.
"""

from __future__ import annotations

from pathlib import Path

from behave_kit._core.types import Scope


class DataCache:
    """Cache of loaded data, keyed by ``(path, scope)``."""

    def __init__(self) -> None:
        self._entries: dict[tuple[str, Scope], object] = {}

    def get(self, path: str | Path, scope: Scope = Scope.SCENARIO) -> object | None:
        return self._entries.get((str(path), scope))

    def set(self, path: str | Path, scope: Scope, data: object) -> None:
        self._entries[(str(path), scope)] = data

    def invalidate(self, scope: Scope) -> None:
        """Remove every entry cached at ``scope``."""
        for key in [key for key in self._entries if key[1] == scope]:
            del self._entries[key]
