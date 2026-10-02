"""Wiring layer: connect all behave-kit modules to a Behave context.

``setup()`` is idempotent and fault-tolerant — if one module fails to wire,
the others still work.  ``teardown()`` only cleans up what was successfully
wired, in reverse order.

Usage in ``environment.py``::

    from behave_kit import setup, teardown

    def before_all(context):
        setup(context, env="staging")

    def after_scenario(context, scenario):
        teardown(context)

    def after_feature(context, feature):
        teardown_feature(context)
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

from behave_kit._core.errors import BehaveKitError
from behave_kit._core.logging import get_logger
from behave_kit._core.types import Context, Scope

if TYPE_CHECKING:
    from behave_kit.fixtures import FixtureManager

logger = get_logger("hooks")

_WIRED_KEY = "_behave_kit_wired"
_FIXTURES_KEY = "_behave_kit_fixtures"


def _get_timeout_key() -> str:
    from behave_kit.timeout import _TIMEOUT_HANDLER_KEY

    return _TIMEOUT_HANDLER_KEY


def _validate_log_level(level: str) -> None:
    """Validate ``level`` without mutating any logger as a side effect."""
    if isinstance(level, str) and level.upper() in logging.getLevelNamesMapping():
        return
    raise BehaveKitError(
        f"Invalid log_level '{level}'",
        suggestion="Use a logging level name such as DEBUG, INFO, WARNING, ERROR, or CRITICAL",
    )


def _wire_env_config(context: Context, env: str, config_file: str) -> None:
    from behave_kit.env.config import load_env_config

    load_env_config(context, env, config_file)


def _wire_soft_asserts(context: Context) -> None:
    from behave_kit.assertions.soft import use_soft_asserts

    use_soft_asserts(context)


def _wire_context_dump(context: Context) -> None:
    from behave_kit.context.dump import dump_context_on_failure  # noqa: F401


def _wire_suggestions(context: Context) -> None:
    from behave_kit.steps.suggestions import setup_suggestions

    context.kit_suggestions = setup_suggestions(context)


def _get_fixture_manager(context: Context) -> FixtureManager | None:
    """Return the wired `FixtureManager`, checking the public name first."""
    manager = getattr(context, "kit_fixtures", None)
    if manager is None:
        manager = getattr(context, _FIXTURES_KEY, None)
    return manager


def _wire_fixtures(context: Context) -> None:
    from behave_kit.fixtures import FixtureManager

    context.kit_fixtures = FixtureManager()


def _teardown_timeout(context: Context) -> None:
    from behave_kit.timeout import timeout_after_scenario

    handler = getattr(context, _get_timeout_key(), None)
    if handler is not None:
        scenario = getattr(context, "scenario", None)
        if scenario is not None:
            timeout_after_scenario(context, scenario)


def setup(
    context: Context,
    *,
    env: str | None = None,
    config_file: str = "behave.toml",
    log_level: str = "INFO",
    continue_after_failed: bool | None = None,
) -> None:
    """Wire all behave-kit modules into ``context``.

    Idempotent: calling twice is a no-op.  Each module is wired independently
    in try/except — a failure in one does not prevent the others.

    Wired state is exposed under public attributes — ``context.kit_config``
    (resolved `KitConfig`, when ``env`` is given), ``context.kit_fixtures``
    (the `FixtureManager`) and ``context.kit_suggestions`` (an
    ``after_step`` hook for undefined-step hints) — leaving Behave's own
    ``context.config`` untouched.

    Args:
        context: The Behave context object.
        env: Optional environment name for profile-based configuration.
        config_file: Path to the configuration file (default ``behave.toml``).
        log_level: Logging level for the ``behave_kit`` logger.
        continue_after_failed: When ``True``, scenarios continue executing
            remaining steps after a failure.  When ``False``, the default
            Behave behaviour (stop on first failure) is restored.  ``None``
            leaves the current setting unchanged.
    """
    _validate_log_level(log_level)
    logging.getLogger("behave_kit").setLevel(log_level.upper())
    if hasattr(context, _WIRED_KEY):
        return

    wired: set[str] = set()

    if continue_after_failed is not None:
        try:
            from behave_kit.continue_after_failed import continue_after_failed as _caf

            _caf(continue_after_failed)
            wired.add("continue_after_failed")
        except Exception:
            logger.warning("Failed to set continue_after_failed", exc_info=True)

    if env is not None:
        try:
            _wire_env_config(context, env, config_file)
            wired.add("env")
        except Exception:
            logger.warning("Failed to wire env config", exc_info=True)

    try:
        _wire_soft_asserts(context)
        wired.add("soft")
    except Exception:
        logger.warning("Failed to wire soft asserts", exc_info=True)

    try:
        _wire_context_dump(context)
        wired.add("dump")
    except Exception:
        logger.warning("Failed to wire context dump", exc_info=True)

    try:
        _wire_suggestions(context)
        wired.add("suggestions")
    except Exception:
        logger.warning("Failed to wire suggestions", exc_info=True)

    try:
        _wire_fixtures(context)
        wired.add("fixtures")
    except Exception:
        logger.warning("Failed to wire fixtures", exc_info=True)

    setattr(context, _WIRED_KEY, wired)


def teardown_timeout(context: Context) -> None:
    """Cancel any active per-scenario timeout.

    Safe to call without a prior ``setup_timeout`` (no-op).
    """
    _teardown_timeout(context)


def _teardown_fixtures(context: Context) -> None:
    manager = _get_fixture_manager(context)
    if manager is not None:
        manager.teardown_scenario(context)


def _cleanup_scoped(context: Context) -> None:
    from behave_kit.context.scoped import cleanup_scoped

    cleanup_scoped(context)


def _report_soft_asserts(context: Context) -> None:
    from behave_kit.assertions.soft import use_soft_asserts

    collector = getattr(context, "_behave_kit_soft", None)
    if collector is not None:
        report = collector.report()
        if report.has_failures:
            logger.error("Soft assertion failures:\n%s", report)
        try:
            collector.raise_if_failed()
        finally:
            use_soft_asserts(context)


def _dump_if_failed(context: Context) -> None:
    from behave_kit.context.dump import dump_context_on_failure

    scenario = getattr(context, "scenario", None)
    if scenario is not None:
        dump_context_on_failure(context, scenario)


def _reset_continue_after_failed(context: Context) -> None:
    from behave_kit.continue_after_failed import continue_after_failed as _caf

    _caf(False)


def teardown(context: Context) -> None:
    """Clean up wired modules in reverse order.

    Only modules that were successfully wired during ``setup()`` are torn down.
    Safe to call without a prior ``setup()`` (no-op).  Also tears down any
    class-based step instances created during the scenario, even if
    ``setup()`` was not called.

    Fault-tolerant: every teardown step runs even if an earlier one fails —
    a failing step never prevents the rest of the cleanup.  The first error
    raised is re-raised once all steps have run.
    """
    wired: set[str] = getattr(context, _WIRED_KEY, set())
    first_error: BaseException | None = None

    def _run(step: Callable[[Context], None]) -> None:
        nonlocal first_error
        try:
            step(context)
        except Exception as exc:
            if first_error is None:
                first_error = exc
            else:
                logger.exception("Error during teardown step %s", step.__name__)

    if "fixtures" in wired:
        _run(_teardown_fixtures)
    _run(_teardown_timeout)
    _run(_cleanup_scoped)
    # Class-based step instances are torn down regardless of wiring,
    # since they may be used with cherry-picked imports only.
    _run(_teardown_step_instances)
    if "dump" in wired:
        _run(_dump_if_failed)
    if "soft" in wired:
        _run(_report_soft_asserts)
    if "continue_after_failed" in wired:
        _run(_reset_continue_after_failed)

    if first_error is not None:
        raise first_error


def teardown_feature(context: Context) -> None:
    """Clean up feature-scoped state.  Call from ``after_feature``.

    Runs FEATURE-scoped fixture teardowns and removes attributes tracked
    with ``@scoped(..., scope=Scope.FEATURE)``.  Safe to call without a
    prior ``setup()`` (no-op for whatever is not present).
    """
    from behave_kit.context.scoped import cleanup_scoped

    manager = _get_fixture_manager(context)
    if manager is not None:
        manager.teardown_feature(context)
    cleanup_scoped(context, Scope.FEATURE)


def _teardown_step_instances(context: Context) -> None:
    """Tear down class-based step instances for ``context`` (no-op if none)."""
    from behave_kit.steps.classes import teardown_steps

    teardown_steps(context)
