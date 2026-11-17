"""`wait_until` — poll a condition until it becomes true or a timeout is reached.

Common in E2E and integration tests where a resource (API, database, browser)
is not immediately available after an action.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable

from behave_kit._core.boolutil import as_bool
from behave_kit._core.errors import BehaveKitError


def wait_until(
    condition: Callable[[], object],
    *,
    timeout: float = 10.0,
    interval: float = 0.5,
    message: str = "",
) -> None:
    """Poll ``condition`` until it is truthy or ``timeout`` seconds elapse.

    Args:
        condition: Zero-argument callable whose return value is evaluated
            with scalar-bool coercion (tolerates array-like objects).
        timeout: Maximum number of seconds to wait (default 10).
        interval: Seconds between polls (default 0.5).
        message: Custom message for the timeout error.

    Raises:
        TimeoutError: If ``condition`` does not become truthy within
            ``timeout`` seconds.
    """
    if not callable(condition):
        raise BehaveKitError(
            f"condition must be callable, got {type(condition).__name__}",
            suggestion="Pass a zero-argument callable, e.g. lambda: check()",
        )
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool):
        raise BehaveKitError(
            f"timeout must be a number, got {type(timeout).__name__}",
            suggestion="Use a positive float for timeout seconds",
        )
    if timeout < 0 or not math.isfinite(timeout):
        raise BehaveKitError(
            f"timeout must be a finite non-negative number, got {timeout}",
            suggestion="Use a positive float for timeout seconds",
        )
    if not isinstance(interval, (int, float)) or isinstance(interval, bool):
        raise BehaveKitError(
            f"interval must be a number, got {type(interval).__name__}",
            suggestion="Use a positive float for interval seconds",
        )
    if interval <= 0 or not math.isfinite(interval):
        raise BehaveKitError(
            f"interval must be a positive finite number, got {interval}",
            suggestion="Use a positive float for interval seconds",
        )

    deadline = time.monotonic() + timeout
    while True:
        if as_bool(condition()):
            return
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        time.sleep(min(interval, remaining))

    raise TimeoutError(
        message or f"wait_until() timed out after {timeout}s (polling every {interval}s)",
    )
