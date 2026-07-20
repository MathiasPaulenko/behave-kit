"""Profile selection and override application for raw `behave.toml` data.

Operates on plain dicts (as returned by `tomllib.load`) so profile
resolution can be unit-tested without touching the filesystem or
`KitConfig`.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from behave_kit._core.errors import ConfigError


def _merge_profiles(default: Mapping[str, Any], profile: Mapping[str, Any]) -> dict[str, Any]:
    """Merge ``profile`` over ``default`` recursively for nested dicts."""
    merged: dict[str, Any] = dict(default)
    for key, value in profile.items():
        if (
            key in merged
            and isinstance(merged[key], Mapping)
            and isinstance(value, Mapping)
            and not isinstance(merged[key], str)
            and not isinstance(value, str)
        ):
            merged[key] = _merge_profiles(merged[key], value)
        else:
            merged[key] = value
    return merged


def select_profile(toml_data: dict[str, Any], env_name: str) -> dict[str, Any]:
    """Return the ``[env.<env_name>]`` section merged over ``[env.default]``.

    Raises:
        ConfigError: if ``env_name`` has no matching section or the TOML
            structure is invalid.
    """
    if not isinstance(toml_data, Mapping):
        raise ConfigError("Configuration data must be a mapping")
    environments = toml_data.get("env", {})
    if not isinstance(environments, Mapping):
        raise ConfigError("'env' must be a table")
    default_section = environments.get("default", {})
    if not isinstance(default_section, Mapping):
        raise ConfigError("'env.default' must be a table")
    profile = environments.get(env_name)
    if not isinstance(profile, Mapping):
        raise ConfigError(
            f"Environment profile 'env.{env_name}' not found",
            suggestion=f"Available profiles: {', '.join(sorted(environments)) or '(none)'}",
        )
    return _merge_profiles(default_section, profile)


def apply_overrides(config_dict: dict[str, Any], overrides: dict[str, str]) -> dict[str, Any]:
    """Return ``config_dict`` with CLI ``--set key=value`` overrides applied on top."""
    merged = dict(config_dict)
    merged.update(overrides)
    return merged
