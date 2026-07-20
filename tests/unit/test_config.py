"""Tests for behave_kit._core.config."""

from pathlib import Path

import pytest

from behave_kit._core.config import KitConfig
from behave_kit._core.errors import ConfigError

TOML_CONTENT = """
[env.default]
timeouts = { implicit = 5 }

[env.staging]
base_url = "https://staging.example.com"
browser = "chrome"
timeouts = { implicit = 10, explicit = 30 }
credentials = { user = "staging-user" }

[env.production]
base_url = "https://prod.example.com"
browser = "firefox"
"""


@pytest.fixture
def toml_path(tmp_path: Path) -> Path:
    path = tmp_path / "behave.toml"
    path.write_text(TOML_CONTENT, encoding="utf-8")
    return path


def test_from_toml_valid_profile(toml_path: Path) -> None:
    config = KitConfig.from_toml(toml_path, env="staging")
    assert config.env == "staging"
    assert config.base_url == "https://staging.example.com"
    assert config.browser == "chrome"
    assert config.timeouts == {"implicit": 10, "explicit": 30}
    assert config.credentials == {"user": "staging-user"}


def test_from_toml_missing_profile_raises(toml_path: Path) -> None:
    with pytest.raises(ConfigError):
        KitConfig.from_toml(toml_path, env="does-not-exist")


def test_from_toml_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        KitConfig.from_toml(tmp_path / "missing.toml", env="staging")


def test_from_toml_invalid_toml_raises(tmp_path: Path) -> None:
    path = tmp_path / "behave.toml"
    path.write_text("not = [valid toml", encoding="utf-8")
    with pytest.raises(ConfigError):
        KitConfig.from_toml(path, env="staging")


def test_from_toml_applies_overrides(toml_path: Path) -> None:
    config = KitConfig.from_toml(toml_path, env="staging", overrides={"browser": "firefox"})
    assert config.browser == "firefox"
    assert config.raw["browser"] == "firefox"


def test_config_is_immutable(toml_path: Path) -> None:
    config = KitConfig.from_toml(toml_path, env="production")
    with pytest.raises(AttributeError):
        config.browser = "edge"  # type: ignore[misc]
    with pytest.raises(TypeError):
        config.timeouts["implicit"] = 1  # type: ignore[index]


def test_from_toml_deep_merges_nested_tables(toml_path: Path) -> None:
    config = KitConfig.from_toml(toml_path, env="staging")
    assert config.timeouts == {"implicit": 10, "explicit": 30}


def test_from_toml_rejects_overriding_table_with_string(toml_path: Path) -> None:
    with pytest.raises(ConfigError, match="timeouts.*table"):
        KitConfig.from_toml(toml_path, env="staging", overrides={"timeouts": "10"})


def test_from_toml_rejects_directory_path(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="not found or is not a file|not a file"):
        KitConfig.from_toml(tmp_path, env="staging")
