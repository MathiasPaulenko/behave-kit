"""`FixtureManager` — orchestrates setup/teardown by tags and scope.

Usage in ``environment.py``::

    from behave_kit.fixtures import FixtureManager

    fixtures = FixtureManager()

    def before_scenario(context, scenario):
        fixtures.setup_for_scenario(context, scenario)

    def after_scenario(context):
        fixtures.teardown_scenario(context)
"""

from __future__ import annotations

import difflib
import re

from behave_kit._core.errors import FixtureError
from behave_kit._core.logging import get_logger
from behave_kit._core.types import Context, Scope
from behave_kit.fixtures.registry import (
    FixtureTeardown,
    fixture_names,
    fixture_scope,
    get_fixture,
    resolve_fixture_order,
)

logger = get_logger("fixtures.manager")


class FixtureManager:
    """Orchestrates fixture setup/teardown lifecycle by scope."""

    def __init__(self) -> None:
        self._scenario_teardowns: list[tuple[str, FixtureTeardown]] = []
        self._feature_teardowns: list[tuple[str, FixtureTeardown]] = []

    @staticmethod
    def _get_tags(obj: object) -> set[str]:
        tags = getattr(obj, "tags", [])
        return {str(tag) for tag in tags}

    def _run_fixture(self, name: str, context: Context) -> None:
        factory = get_fixture(name)
        result = factory(context)
        if result is not None:
            setup_fn, teardown_fn = result
            setup_fn(context)
            scope = fixture_scope(name)
            if scope == Scope.SCENARIO:
                self._scenario_teardowns.append((name, teardown_fn))
            else:
                self._feature_teardowns.append((name, teardown_fn))

    def _setup_for_tags(self, context: Context, tags: set[str], scope: Scope) -> None:
        available = set(fixture_names())
        matched = tags & available
        executed: set[str] = set()
        for tag in sorted(matched):
            try:
                order = resolve_fixture_order(tag)
            except FixtureError as exc:
                match = re.search(r"'([^']+)'", exc.message)
                missing = match.group(1) if match else tag
                similar = difflib.get_close_matches(missing, fixture_names())
                suggestion = f"Did you mean: {', '.join(similar)}" if similar else exc.suggestion
                raise FixtureError(
                    f"Fixture '{missing}' not found",
                    suggestion=suggestion,
                ) from exc
            for dep_name in order:
                if dep_name not in executed:
                    self._run_fixture(dep_name, context)
                    executed.add(dep_name)

    def setup_for_scenario(self, context: Context, scenario: object) -> None:
        """Run scenario-scoped fixtures matching ``scenario`` tags."""
        tags = self._get_tags(scenario)
        self._setup_for_tags(context, tags, Scope.SCENARIO)

    def setup_for_feature(self, context: Context, feature: object) -> None:
        """Run feature-scoped fixtures matching ``feature`` tags."""
        tags = self._get_tags(feature)
        self._setup_for_tags(context, tags, Scope.FEATURE)

    def teardown_scenario(self, context: Context) -> None:
        """Run scenario-scoped teardowns in reverse order."""
        for name, teardown in reversed(self._scenario_teardowns):
            try:
                teardown(context)
            except Exception:
                logger.exception("Teardown error in fixture '%s'", name)
        self._scenario_teardowns.clear()

    def teardown_feature(self, context: Context) -> None:
        """Run feature-scoped teardowns in reverse order."""
        for name, teardown in reversed(self._feature_teardowns):
            try:
                teardown(context)
            except Exception:
                logger.exception("Teardown error in fixture '%s'", name)
        self._feature_teardowns.clear()
