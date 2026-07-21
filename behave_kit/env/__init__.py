"""Environment management: `behave.toml` profiles and typed `env()` reads."""

from __future__ import annotations

from behave_kit._core.config import KitConfig
from behave_kit.env.config import load_env_config
from behave_kit.env.snapshot import env_snapshot
from behave_kit.env.variables import env

__all__ = [
    "KitConfig",
    "load_env_config",
    "env",
    "env_snapshot",
]
