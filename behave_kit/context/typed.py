"""Typed proxy over the Behave context.

`TypedContext` does not subclass or replace `behave.runner.Context` — it
wraps it. Attribute access and assignment are validated against a plain
schema class's annotations, giving IDE autocompletion and mypy support
without requiring any migration away from the real context.
"""

from __future__ import annotations

import types
from typing import Any, Generic, TypeVar, Union, get_args, get_origin, get_type_hints

from behave_kit._core.errors import ScopeError
from behave_kit._core.types import Context

T = TypeVar("T")


def _matches_type(value: object, hint: Any) -> bool:
    """Return True if ``value`` satisfies ``hint`` for common typing constructs."""
    if hint is Any:
        return True
    origin = get_origin(hint)
    if origin is not None:
        if origin is Union or origin is types.UnionType:
            return any(_matches_type(value, arg) for arg in get_args(hint))
        if isinstance(origin, type):
            return isinstance(value, origin)
        return True
    if isinstance(hint, type):
        return isinstance(value, hint)
    return True


class TypedContext(Generic[T]):
    """Schema-validated proxy over a Behave `Context`."""

    def __init__(self, context: Context, schema: type[T]) -> None:
        super().__setattr__("_context", context)
        super().__setattr__("_schema", schema)

    def _declared_attrs(self) -> dict[str, Any]:
        annotations: dict[str, Any] = {}
        for cls in reversed(getattr(self._schema, "__mro__", [self._schema])):
            annotations.update(getattr(cls, "__annotations__", {}))
        return annotations

    def _type_hints(self) -> dict[str, Any]:
        try:
            return get_type_hints(self._schema)
        except Exception:
            return self._declared_attrs()

    def _validate_name(self, name: str) -> None:
        declared = self._declared_attrs()
        if name not in declared:
            raise ScopeError(
                f"'{name}' not declared in {self._schema.__name__}",
                suggestion=f"Declared attributes: {', '.join(sorted(declared)) or '(none)'}",
            )

    def _validate_value(self, name: str, value: Any) -> None:
        hint = self._type_hints().get(name)
        if hint is not None and not _matches_type(value, hint):
            raise ScopeError(
                f"Value for '{name}' must match {hint}, got {type(value).__name__}",
                suggestion="Use a value compatible with the declared type",
            )

    def __getattr__(self, name: str) -> Any:
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        self._validate_name(name)
        return getattr(self._context, name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ("_context", "_schema"):
            super().__setattr__(name, value)
            return
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        self._validate_name(name)
        self._validate_value(name, value)
        setattr(self._context, name, value)

    def setup(self, **kwargs: Any) -> None:
        """Type-checked assignment of attributes to the real context."""
        for key in kwargs:
            self._validate_name(key)
        for key, value in kwargs.items():
            self._validate_value(key, value)
            setattr(self._context, key, value)
