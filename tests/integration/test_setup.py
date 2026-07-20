"""Integration tests for behave_kit.hooks.setup."""

from __future__ import annotations

import logging
from types import SimpleNamespace
from unittest import mock

from behave_kit.hooks import _WIRED_KEY, setup


def test_setup_wires_all_modules(tmp_path: object) -> None:
    config = tmp_path / "behave.toml"  # type: ignore[operator]
    config.write_text(
        '[env.default]\nbase_url = "https://example.com"\n\n[env.test]\nbase_url = "https://test.example.com"\n',
        encoding="utf-8",
    )
    context = SimpleNamespace()
    setup(context, env="test", config_file=str(config))
    wired = getattr(context, _WIRED_KEY)
    assert "env" in wired
    assert "soft" in wired
    assert "dump" in wired
    assert "suggestions" in wired
    assert "fixtures" in wired


def test_setup_without_env_skips_env_wiring() -> None:
    context = SimpleNamespace()
    setup(context)
    wired = getattr(context, _WIRED_KEY)
    assert "env" not in wired
    assert "soft" in wired
    assert "dump" in wired
    assert "suggestions" in wired
    assert "fixtures" in wired


def test_setup_idempotent() -> None:
    context = SimpleNamespace()
    setup(context)
    wired_first = getattr(context, _WIRED_KEY)
    setup(context)
    wired_second = getattr(context, _WIRED_KEY)
    assert wired_first is wired_second


def test_setup_partial_failure() -> None:
    context = SimpleNamespace()
    with mock.patch("behave_kit.hooks._wire_soft_asserts", side_effect=RuntimeError("boom")):
        setup(context)
    wired = getattr(context, _WIRED_KEY)
    assert "soft" not in wired
    assert "dump" in wired
    assert "suggestions" in wired
    assert "fixtures" in wired


def test_setup_context_wired_populated() -> None:
    context = SimpleNamespace()
    setup(context)
    wired = getattr(context, _WIRED_KEY)
    assert isinstance(wired, set)
    assert len(wired) > 0


def test_setup_sets_log_level() -> None:
    context = SimpleNamespace()
    setup(context, log_level="DEBUG")
    assert logging.getLogger("behave_kit").getEffectiveLevel() == logging.DEBUG
    logging.getLogger("behave_kit").setLevel("INFO")


def test_setup_attaches_fixture_manager() -> None:
    context = SimpleNamespace()
    setup(context)
    manager = getattr(context, "_behave_kit_fixtures", None)
    assert manager is not None


def test_setup_attaches_soft_collector() -> None:
    context = SimpleNamespace()
    setup(context)
    collector = getattr(context, "_behave_kit_soft", None)
    assert collector is not None


def test_setup_attaches_suggestions_hook() -> None:
    context = SimpleNamespace()
    setup(context)
    hook = getattr(context, "_behave_kit_suggestions", None)
    assert callable(hook)
