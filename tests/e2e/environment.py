"""E2E environment.py — wires behave-kit features for dogfooding tests."""

from __future__ import annotations

from behave_kit.assertions.soft import use_soft_asserts
from behave_kit.fixtures import FixtureManager


def before_all(context: object) -> None:
    # Wire soft asserts at the global level
    use_soft_asserts(context)
    # Wire fixtures manager
    context._behave_kit_fixtures = FixtureManager()
    # Set env on the existing config so skip_if_env can read it
    config = getattr(context, "config", None)
    if config is not None:
        config.env = "test"
    # Mark as wired
    context._behave_kit_wired = {"soft", "fixtures"}


def before_scenario(context: object, scenario: object) -> None:
    # Fresh soft assert collector per scenario
    use_soft_asserts(context)


def after_scenario(context: object, scenario: object) -> None:
    # Clear soft assert failures so they don't leak
    collector = getattr(context, "_behave_kit_soft", None)
    if collector is not None:
        collector._failures.clear()  # noqa: SLF001
    # Tear down fixtures
    manager = getattr(context, "_behave_kit_fixtures", None)
    if manager is not None:
        manager.teardown_scenario(context)
