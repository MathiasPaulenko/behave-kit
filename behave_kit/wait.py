"""`wait_until` — poll a condition until it becomes true or a timeout is reached.

Common in E2E and integration tests where a resource (API, database, browser)
is not immediately available after an action.
"""

from __future__ import annotations

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
    if timeout < 0:
        raise BehaveKitError(
            f"timeout must be non-negative, got {timeout}",
            suggestion="Use a positive float for timeout seconds",
        )
    if interval <= 0:
        raise BehaveKitError(
            f"interval must be positive, got {interval}",
            suggestion="Use a positive float for interval seconds",
        )

    deadline = time.monotonic() + timeout
    while True:
        if as_bool(condition()):
            return
        if time.monotonic() >= deadline:
            break
        time.sleep(interval)

    raise TimeoutError(
        message
        or f"wait_until() timed out after {timeout}s "
        f"(polling every {interval}s)",
    )
