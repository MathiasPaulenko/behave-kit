"""Project-wide configuration object loaded from ``behave.toml``.

`KitConfig` exposes the subset of fields behave-kit cares about, while
``raw`` preserves the full merged profile for custom tooling.
"""

from __future__ import annotations

import tomllib
import types
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from behave_kit._core.errors import ConfigError
from behave_kit.env.profiles import apply_overrides, select_profile


@dataclass(frozen=True)
class KitConfig:
    """Read-only, deeply immutable resolved configuration."""

    env: str
    base_url: str = ""
    browser: str = ""
    timeouts: Mapping[str, int] = field(
        default_factory=lambda: types.MappingProxyType({}),
    )
    credentials: Mapping[str, str] = field(
        default_factory=lambda: types.MappingProxyType({}),
    )
    raw: Mapping[str, Any] = field(
        default_factory=lambda: types.MappingProxyType({}),
    )

    @classmethod
    def from_toml(
        cls,
        path: str | Path,
        *,
        env: str | None = None,
        overrides: dict[str, str] | None = None,
    ) -> KitConfig:
        """Load a ``KitConfig`` from a TOML file.

        ``env`` defaults to ``behave_kit.env`` if omitted. CLI ``--set``
        overrides are dotted keys flattened to top-level strings.

        Raises:
            ConfigError: if the file is missing, unreadable, malformed, or
                the requested profile does not exist.
        """
        file_path = Path(path)
        try:
            if not file_path.is_file():
                raise ConfigError(
                    f"Configuration file not found or is not a file: {file_path}",
                    suggestion="Create a behave.toml at the project root",
                )
            with file_path.open("rb") as f:
                data = tomllib.load(f)
        except FileNotFoundError as exc:
            raise ConfigError(
                f"Configuration file not found: {file_path}",
                cause=exc,
                suggestion="Create a behave.toml at the project root",
            ) from exc
        except tomllib.TOMLDecodeError as exc:
            raise ConfigError(
                f"Invalid TOML in {file_path}: {exc}",
                cause=exc,
                suggestion="Fix the syntax error shown above",
            ) from exc
        except OSError as exc:
            raise ConfigError(
                f"Cannot read configuration file {file_path}: {exc}",
                cause=exc,
                suggestion="Check the path and file permissions",
            ) from exc

        env_name = env or data.get("behave_kit", {}).get("env", "default")
        if not isinstance(env_name, str):
            raise ConfigError(
                f"'behave_kit.env' must be a string, got {type(env_name).__name__}",
                suggestion="Set behave_kit.env to a profile name",
            )

        try:
            resolved = select_profile(data, env_name)
        except ConfigError:
            raise
        except Exception as exc:
            raise ConfigError(
                f"Cannot resolve profile '{env_name}' from {file_path}: {exc}",
                cause=exc,
                suggestion="Check the [env] table structure",
            ) from exc

        resolved = apply_overrides(resolved, overrides or {})

        timeouts_value = resolved.get("timeouts", {})
        if not isinstance(timeouts_value, Mapping):
            raise ConfigError(
                f"'timeouts' must be a table, got {type(timeouts_value).__name__}",
                suggestion="Use [timeouts] in behave.toml or pass a valid override",
            )
        credentials_value = resolved.get("credentials", {})
        if not isinstance(credentials_value, Mapping):
            raise ConfigError(
                f"'credentials' must be a table, got {type(credentials_value).__name__}",
                suggestion="Use [credentials] in behave.toml or pass a valid override",
            )

        return cls(
            env=env_name,
            base_url=resolved.get("base_url", ""),
            browser=resolved.get("browser", ""),
            timeouts=types.MappingProxyType(
                {key: int(value) for key, value in timeouts_value.items()}
            ),
            credentials=types.MappingProxyType(
                {str(key): str(value) for key, value in credentials_value.items()}
            ),
            raw=types.MappingProxyType(resolved),
        )

    def get(self, key: str, default: Any = None) -> Any:
        """Return the raw configuration value for ``key`` or ``default``."""
        return self.raw.get(key, default)
