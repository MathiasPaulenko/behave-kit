"""Integration tests for behave_kit.context.scoped."""

import contextlib
from types import SimpleNamespace

from behave_kit._core.types import Scope
from behave_kit.context.scoped import cleanup_scoped, scoped


def test_scoped_attribute_cleaned_after_scenario() -> None:
    context = SimpleNamespace()

    @scoped("driver")
    def step(context: SimpleNamespace) -> None:
        context.driver = "chrome"

    step(context)
    assert context.driver == "chrome"
    cleanup_scoped(context, scope=Scope.SCENARIO)
    assert not hasattr(context, "driver")


def test_feature_scope_persists_through_scenario_cleanup() -> None:
    context = SimpleNamespace()

    @scoped("database", scope=Scope.FEATURE)
    def step(context: SimpleNamespace) -> None:
        context.database = "postgres"

    step(context)
    cleanup_scoped(context, scope=Scope.SCENARIO)
    assert context.database == "postgres"
    cleanup_scoped(context, scope=Scope.FEATURE)
    assert not hasattr(context, "database")


def test_leak_prevention_between_scenarios() -> None:
    context = SimpleNamespace()

    @scoped("user")
    def step(context: SimpleNamespace) -> None:
        context.user = "alice"

    step(context)
    cleanup_scoped(context)
    assert not hasattr(context, "user")

    # Next scenario reuses the same context object, attribute should be gone.
    assert not hasattr(context, "user")


def test_multiple_scoped_attributes_all_cleaned() -> None:
    context = SimpleNamespace()

    @scoped("driver")
    def step_one(context: SimpleNamespace) -> None:
        context.driver = "chrome"

    @scoped("user")
    def step_two(context: SimpleNamespace) -> None:
        context.user = "alice"

    step_one(context)
    step_two(context)
    cleanup_scoped(context, scope=Scope.SCENARIO)
    assert not hasattr(context, "driver")
    assert not hasattr(context, "user")


def test_cleanup_scoped_is_safe_when_attribute_already_removed() -> None:
    context = SimpleNamespace()

    @scoped("driver")
    def step(context: SimpleNamespace) -> None:
        context.driver = "chrome"

    step(context)
    del context.driver
    cleanup_scoped(context, scope=Scope.SCENARIO)  # should not raise


def test_scoped_tracks_attribute_when_step_raises() -> None:
    context = SimpleNamespace()

    @scoped("driver")
    def step(context: SimpleNamespace) -> None:
        context.driver = "chrome"
        raise RuntimeError("boom")

    with contextlib.suppress(RuntimeError):
        step(context)
    assert context.driver == "chrome"
    cleanup_scoped(context, scope=Scope.SCENARIO)
    assert not hasattr(context, "driver")
