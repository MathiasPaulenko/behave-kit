"""Better error messages: suggest similar steps for undefined step names.

Does not wrap or modify Behave's step registry. Reads step patterns from
`behave.step_registry.registry` (a public module-level singleton) and
compares them against the undefined step's text with `difflib`.
"""

from __future__ import annotations

import difflib
from collections.abc import Callable

from behave.step_registry import registry as the_step_registry

from behave_kit._core.logging import get_logger
from behave_kit._core.types import Context

logger = get_logger("steps.suggestions")


def _known_step_patterns() -> list[str]:
    """Collect every registered step pattern from Behave's step registry."""
    patterns: list[str] = []
    for matchers in the_step_registry.steps.values():
        patterns.extend(matcher.pattern for matcher in matchers)
    return patterns


def suggest_for_undefined(step: object) -> list[str]:
    """Log the closest registered step pattern(s) for an undefined ``step``.

    Returns the list of close matches found (possibly empty).
    """
    step_name = str(getattr(step, "name", step))
    matches = difflib.get_close_matches(step_name, _known_step_patterns())
    if matches:
        logger.info("Step '%s' has not been defined. Did you mean: '%s'?", step_name, matches[0])
    return matches


def setup_suggestions(context: Context) -> Callable[[Context, object], None]:
    """Return an ``after_step(context, step)`` hook that logs suggestions.

    Wire it in ``environment.py``::

        _suggest = behave_kit.steps.setup_suggestions(context)

        def after_step(context, step):
            _suggest(context, step)
    """

    def after_step_hook(hook_context: Context, step: object) -> None:
        """Suggest similar steps when ``step`` is reported as undefined."""
        status = getattr(step, "status", None)
        status_name = str(getattr(status, "name", status)).lower()
        if status_name == "undefined":
            suggest_for_undefined(step)

    return after_step_hook
