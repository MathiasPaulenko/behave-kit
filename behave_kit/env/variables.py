"""`env()` — read environment variables with validation and type conversion.

Falls back to the `KitConfig` attached to `context.config` (see
`behave_kit.env.config.load_env_config`) when the variable is not present
in `os.environ`. Loads a `.env` file once via `python-dotenv` if installed.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal, TypeVar, overload

from behave_kit._core.compat import HAS_DOTENV
from behave_kit._core.errors import EnvVarError
from behave_kit._core.types import Context

T = TypeVar("T")

_TRUE_VALUES = {"true", "1", "yes", "on"}
_FALSE_VALUES = {"false", "0", "no", "off"}

_dotenv_loaded = False


def _ensure_dotenv_loaded() -> None:
    global _dotenv_loaded
    if _dotenv_loaded:
        return
    _dotenv_loaded = True
    if not HAS_DOTENV:
        return
    from dotenv import load_dotenv

    load_dotenv(Path(".env"))


def _to_bool(raw: str) -> bool:
    normalized = raw.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise EnvVarError(
        f"Cannot convert '{raw}' to bool",
        suggestion=f"Use one of: {', '.join(sorted(_TRUE_VALUES | _FALSE_VALUES))}",
    )


def _to_int(raw: str) -> int:
    try:
        return int(raw)
    except ValueError as exc:
        raise EnvVarError(
            f"Cannot convert '{raw}' to int",
            cause=exc,
            suggestion="Provide an integer value",
        ) from exc


def _to_float(raw: str) -> float:
    try:
        return float(raw)
    except ValueError as exc:
        raise EnvVarError(
            f"Cannot convert '{raw}' to float",
            cause=exc,
            suggestion="Provide a numeric value",
        ) from exc


def _convert(raw: object, var_type: type) -> Any:
    if var_type is bool:
        if isinstance(raw, bool):
            return raw
        if isinstance(raw, (int, float)):
            return bool(raw)
        return _to_bool(str(raw))
    if var_type is int:
        if isinstance(raw, bool):
            raise EnvVarError(
                f"Cannot convert '{raw}' to int",
                suggestion="Provide an integer value",
            )
        if isinstance(raw, (int, float)):
            return int(raw)
        return _to_int(str(raw).strip())
    if var_type is float:
        if isinstance(raw, bool):
            raise EnvVarError(
                f"Cannot convert '{raw}' to float",
                suggestion="Provide a numeric value",
            )
        if isinstance(raw, (int, float)):
            return float(raw)
        return _to_float(str(raw).strip())
    if var_type is str:
        return str(raw)
    raise EnvVarError(
        f"Unsupported var_type '{var_type.__name__}'",
        suggestion="Use bool, int, float, or str",
    )


def _from_config(context: Context | None, key: str) -> object | None:
    if context is None:
        return None
    config = getattr(context, "config", None)
    if config is None:
        return None
    raw_config = getattr(config, "raw", None) or {}
    return raw_config.get(key)


@overload
def env(
    key: str,
    *,
    required: Literal[True] = True,
    var_type: type[T] = ...,
    default: Any = None,
    context: Context | None = None,
) -> T: ...


@overload
def env(
    key: str,
    *,
    required: Literal[False],
    var_type: type[T] = ...,
    default: Any = None,
    context: Context | None = None,
) -> T | None: ...


def env(
    key: str,
    *,
    required: bool = True,
    var_type: type = str,
    default: Any = None,
    context: Context | None = None,
) -> Any:
    """Read environment variable ``key``, converted to ``var_type``.

    Resolution order: ``os.environ`` -> ``context.config.raw`` (if
    ``context`` is given) -> ``default`` -> `EnvVarError` (if ``required``).
    """
    if not key:
        raise EnvVarError(
            "Environment variable key must not be empty",
            suggestion="Provide a non-empty key name",
        )

    _ensure_dotenv_loaded()
    raw: object | None = os.environ.get(key)
    if raw is None:
        raw = _from_config(context, key)
    if raw is None:
        if default is not None:
            return _convert(default, var_type)
        if required:
            raise EnvVarError(
                f"Environment variable '{key}' is not set",
                suggestion=f"Set it with: export {key}=...",
            )
        return None
    return _convert(raw, var_type)
