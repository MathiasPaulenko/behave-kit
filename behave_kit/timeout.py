"""Per-scenario timeout with tag-based overrides.

Behave provides a global ``--timeout`` flag but no way to set a different
timeout per scenario.  This module fills that gap:

1. ``setup_timeout`` configures a default timeout on the context.
2. Tags ``@timeout:N`` override the timeout per scenario or feature.
3. On expiry the scenario fails with ``TimeoutError``.

Platform notes
--------------
- **Unix** (Linux, macOS): uses ``signal.SIGALRM`` for immediate
  interruption of the main thread.
- **Windows**: ``signal.SIGALRM`` is unavailable, so a
  ``threading.Timer`` fallback is used.  This cannot interrupt
  CPU-bound code — the timeout is detected after the current step
  finishes.  I/O-bound code (``time.sleep``, socket reads, etc.) is
  interrupted promptly because the timer callback sets a flag that
  ``__exit__`` checks.

Usage in ``environment.py``::

    from behave_kit import setup_timeout
    from behave_kit.timeout import timeout_before_scenario, timeout_after_scenario

    def before_all(context):
        setup_timeout(context, default_timeout=30)

    def before_scenario(context, scenario):
        timeout_before_scenario(context, scenario)

    def after_scenario(context, scenario):
        timeout_after_scenario(context, scenario)
"""

from __future__ import annotations

import math
import signal
import sys
import threading
from types import TracebackType
from typing import TYPE_CHECKING, Protocol

from behave_kit._core.logging import get_logger
from behave_kit._core.types import Context

if TYPE_CHECKING:
    from behave.model_core import Scenario as BehaveScenario

logger = get_logger("timeout")

_DEFAULT_TAG = "timeout"
_TIMEOUT_HANDLER_KEY = "_behave_kit_timeout_handler"
_TIMEOUT_DEFAULT_KEY = "_behave_kit_timeout_default"
_TIMEOUT_TAG_KEY = "_behave_kit_timeout_tag"

_IS_WINDOWS = sys.platform == "win32"


# ---------------------------------------------------------------------------
# Handler protocols and implementations
# ---------------------------------------------------------------------------


class TimeoutHandler(Protocol):
    """Protocol for platform-specific timeout handlers."""

    timeout: float

    def __enter__(self) -> TimeoutHandler: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...


class SignalTimeoutHandler:
    """Unix timeout handler using ``signal.SIGALRM``.

    Interrupts the main thread immediately when the deadline is reached.
    Only works on the main thread of the main interpreter.
    """

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout
        self._old_handler: object = None
        self._entered: bool = False

    def __enter__(self) -> SignalTimeoutHandler:
        if self._entered:
            raise RuntimeError("SignalTimeoutHandler is not reentrant")
        self._entered = True
        if self.timeout <= 0:
            return self
        sigalrm: int = signal.SIGALRM  # type: ignore[attr-defined]
        self._old_handler = signal.signal(sigalrm, self._handle_timeout)
        setitimer = signal.setitimer  # type: ignore[attr-defined]
        itimer_real: int = signal.ITIMER_REAL  # type: ignore[attr-defined]
        setitimer(itimer_real, self.timeout)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if not self._entered:
            return
        self._entered = False
        if self.timeout <= 0:
            return
        setitimer = signal.setitimer  # type: ignore[attr-defined]
        itimer_real: int = signal.ITIMER_REAL  # type: ignore[attr-defined]
        setitimer(itimer_real, 0)
        sigalrm: int = signal.SIGALRM  # type: ignore[attr-defined]
        signal.signal(sigalrm, self._old_handler)  # type: ignore[arg-type]

    def _handle_timeout(self, signum: int, frame: object | None) -> None:
        raise TimeoutError(f"Scenario exceeded timeout of {self.timeout}s")


class ThreadTimeoutHandler:
    """Windows fallback timeout handler using ``threading.Timer``.

    Cannot interrupt CPU-bound code.  The timeout is detected in
    ``__exit__`` after the wrapped block finishes.  I/O-bound code
    that checks for interrupts (e.g. ``time.sleep``) may be interrupted
    sooner.
    """

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout
        self._timer: threading.Timer | None = None
        self._timed_out: bool = False
        self._entered: bool = False

    def __enter__(self) -> ThreadTimeoutHandler:
        if self._entered:
            raise RuntimeError("ThreadTimeoutHandler is not reentrant")
        self._entered = True
        if self.timeout <= 0:
            return self
        self._timer = threading.Timer(self.timeout, self._handle_timeout)
        self._timer.daemon = True
        self._timer.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if not self._entered:
            return
        self._entered = False
        if self.timeout <= 0:
            return
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        if self._timed_out and exc_type is None:
            raise TimeoutError(f"Scenario exceeded timeout of {self.timeout}s")

    def _handle_timeout(self) -> None:
        self._timed_out = True


def _select_handler(timeout: float) -> TimeoutHandler:
    """Return the appropriate handler for the current platform."""
    if _IS_WINDOWS:
        return ThreadTimeoutHandler(timeout)
    return SignalTimeoutHandler(timeout)


# ---------------------------------------------------------------------------
# Tag parsing
# ---------------------------------------------------------------------------


def _parse_timeout_value(tag: str, tag_name: str) -> float | None:
    """Extract the numeric value from a ``@tag_name:N`` tag.

    Returns ``None`` if the tag does not match or the value is invalid.
    """
    prefix = f"{tag_name}:"
    if not tag.startswith(prefix):
        return None
    raw = tag[len(prefix) :]
    try:
        value = float(raw)
    except ValueError:
        logger.warning("Invalid timeout tag '@%s' (value: '%s')", tag, raw)
        return None
    if value < 0:
        logger.warning("Negative timeout in tag '@%s', ignoring", tag)
        return None
    if not math.isfinite(value):
        logger.warning("Non-finite timeout in tag '@%s', ignoring", tag)
        return None
    return value


def _parse_timeout_tag(scenario: object, tag_name: str) -> float | None:
    """Search for ``@tag_name:N`` in scenario or feature tags.

    Precedence: scenario tags are checked first, then feature tags.
    Returns ``N`` in seconds, or ``None`` if no valid tag is found.
    """
    # Check scenario tags first (higher precedence)
    scenario_tags = getattr(scenario, "tags", None) or []
    for tag in scenario_tags:
        value = _parse_timeout_value(str(tag), tag_name)
        if value is not None:
            return value

    # Fall back to feature tags
    feature = getattr(scenario, "feature", None)
    if feature is not None:
        feature_tags = getattr(feature, "tags", None) or []
        for tag in feature_tags:
            value = _parse_timeout_value(str(tag), tag_name)
            if value is not None:
                return value

    return None


# ---------------------------------------------------------------------------
# Hook integration
# ---------------------------------------------------------------------------


def timeout_before_scenario(context: Context, scenario: BehaveScenario) -> None:
    """Start the timeout timer for ``scenario``.

    Call this from ``before_scenario``.  If no timeout is configured
    (default is 0 and no ``@timeout:N`` tag is present), this is a no-op.
    """
    # Clear any stale handler from a previous scenario
    setattr(context, _TIMEOUT_HANDLER_KEY, None)

    default = getattr(context, _TIMEOUT_DEFAULT_KEY, 0)
    tag_name = getattr(context, _TIMEOUT_TAG_KEY, _DEFAULT_TAG)

    timeout = _parse_timeout_tag(scenario, tag_name)
    if timeout is None:
        timeout = default

    if timeout > 0:
        handler = _select_handler(timeout)
        handler.__enter__()
        setattr(context, _TIMEOUT_HANDLER_KEY, handler)
        logger.debug("Scenario timeout set to %.1fs", timeout)


def timeout_after_scenario(context: Context, scenario: BehaveScenario) -> None:
    """Cancel the timeout timer for ``scenario``.

    Call this from ``after_scenario``.  Raises ``TimeoutError`` if the
    scenario exceeded its timeout (Windows fallback only; on Unix the
    error is raised immediately during step execution).

    If the scenario already failed with an exception, that exception
    is passed to the handler so it doesn't mask the original failure.
    """
    handler = getattr(context, _TIMEOUT_HANDLER_KEY, None)
    if handler is None:
        return
    # Pass the scenario's existing exception (if any) to the handler
    # so it doesn't mask the original failure with a TimeoutError.
    exc_info = getattr(scenario, "exception", None)
    exc_type: type[BaseException] | None = None
    exc_val: BaseException | None = None
    if exc_info is not None and isinstance(exc_info, BaseException):
        exc_val = exc_info
        exc_type = type(exc_val)
    try:
        handler.__exit__(exc_type, exc_val, None)
    finally:
        setattr(context, _TIMEOUT_HANDLER_KEY, None)


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------


def setup_timeout(
    context: Context,
    default_timeout: float = 0,
    *,
    timeout_tag: str = _DEFAULT_TAG,
) -> None:
    """Configure per-scenario timeout.

    Args:
        context: The Behave context object.
        default_timeout: Timeout in seconds for all scenarios.
            ``0`` disables the per-scenario timeout (Behave's native
            ``--timeout`` still applies independently).
        timeout_tag: Name of the tag used for per-scenario overrides.
            The format is ``@<timeout_tag>:N`` where ``N`` is seconds.
            Default: ``"timeout"`` (i.e. ``@timeout:10``).
    """
    if default_timeout < 0:
        raise ValueError(f"default_timeout must be non-negative, got {default_timeout}")
    if not math.isfinite(default_timeout):
        raise ValueError(f"default_timeout must be finite, got {default_timeout}")
    if not timeout_tag or not isinstance(timeout_tag, str):
        raise ValueError(f"timeout_tag must be a non-empty string, got {timeout_tag!r}")

    setattr(context, _TIMEOUT_DEFAULT_KEY, default_timeout)
    setattr(context, _TIMEOUT_TAG_KEY, timeout_tag)
