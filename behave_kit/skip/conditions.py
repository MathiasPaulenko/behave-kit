"""Reusable skip conditions, usable standalone or via `skip.decorators`."""

from __future__ import annotations

import importlib
import logging
import platform

from behave_kit._core.types import Context

logger = logging.getLogger("behave_kit.skip.conditions")


def is_env(context: Context, env_name: str) -> bool:
    """True if ``context.config.env == env_name``."""
    config = getattr(context, "config", None)
    return getattr(config, "env", None) == env_name


def is_os(os_name: str) -> bool:
    """True if the current OS matches ``os_name`` (case-insensitive)."""
    if not isinstance(os_name, str):
        logger.warning("is_os() expected a string, got %s", type(os_name).__name__)
        return False
    return platform.system().lower() == os_name.lower()


def is_missing(module_name: str) -> bool:
    """True if ``module_name`` cannot be imported.

    Invalid inputs (non-string or empty) are treated as missing to avoid
    executing arbitrary code.
    """
    if not isinstance(module_name, str) or not module_name:
        return True
    try:
        importlib.import_module(module_name)
    except Exception:
        return True
    return False


def is_no_browser() -> bool:
    """True if Selenium is not installed."""
    return is_missing("selenium")
