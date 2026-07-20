"""Per-module logger helper.

Every behave-kit module gets a logger named `behave_kit.<module>`, so the
log level can be configured globally via `logging.getLogger("behave_kit")`.
"""

from __future__ import annotations

import logging


def get_logger(name: str) -> logging.Logger:
    """Return the logger for a behave-kit submodule.

    Args:
        name: Short module name, e.g. ``"assertions"`` or ``"fixtures"``.

    Returns:
        A logger named ``behave_kit.<name>``.
    """
    return logging.getLogger(f"behave_kit.{name}")
