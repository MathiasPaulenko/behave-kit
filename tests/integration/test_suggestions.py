"""Integration tests for behave_kit.steps.suggestions."""

import logging
from types import SimpleNamespace

import pytest

from behave_kit.steps.suggestions import setup_suggestions, suggest_for_undefined


class _FakeMatcher:
    def __init__(self, pattern: str) -> None:
        self.pattern = pattern


@pytest.fixture(autouse=True)
def _sample_step_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    from behave.step_registry import registry as the_step_registry

    monkeypatch.setitem(the_step_registry.steps, "when", [_FakeMatcher("I click the {element}")])
    monkeypatch.setitem(the_step_registry.steps, "given", [])
    monkeypatch.setitem(the_step_registry.steps, "then", [])
    monkeypatch.setitem(the_step_registry.steps, "step", [])


def test_suggest_for_undefined_finds_close_match(caplog: pytest.LogCaptureFixture) -> None:
    step = SimpleNamespace(name="I click the buttonn")
    with caplog.at_level(logging.INFO, logger="behave_kit.steps.suggestions"):
        matches = suggest_for_undefined(step)
    assert matches
    assert "Did you mean" in caplog.text


def test_suggest_for_undefined_no_close_match() -> None:
    step = SimpleNamespace(name="a totally unrelated step text with nothing in common")
    matches = suggest_for_undefined(step)
    assert matches == []


def test_setup_suggestions_hook_logs_for_undefined_step(
    caplog: pytest.LogCaptureFixture,
) -> None:
    context = SimpleNamespace()
    hook = setup_suggestions(context)
    step = SimpleNamespace(name="I click the buttonn", status="undefined")
    with caplog.at_level(logging.INFO, logger="behave_kit.steps.suggestions"):
        hook(context, step)
    assert "Did you mean" in caplog.text


def test_setup_suggestions_hook_skips_defined_step(caplog: pytest.LogCaptureFixture) -> None:
    context = SimpleNamespace()
    hook = setup_suggestions(context)
    step = SimpleNamespace(name="I click the buttonn", status="passed")
    with caplog.at_level(logging.INFO, logger="behave_kit.steps.suggestions"):
        hook(context, step)
    assert "Did you mean" not in caplog.text
