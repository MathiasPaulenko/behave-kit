"""`env()` — read environment variables with validation and type conversion.

Falls back to the `KitConfig` attached to `context.config` (see
`behave_kit.env.config.load_env_config`) when the variable is not present
in `os.environ`. Loads a `.env` file once via `python-dotenv` if installed.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, overload

from behave_kit._core.compat import HAS_DOTENV
from behave_kit._core.errors import EnvVarError
from behave_kit._core.types import Context

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


def _convert(raw: str, var_type: type) -> Any:
    if var_type is bool:
        normalized = raw.strip().lower()
        if normalized in _TRUE_VALUES:
            return True
        if normalized in _FALSE_VALUES:
            return False
        raise EnvVarError(
            f"Cannot convert '{raw}' to bool",
            suggestion=f"Use one of: {', '.join(sorted(_TRUE_VALUES | _FALSE_VALUES))}",
        )
    if var_type is int:
        try:
            return int(raw)
        except ValueError as exc:
            raise EnvVarError(
                f"Cannot convert '{raw}' to int",
                cause=exc,
                suggestion="Provide an integer value",
            ) from exc
    return raw


def _from_config(context: Context | None, key: str) -> str | None:
    if context is None:
        return None
    config = getattr(context, "config", None)
    if config is None:
        return None
    raw_value = getattr(config, "raw", {}).get(key)
    return None if raw_value is None else str(raw_value)


@overload
def env(
    key: str,
    *,
    required: bool = True,
    var_type: type[bool],
    default: bool | None = None,
    context: Context | None = None,
) -> bool: ...


@overload
def env(
    key: str,
    *,
    required: bool = True,
    var_type: type[int],
    default: int | None = None,
    context: Context | None = None,
) -> int: ...


@overload
def env(
    key: str,
    *,
    required: bool = True,
    var_type: type[str] = str,
    default: str | None = None,
    context: Context | None = None,
) -> str: ...


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
    _ensure_dotenv_loaded()
    raw = os.environ.get(key)
    if raw is None:
        raw = _from_config(context, key)
    if raw is None:
        if default is not None:
            return default
        if required:
            raise EnvVarError(
                f"Environment variable '{key}' is not set",
                suggestion=f"Set it with: export {key}=...",
            )
        return None
    return _convert(raw, var_type)
