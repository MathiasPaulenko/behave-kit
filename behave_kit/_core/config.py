"""Immutable, resolved configuration loaded from `behave.toml`.

`behave.toml` groups settings by environment under `[env.<name>]` sections.
An optional `[env.default]` section provides values shared by all
environments; per-environment sections override it. CLI `--set key=value`
overrides are applied last.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from behave_kit._core.errors import ConfigError


@dataclass(frozen=True)
class KitConfig:
    """Resolved, immutable configuration for a single environment."""

    env: str
    base_url: str = ""
    browser: str = ""
    timeouts: dict[str, int] = field(default_factory=dict)
    credentials: dict[str, str] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_toml(
        cls,
        path: Path,
        env: str,
        overrides: dict[str, str] | None = None,
    ) -> KitConfig:
        """Load ``path``, select the ``[env.<env>]`` profile and apply overrides.

        Raises:
            ConfigError: if the file cannot be parsed, or the profile is missing.
        """
        try:
            with path.open("rb") as f:
                data = tomllib.load(f)
        except FileNotFoundError as exc:
            raise ConfigError(
                f"Config file not found: {path}",
                cause=exc,
                suggestion=f"Create {path} or pass a different config_file path",
            ) from exc
        except tomllib.TOMLDecodeError as exc:
            raise ConfigError(
                f"Invalid TOML in {path}: {exc}",
                cause=exc,
                suggestion="Check the file for syntax errors",
            ) from exc

        environments = data.get("env", {})
        default_section = environments.get("default", {})
        profile = environments.get(env)
        if profile is None:
            raise ConfigError(
                f"Environment profile 'env.{env}' not found in {path}",
                suggestion=f"Available profiles: {', '.join(sorted(environments)) or '(none)'}",
            )

        resolved: dict[str, Any] = {**default_section, **profile}
        for key, value in (overrides or {}).items():
            resolved[key] = value

        return cls(
            env=env,
            base_url=str(resolved.get("base_url", "")),
            browser=str(resolved.get("browser", "")),
            timeouts=dict(resolved.get("timeouts", {})),
            credentials=dict(resolved.get("credentials", {})),
            raw=resolved,
        )
