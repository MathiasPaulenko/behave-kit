"""Tests for behave_kit.env.profiles."""

import pytest

from behave_kit._core.errors import ConfigError
from behave_kit.env.profiles import apply_overrides, select_profile

TOML_DATA = {
    "env": {
        "default": {"timeout": 5},
        "staging": {"base_url": "https://staging.example.com", "browser": "chrome"},
        "production": {"base_url": "https://prod.example.com"},
    }
}


def test_select_profile_returns_matching_section() -> None:
    profile = select_profile(TOML_DATA, "staging")
    assert profile["base_url"] == "https://staging.example.com"
    assert profile["browser"] == "chrome"


def test_select_profile_merges_with_default() -> None:
    profile = select_profile(TOML_DATA, "staging")
    assert profile["timeout"] == 5


def test_select_profile_missing_raises() -> None:
    with pytest.raises(ConfigError):
        select_profile(TOML_DATA, "does-not-exist")


def test_apply_overrides_adds_and_replaces_keys() -> None:
    base = {"browser": "chrome", "timeout": 5}
    result = apply_overrides(base, {"browser": "firefox", "headless": "true"})
    assert result == {"browser": "firefox", "timeout": 5, "headless": "true"}


def test_apply_overrides_does_not_mutate_input() -> None:
    base = {"browser": "chrome"}
    apply_overrides(base, {"browser": "firefox"})
    assert base == {"browser": "chrome"}


def test_select_profile_deep_merges_nested_tables() -> None:
    data = {
        "env": {
            "default": {"timeouts": {"implicit": 5}},
            "staging": {"timeouts": {"explicit": 30}},
        }
    }
    profile = select_profile(data, "staging")
    assert profile["timeouts"] == {"implicit": 5, "explicit": 30}


def test_select_profile_rejects_non_mapping_env() -> None:
    with pytest.raises(ConfigError, match="env.*table"):
        select_profile({"env": "not-a-table"}, "staging")
