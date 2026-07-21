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
"""

from __future__ import annotations

import logging

from behave_kit._core.errors import BehaveKitError
from behave_kit._core.logging import get_logger
from behave_kit._core.types import Context

logger = get_logger("hooks")

_WIRED_KEY = "_behave_kit_wired"
_FIXTURES_KEY = "_behave_kit_fixtures"
_SUGGESTIONS_KEY = "_behave_kit_suggestions"


def _validate_log_level(level: str) -> None:
    try:
        logging.getLogger().setLevel(level)
    except (TypeError, ValueError) as exc:
        raise BehaveKitError(
            f"Invalid log_level '{level}'",
            cause=exc,
            suggestion="Use a logging level name such as DEBUG, INFO, WARNING, ERROR, or CRITICAL",
        ) from exc


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

    hook = setup_suggestions(context)
    setattr(context, _SUGGESTIONS_KEY, hook)


def _wire_fixtures(context: Context) -> None:
    from behave_kit.fixtures import FixtureManager

    manager = FixtureManager()
    setattr(context, _FIXTURES_KEY, manager)


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
    logging.getLogger("behave_kit").setLevel(log_level)
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


def _teardown_fixtures(context: Context) -> None:
    manager = getattr(context, _FIXTURES_KEY, None)
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
    Safe to call without a prior ``setup()`` (no-op).
    """
    wired: set[str] = getattr(context, _WIRED_KEY, set())

    if "fixtures" in wired:
        _teardown_fixtures(context)
    _cleanup_scoped(context)
    if "dump" in wired:
        _dump_if_failed(context)
    if "soft" in wired:
        _report_soft_asserts(context)
    if "continue_after_failed" in wired:
        _reset_continue_after_failed(context)
