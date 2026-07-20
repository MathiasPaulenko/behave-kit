"""Integration tests for behave_kit.env.config and .env loading via env()."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from behave_kit._core.config import KitConfig
from behave_kit.env.config import load_env_config
from behave_kit.env.variables import env

TOML_CONTENT = """
[env.staging]
base_url = "https://staging.example.com"
browser = "chrome"
"""


@pytest.fixture
def toml_path(tmp_path: Path) -> Path:
    path = tmp_path / "behave.toml"
    path.write_text(TOML_CONTENT, encoding="utf-8")
    return path


def test_load_env_config_attaches_kit_config(toml_path: Path) -> None:
    context = SimpleNamespace()
    config = load_env_config(context, env="staging", config_file=toml_path)
    assert isinstance(config, KitConfig)
    assert context.config is config
    assert context.config.base_url == "https://staging.example.com"


def test_load_env_config_applies_overrides(toml_path: Path) -> None:
    context = SimpleNamespace()
    load_env_config(context, env="staging", config_file=toml_path, overrides={"browser": "firefox"})
    assert context.config.browser == "firefox"


def test_env_falls_back_to_context_config(toml_path: Path) -> None:
    context = SimpleNamespace()
    load_env_config(context, env="staging", config_file=toml_path)
    assert env("base_url", context=context) == "https://staging.example.com"


def test_env_prefers_os_environ_over_context(
    toml_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    context = SimpleNamespace()
    load_env_config(context, env="staging", config_file=toml_path)
    monkeypatch.setenv("browser", "edge")
    assert env("browser", context=context) == "edge"
    monkeypatch.delenv("browser", raising=False)


def test_dotenv_loading_is_a_noop_without_python_dotenv(monkeypatch: pytest.MonkeyPatch) -> None:
    from behave_kit.env import variables as variables_module

    monkeypatch.setattr(variables_module, "HAS_DOTENV", False)
    monkeypatch.setattr(variables_module, "_dotenv_loaded", False)
    variables_module._ensure_dotenv_loaded()
    assert variables_module._dotenv_loaded is True
