"""`@parameter_type` — register custom step-parameter converters.

Registered types are usable in two ways:

* In Behave step patterns — ``{name:Type}`` placeholders are converted
  automatically (types are wired into Behave's parse/cfparse matcher).
* Standalone — via `convert(name, text)`.

Ships built-in converters for common types (int, float, date, datetime,
decimal, email, url) via `register_builtin_types()`.
"""

from __future__ import annotations

import contextlib
import re
from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from behave_kit._core.errors import StepError
from behave_kit._core.registry import Registry

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_URL_PATTERN = re.compile(r"^https?://\S+$")

_registry: Registry[Callable[[str], Any]] = Registry()
_patterns: dict[str, str] = {}


def _register_with_behave(name: str, func: Callable[[str], Any], pattern: str) -> None:
    """Make ``{param:name}`` usable in Behave parse/cfparse step patterns.

    Behave resolves ``{param:Type}`` through the ``pattern`` attribute of the
    registered converter (same mechanism as ``@parse.with_pattern``).  Types
    are registered on ``ParseMatcher`` directly so they are also visible to
    ``cfparse``, which shares the same type registry.
    """
    from behave.matchers import ParseMatcher

    if pattern:
        with contextlib.suppress(AttributeError, TypeError):
            func.pattern = pattern  # type: ignore[attr-defined]
    ParseMatcher.register_type(**{name: func})


def parameter_type(
    name: str,
    pattern: str = "",
) -> Callable[[Callable[[str], Any]], Callable[[str], Any]]:
    """Register ``func`` as the converter for parameter type ``name``.

    The type is also registered with Behave, so ``{param:name}`` placeholders
    in ``@given``/``@when``/``@then`` patterns (parse/cfparse matchers) are
    converted automatically.  ``pattern`` is the regular expression used to
    match the parameter text; when omitted, Behave falls back to its default
    "anything" pattern.
    """

    def decorator(func: Callable[[str], Any]) -> Callable[[str], Any]:
        """Register ``func`` as the converter for ``name``."""
        _registry.register(name, func)
        _patterns[name] = pattern
        _register_with_behave(name, func, pattern)
        return func

    return decorator


def get_parameter_type_pattern(name: str) -> str | None:
    """Return the registered pattern for ``name``, or ``None`` if not registered."""
    return _patterns.get(name)


def convert(name: str, match_string: str) -> Any:
    """Apply the converter registered under ``name`` to ``match_string``."""
    if not isinstance(match_string, str):
        raise StepError(
            f"Cannot convert non-string value of type {type(match_string).__name__}",
            suggestion="Pass a string to convert()",
        )
    try:
        converter = _registry.get(name)
    except Exception as exc:
        raise StepError(
            f"Parameter type '{name}' is not registered",
            cause=exc,
            suggestion=(
                f"Use a registered type or register one with @parameter_type('{name}', pattern)"
            ),
        ) from exc
    try:
        return converter(match_string)
    except StepError:
        raise
    except Exception as exc:
        raise StepError(
            f"Cannot convert '{match_string}' using '{name}'",
            cause=exc,
            suggestion="Check the input matches the expected format",
        ) from exc


def _to_int(value: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise StepError(f"Cannot convert '{value}' to int", cause=exc) from exc


def _to_float(value: str) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise StepError(f"Cannot convert '{value}' to float", cause=exc) from exc


def _to_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise StepError(
            f"Cannot convert '{value}' to date (expected ISO format)", cause=exc
        ) from exc


def _to_datetime(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise StepError(
            f"Cannot convert '{value}' to datetime (expected ISO format)", cause=exc
        ) from exc


def _to_decimal(value: str) -> Decimal:
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise StepError(f"Cannot convert '{value}' to decimal", cause=exc) from exc


def _to_email(value: str) -> str:
    if not _EMAIL_PATTERN.match(value):
        raise StepError(f"'{value}' is not a valid email address")
    return value


def _to_url(value: str) -> str:
    if not _URL_PATTERN.match(value):
        raise StepError(f"'{value}' is not a valid URL")
    return value


_BUILTIN_TYPES: dict[str, Callable[[str], Any]] = {
    "int": _to_int,
    "float": _to_float,
    "date": _to_date,
    "datetime": _to_datetime,
    "decimal": _to_decimal,
    "email": _to_email,
    "url": _to_url,
}

_BUILTIN_PATTERNS: dict[str, str] = {
    "int": r"[-+]?\d+",
    "float": r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?",
    "date": r"\d{4}-\d{2}-\d{2}",
    "datetime": r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?",
    "decimal": r"[-+]?\d*\.?\d+",
    "email": r"[^@\s]+@[^@\s]+\.[^@\s]+",
    "url": r"https?://\S+",
}


def register_builtin_types() -> None:
    """Register every built-in converter. Safe to call more than once.

    Registered types are also usable as ``{param:name}`` in Behave step
    patterns (e.g. ``{email:email}``, ``{url:url}``).
    """
    registered = _registry.names()
    for name, func in _BUILTIN_TYPES.items():
        if name not in registered:
            _registry.register(name, func)
            _patterns[name] = _BUILTIN_PATTERNS[name]
            _register_with_behave(name, func, _BUILTIN_PATTERNS[name])
