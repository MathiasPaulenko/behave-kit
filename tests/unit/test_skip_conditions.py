"""Tests for behave_kit.skip.conditions."""

import platform
from types import SimpleNamespace

from behave_kit.skip.conditions import is_env, is_missing, is_no_browser, is_os


def test_is_env_true_when_matching() -> None:
    context = SimpleNamespace(config=SimpleNamespace(env="ci"))
    assert is_env(context, "ci") is True


def test_is_env_false_when_not_matching() -> None:
    context = SimpleNamespace(config=SimpleNamespace(env="staging"))
    assert is_env(context, "ci") is False


def test_is_env_false_when_no_config() -> None:
    context = SimpleNamespace()
    assert is_env(context, "ci") is False


def test_is_os_matches_current_platform() -> None:
    current = platform.system()
    assert is_os(current) is True
    assert is_os(current.upper()) is True


def test_is_os_does_not_match_other_platform() -> None:
    assert is_os("not-a-real-os") is False


def test_is_missing_false_for_existing_module() -> None:
    assert is_missing("json") is False


def test_is_missing_true_for_nonexistent_module() -> None:
    assert is_missing("this_module_does_not_exist_anywhere") is True


def test_is_no_browser_reflects_selenium_availability() -> None:
    result = is_no_browser()
    assert isinstance(result, bool)


def test_is_os_with_invalid_input_returns_false() -> None:
    assert is_os(123) is False


def test_is_missing_with_invalid_input_returns_true() -> None:
    assert is_missing(123) is True
    assert is_missing("") is True
