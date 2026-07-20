"""Reusable skip conditions, usable standalone or via `skip.decorators`."""

from __future__ import annotations

import importlib
import platform

from behave_kit._core.types import Context


def is_env(context: Context, env_name: str) -> bool:
    """True if ``context.config.env == env_name``."""
    config = getattr(context, "config", None)
    return getattr(config, "env", None) == env_name


def is_os(os_name: str) -> bool:
    """True if the current OS matches ``os_name`` (case-insensitive)."""
    return platform.system().lower() == os_name.lower()


def is_missing(module_name: str) -> bool:
    """True if ``module_name`` cannot be imported."""
    try:
        importlib.import_module(module_name)
    except ImportError:
        return True
    return False


def is_no_browser() -> bool:
    """True if Selenium is not installed."""
    return is_missing("selenium")
