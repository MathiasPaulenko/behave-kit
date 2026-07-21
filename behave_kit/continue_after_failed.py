"""Continue executing remaining steps after a step fails.

By default, Behave stops a scenario at the first failing step.  This module
provides utilities to change that behaviour globally or temporarily.

Usage in ``environment.py``::

    from behave_kit import continue_after_failed

    def before_all(context):
        continue_after_failed(True)

Or as a context manager for temporary activation::

    from behave_kit import continue_on_failure

    def before_scenario(context, scenario):
        if "smoke" in scenario.tags:
            context._caf_cm = continue_on_failure()
            context._caf_cm.__enter__()

    def after_scenario(context, scenario):
        cm = getattr(context, "_caf_cm", None)
        if cm is not None:
            cm.__exit__(None, None, None)
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from behave_kit._core.errors import BehaveKitError
from behave_kit._core.logging import get_logger

logger = get_logger("continue_after_failed")


def continue_after_failed(enabled: bool = True) -> None:
    """Set whether scenarios continue executing after a failed step.

    Sets the class-level attribute ``Scenario.continue_after_failed_step``
    which Behave checks before aborting a scenario on step failure.

    Args:
        enabled: When ``True``, scenarios keep running remaining steps
            even after a step fails.  When ``False``, execution stops
            at the first failing step (Behave's default).

    Raises:
        BehaveKitError: If ``enabled`` is not a boolean.
    """
    if not isinstance(enabled, bool):
        raise BehaveKitError(
            f"enabled must be a bool, got {type(enabled).__name__}",
            suggestion="Pass True or False explicitly",
        )
    from behave.model import Scenario

    Scenario.continue_after_failed_step = enabled
    logger.debug("continue_after_failed_step set to %s", enabled)


@contextmanager
def continue_on_failure() -> Iterator[None]:
    """Temporarily enable continue-after-failed for the current block.

    Sets ``Scenario.continue_after_failed_step`` to ``True`` on entry and
    restores the previous value on exit, even if an exception occurs.

    Usage::

        with continue_on_failure():
            # any scenario that runs while inside this block
            # will continue after failed steps
            ...
    """
    from behave.model import Scenario

    previous: bool = getattr(Scenario, "continue_after_failed_step", False)
    Scenario.continue_after_failed_step = True
    try:
        yield
    finally:
        Scenario.continue_after_failed_step = previous
