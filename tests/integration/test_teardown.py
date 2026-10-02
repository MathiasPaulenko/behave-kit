"""Integration tests for behave_kit.hooks.teardown."""

from __future__ import annotations

from types import SimpleNamespace
from unittest import mock

import pytest

from behave_kit.hooks import _WIRED_KEY, setup, teardown


def test_teardown_without_setup_is_noop() -> None:
    context = SimpleNamespace()
    teardown(context)


def test_setup_validates_log_level() -> None:
    context = SimpleNamespace()
    with pytest.raises(Exception, match="Invalid log_level"):
        setup(context, log_level="not-a-level")


def test_teardown_only_wired_modules() -> None:
    context = SimpleNamespace()
    with mock.patch("behave_kit.hooks._wire_soft_asserts", side_effect=RuntimeError("boom")):
        setup(context)
    wired = getattr(context, _WIRED_KEY)
    assert "soft" not in wired

    with mock.patch("behave_kit.hooks._report_soft_asserts") as report_mock:
        teardown(context)
        report_mock.assert_not_called()


def test_teardown_calls_fixture_teardown() -> None:
    context = SimpleNamespace()
    setup(context)
    manager = context.kit_fixtures
    with mock.patch.object(manager, "teardown_scenario") as fixture_mock:
        teardown(context)
        fixture_mock.assert_called_once_with(context)


def test_teardown_calls_cleanup_scoped() -> None:
    context = SimpleNamespace()
    setup(context)
    with mock.patch("behave_kit.context.scoped.cleanup_scoped") as cleanup_mock:
        teardown(context)
        cleanup_mock.assert_called_once_with(context)


def test_teardown_calls_dump_if_failed() -> None:
    context = SimpleNamespace()
    setup(context)
    context.scenario = SimpleNamespace(status="passed")
    with mock.patch("behave_kit.hooks._dump_if_failed") as dump_mock:
        teardown(context)
        dump_mock.assert_called_once_with(context)


def test_teardown_does_not_call_dump_if_not_wired() -> None:
    context = SimpleNamespace()
    with mock.patch("behave_kit.hooks._wire_context_dump", side_effect=RuntimeError("boom")):
        setup(context)
    with mock.patch("behave_kit.hooks._dump_if_failed") as dump_mock:
        teardown(context)
        dump_mock.assert_not_called()


def test_teardown_soft_assert_report_on_failure() -> None:
    context = SimpleNamespace()
    setup(context)
    collector = context._behave_kit_soft
    collector.assert_soft(False, "intentional failure")
    with pytest.raises(AssertionError, match="intentional failure"):
        teardown(context)


def test_teardown_soft_assert_no_failure_no_raise() -> None:
    context = SimpleNamespace()
    setup(context)
    teardown(context)


def test_teardown_order_fixtures_before_scoped() -> None:
    context = SimpleNamespace()
    setup(context)
    call_order: list[str] = []
    manager = context.kit_fixtures
    with (
        mock.patch.object(
            manager,
            "teardown_scenario",
            side_effect=lambda ctx: call_order.append("fixtures"),
        ),
        mock.patch(
            "behave_kit.context.scoped.cleanup_scoped",
            side_effect=lambda ctx: call_order.append("scoped"),
        ),
        mock.patch(
            "behave_kit.hooks._report_soft_asserts",
            side_effect=lambda ctx: call_order.append("soft"),
        ),
        mock.patch(
            "behave_kit.hooks._dump_if_failed",
            side_effect=lambda ctx: call_order.append("dump"),
        ),
    ):
        teardown(context)
    assert call_order == ["fixtures", "scoped", "dump", "soft"]


# ---------------------------------------------------------------------------
# Teardown resilience and feature scope
# ---------------------------------------------------------------------------


def test_teardown_runs_all_steps_despite_intermediate_failure() -> None:
    """A TimeoutError mid-teardown must not skip later cleanup steps."""
    from behave.model import Scenario

    original = getattr(Scenario, "continue_after_failed_step", False)
    try:
        context = SimpleNamespace()
        setup(context, continue_after_failed=True)
        call_order: list[str] = []
        with (
            mock.patch(
                "behave_kit.hooks._teardown_timeout",
                side_effect=TimeoutError("timed out"),
            ),
            mock.patch(
                "behave_kit.context.scoped.cleanup_scoped",
                side_effect=lambda ctx: call_order.append("scoped"),
            ),
            mock.patch(
                "behave_kit.hooks._report_soft_asserts",
                side_effect=lambda ctx: call_order.append("soft"),
            ),
            pytest.raises(TimeoutError, match="timed out"),
        ):
            teardown(context)
        assert "scoped" in call_order
        assert "soft" in call_order
        assert Scenario.continue_after_failed_step is False
    finally:
        Scenario.continue_after_failed_step = original


def test_teardown_soft_failure_does_not_skip_continue_after_failed_reset() -> None:
    from behave.model import Scenario

    original = getattr(Scenario, "continue_after_failed_step", False)
    try:
        context = SimpleNamespace()
        setup(context, continue_after_failed=True)
        context._behave_kit_soft.assert_soft(False, "intentional failure")
        with pytest.raises(AssertionError):
            teardown(context)
        assert Scenario.continue_after_failed_step is False
    finally:
        Scenario.continue_after_failed_step = original


def test_teardown_feature_cleans_feature_scoped_attributes() -> None:
    from behave_kit._core.types import Scope
    from behave_kit.context.scoped import scoped
    from behave_kit.hooks import teardown_feature

    context = SimpleNamespace()

    @scoped("database", scope=Scope.FEATURE)
    def step(ctx: SimpleNamespace) -> None:
        ctx.database = "postgres"

    step(context)
    teardown_feature(context)
    assert not hasattr(context, "database")


def test_teardown_feature_runs_fixture_teardowns() -> None:
    from behave_kit._core.types import Scope
    from behave_kit.fixtures import fixture
    from behave_kit.hooks import teardown_feature

    calls: list[str] = []

    @fixture("teardown_feature_test", scope=Scope.FEATURE)
    def feat_fixture(context: SimpleNamespace) -> tuple:
        def setup_fn(ctx: SimpleNamespace) -> None:
            calls.append("setup")

        def teardown_fn(ctx: SimpleNamespace) -> None:
            calls.append("teardown")

        return setup_fn, teardown_fn

    context = SimpleNamespace()
    setup(context)
    feature = SimpleNamespace(tags=["teardown_feature_test"])
    context.kit_fixtures.setup_for_feature(context, feature)
    teardown_feature(context)
    assert calls == ["setup", "teardown"]
