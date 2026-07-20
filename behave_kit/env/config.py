"""Wiring: load `behave.toml` and attach the resolved config to the Behave context."""

from __future__ import annotations

from pathlib import Path

from behave_kit._core.config import KitConfig
from behave_kit._core.types import Context


def load_env_config(
    context: Context,
    env: str,
    config_file: str | Path = "behave.toml",
    *,
    overrides: dict[str, str] | None = None,
) -> KitConfig:
    """Load ``config_file``, resolve the ``env`` profile, and attach it to ``context.config``."""
    config = KitConfig.from_toml(Path(config_file), env=env, overrides=overrides)
    context.config = config
    return config
