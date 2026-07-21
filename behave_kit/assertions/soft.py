"""Soft assertions: collect failures instead of stopping at the first one.

The active `SoftAssertCollector` is resolved through `contextvars` rather
than a module-level global, so it is thread-safe and naturally scoped per
scenario (Behave hooks reset it before/after each scenario).
"""

from __future__ import annotations

import contextlib
import contextvars
from collections.abc import Iterator

from behave_kit._core.boolutil import as_bool as _as_bool
from behave_kit._core.errors import BehaveKitError
from behave_kit._core.types import Context
from behave_kit.assertions.diff import _safe_equal
from behave_kit.assertions.reporter import SoftAssertReport, SoftFailure


class SoftAssertCollector:
    """Accumulates assertion failures without raising immediately."""

    def __init__(self) -> None:
        self._failures: list[SoftFailure] = []

    def assert_soft(self, condition: bool, msg: str = "") -> None:
        """Record a failure if ``condition`` is falsy.

        Args:
            condition: Boolean (or bool-coercible) value to check.
            msg: Optional message describing the failure.
        """
        if not _as_bool(condition):
            self._failures.append(SoftFailure(message=msg or "condition was false"))

    def assert_soft_equals(self, actual: object, expected: object, msg: str = "") -> None:
        """Record a failure if ``actual`` is not equal to ``expected``.

        Args:
            actual: The value produced by the code under test.
            expected: The value ``actual`` is expected to match.
            msg: Optional override message for the failure.
        """
        if not _safe_equal(actual, expected):
            self._failures.append(
                SoftFailure(message=msg or "values are not equal", expected=expected, actual=actual)
            )

    def assert_soft_true(self, condition: object, msg: str = "") -> None:
        """Record a failure if ``condition`` is not truthy.

        Args:
            condition: Value evaluated with scalar-bool coercion.
            msg: Optional override message for the failure.
        """
        self.assert_soft(_as_bool(condition), msg or "expected a truthy value")

    def assert_soft_is_none(self, value: object, msg: str = "") -> None:
        """Record a failure if ``value`` is not ``None``.

        Args:
            value: The value to check.
            msg: Optional override message for the failure.
        """
        if value is not None:
            self._failures.append(
                SoftFailure(message=msg or "expected None", expected=None, actual=value)
            )

    @property
    def failures(self) -> list[SoftFailure]:
        """Copy of the recorded soft assertion failures."""
        return list(self._failures)

    def report(self) -> SoftAssertReport:
        """Return an immutable report of all recorded failures."""
        return SoftAssertReport(failures=list(self._failures))

    def raise_if_failed(self) -> None:
        """Raise ``AssertionError`` if any failure has been recorded."""
        if self._failures:
            raise AssertionError(str(self.report()))

    def clear(self) -> None:
        """Remove every recorded failure."""
        self._failures.clear()


_collector_var: contextvars.ContextVar[SoftAssertCollector | None] = contextvars.ContextVar(
    "behave_kit_soft_collector"
)


def use_soft_asserts(context: Context) -> SoftAssertCollector:
    """Activate soft assertions for the given Behave ``context``.

    Attaches a fresh `SoftAssertCollector` to ``context._behave_kit_soft``
    and makes it the active collector for `assert_soft` and friends.
    """
    collector = SoftAssertCollector()
    context._behave_kit_soft = collector
    _collector_var.set(collector)
    return collector


def _active_collector() -> SoftAssertCollector:
    try:
        collector = _collector_var.get()
    except LookupError as exc:
        raise BehaveKitError(
            "assert_soft() called without soft asserts activated",
            suggestion="Use use_soft_asserts(context) or behave_kit.setup(context) first",
        ) from exc
    if collector is None:
        raise BehaveKitError(
            "assert_soft() called without soft asserts activated",
            suggestion="Use use_soft_asserts(context) or behave_kit.setup(context) first",
        )
    return collector


def assert_soft(condition: bool, msg: str = "") -> None:
    """Record a soft assertion failure if ``condition`` is falsy."""
    _active_collector().assert_soft(condition, msg)


def assert_soft_equals(actual: object, expected: object, msg: str = "") -> None:
    """Record a soft assertion failure if ``actual`` != ``expected``."""
    _active_collector().assert_soft_equals(actual, expected, msg)


def assert_soft_true(condition: object, msg: str = "") -> None:
    """Record a soft assertion failure if ``condition`` is not truthy."""
    _active_collector().assert_soft_true(condition, msg)


def assert_soft_is_none(value: object, msg: str = "") -> None:
    """Record a soft assertion failure if ``value`` is not None."""
    _active_collector().assert_soft_is_none(value, msg)


@contextlib.contextmanager
def soft_asserts() -> Iterator[SoftAssertCollector]:
    """Context manager for soft assertions outside of Behave (e.g. unit tests).

    Raises an `AssertionError` summarizing every failure when the block
    exits without an exception of its own.
    """
    collector = SoftAssertCollector()
    token = _collector_var.set(collector)
    try:
        yield collector
    finally:
        _collector_var.reset(token)
    collector.raise_if_failed()
