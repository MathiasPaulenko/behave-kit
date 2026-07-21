"""Execute Gherkin sub-steps with state isolation and outline substitution.

``run_steps`` wraps Behave's ``context.execute_steps()`` with two
enhancements that make sub-step execution safer and more expressive:

1. **Scenario Outline substitution** — ``<placeholder>`` variables from
   the current outline row are replaced before parsing, so sub-steps
   can reference the same parameters as the parent step.

2. **Table / text preservation** — ``context.table`` and ``context.text``
   are saved before execution and restored in a ``finally`` block, so the
   parent step's tabular or multiline data is never clobbered by a sub-step.

Usage::

    from behave_kit import run_steps

    @when("I complete the checkout flow")
    def step_impl(context):
        run_steps(context, '''
            Given I have items in my cart
            When I enter shipping info for "<city>"
            And I select payment method "<method>"
            Then I should see the order confirmation
        ''')
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import cast

from behave_kit._core.errors import SubStepError
from behave_kit._core.logging import get_logger
from behave_kit._core.types import Context

logger = get_logger("context.substeps")

_OUTLINE_PATTERN = re.compile(r"<([^>]+)>")


def _substitute_outline_vars(context: Context, steps_text: str) -> str:
    """Replace ``<placeholder>`` variables from ``context.active_outline``.

    If the context has no ``active_outline`` attribute (i.e. the scenario
    is not a Scenario Outline row), or the outline is empty, the text is
    returned unchanged.

    Raises:
        SubStepError: If ``active_outline`` is present but not a dict, or
            if a ``<placeholder>`` is not found in the outline.
    """
    active_outline = getattr(context, "active_outline", None)
    if not active_outline:
        return steps_text

    if not isinstance(active_outline, dict):
        raise SubStepError(
            f"active_outline must be a dict, got {type(active_outline).__name__}",
            suggestion="Ensure context.active_outline is set from a Scenario Outline row",
        )

    def _replace(match: re.Match[str]) -> str:
        var_name = match.group(1)
        if var_name not in active_outline:
            raise SubStepError(
                f"Outline variable '<{var_name}>' not found in active outline",
                suggestion=(
                    f"Available variables: {', '.join(sorted(active_outline.keys())) or '(none)'}"
                ),
            )
        return str(active_outline[var_name])

    return _OUTLINE_PATTERN.sub(_replace, steps_text)


def run_steps(context: Context, steps: str) -> None:
    """Execute Gherkin sub-steps with state isolation.

    Wraps ``context.execute_steps()`` with:

    - Scenario Outline ``<placeholder>`` substitution from ``context.active_outline``.
    - Guaranteed restoration of ``context.table`` and ``context.text``.

    Args:
        context: The Behave context for the current scenario.
        steps: Gherkin step text to execute. Must be a string containing
            one or more step definitions with keywords (Given/When/Then/And/But).

    Raises:
        SubStepError: If called outside a feature context.
        AssertionError: If any sub-step fails (propagated from Behave).
    """
    if not isinstance(steps, str):
        raise SubStepError(
            f"steps must be a string, got {type(steps).__name__}",
            suggestion="Pass a Gherkin string with Given/When/Then keywords",
        )

    if not steps.strip():
        raise SubStepError(
            "steps must not be empty or whitespace-only",
            suggestion="Provide at least one step with a Given/When/Then keyword",
        )

    if not getattr(context, "feature", None):
        raise SubStepError(
            "run_steps() called outside of a feature context",
            suggestion="Use run_steps() only from within a step definition",
        )

    if not callable(getattr(context, "execute_steps", None)):
        raise SubStepError(
            "context does not have a callable execute_steps method",
            suggestion="Ensure run_steps() is called with a valid Behave context",
        )

    original_table = getattr(context, "table", None)
    original_text = getattr(context, "text", None)

    resolved_steps = _substitute_outline_vars(context, steps)

    execute_steps = cast("Callable[[str], object]", context.execute_steps)
    try:
        execute_steps(resolved_steps)
    finally:
        context.table = original_table
        context.text = original_text
