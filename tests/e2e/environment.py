"""E2E environment.py — wires behave-kit features for dogfooding tests."""

from __future__ import annotations

from behave_kit.assertions.soft import use_soft_asserts
from behave_kit.fixtures import FixtureManager
from behave_kit.steps.classes import teardown_steps
from behave_kit.timeout import setup_timeout, timeout_after_scenario, timeout_before_scenario


def before_all(context: object) -> None:
    # Wire soft asserts at the global level
    use_soft_asserts(context)
    # Wire fixtures manager
    context._behave_kit_fixtures = FixtureManager()
    # Set env on the existing config so skip_if_env can read it
    config = getattr(context, "config", None)
    if config is not None:
        config.env = "test"
    # Configure default timeout for all scenarios (2 seconds)
    setup_timeout(context, default_timeout=2)
    # Mark as wired
    context._behave_kit_wired = {"soft", "fixtures"}


def before_scenario(context: object, scenario: object) -> None:
    # Fresh soft assert collector per scenario
    use_soft_asserts(context)
    # Reset continue_after_failed_step to default before each scenario
    from behave.model import Scenario

    Scenario.continue_after_failed_step = False
    # Start per-scenario timeout (no-op if setup_timeout wasn't called)
    timeout_before_scenario(context, scenario)


def after_scenario(context: object, scenario: object) -> None:
    # Cancel per-scenario timeout (raises TimeoutError on Windows fallback)
    timeout_after_scenario(context, scenario)
    # Clear soft assert failures so they don't leak
    collector = getattr(context, "_behave_kit_soft", None)
    if collector is not None:
        collector.clear()
    # Tear down class-based step instances (calls teardown() on each)
    teardown_steps(context)
    # Tear down fixtures
    manager = getattr(context, "_behave_kit_fixtures", None)
    if manager is not None:
        manager.teardown_scenario(context)
    # Reset continue_after_failed_step after each scenario
    from behave.model import Scenario

    Scenario.continue_after_failed_step = False
