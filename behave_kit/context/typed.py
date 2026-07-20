"""Typed proxy over the Behave context.

`TypedContext` does not subclass or replace `behave.runner.Context` — it
wraps it. Attribute access and assignment are validated against a plain
schema class's annotations, giving IDE autocompletion and mypy support
without requiring any migration away from the real context.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from behave_kit._core.errors import ScopeError
from behave_kit._core.types import Context

T = TypeVar("T")


class TypedContext(Generic[T]):
    """Schema-validated proxy over a Behave `Context`."""

    def __init__(self, context: Context, schema: type[T]) -> None:
        self._context = context
        self._schema = schema

    def _declared_attrs(self) -> dict[str, Any]:
        return dict(getattr(self._schema, "__annotations__", {}))

    def __getattr__(self, name: str) -> Any:
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        declared = self._declared_attrs()
        if name not in declared:
            raise ScopeError(
                f"'{name}' not declared in {self._schema.__name__}",
                suggestion=f"Declared attributes: {', '.join(sorted(declared)) or '(none)'}",
            )
        return getattr(self._context, name)

    def setup(self, **kwargs: Any) -> None:
        """Type-checked assignment of attributes to the real context."""
        declared = self._declared_attrs()
        for key in kwargs:
            if key not in declared:
                raise ScopeError(
                    f"'{key}' not declared in {self._schema.__name__}",
                    suggestion=f"Declared attributes: {', '.join(sorted(declared)) or '(none)'}",
                )
        for key, value in kwargs.items():
            setattr(self._context, key, value)
