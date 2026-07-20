"""Integration tests for behave_kit.hooks.teardown."""

from __future__ import annotations

from types import SimpleNamespace
from unittest import mock

import pytest

from behave_kit.hooks import _WIRED_KEY, setup, teardown


def test_teardown_without_setup_is_noop() -> None:
    context = SimpleNamespace()
    teardown(context)


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
    manager = context._behave_kit_fixtures
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
    manager = context._behave_kit_fixtures
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
    assert call_order == ["fixtures", "scoped", "soft", "dump"]
