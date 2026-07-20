"""Profile selection and override application for raw `behave.toml` data.

Operates on plain dicts (as returned by `tomllib.load`) so profile
resolution can be unit-tested without touching the filesystem or
`KitConfig`.
"""

from __future__ import annotations

from typing import Any

from behave_kit._core.errors import ConfigError


def select_profile(toml_data: dict[str, Any], env_name: str) -> dict[str, Any]:
    """Return the ``[env.<env_name>]`` section merged over ``[env.default]``.

    Raises:
        ConfigError: if ``env_name`` has no matching section.
    """
    environments = toml_data.get("env", {})
    default_section = environments.get("default", {})
    profile = environments.get(env_name)
    if profile is None:
        raise ConfigError(
            f"Environment profile 'env.{env_name}' not found",
            suggestion=f"Available profiles: {', '.join(sorted(environments)) or '(none)'}",
        )
    return {**default_section, **profile}


def apply_overrides(config_dict: dict[str, Any], overrides: dict[str, str]) -> dict[str, Any]:
    """Return ``config_dict`` with CLI ``--set key=value`` overrides applied on top."""
    merged = dict(config_dict)
    merged.update(overrides)
    return merged
