"""Dump the Behave context to JSON for post-mortem debugging.

`behave.runner.Context` stores user attributes in an internal stack of
dict "layers" (`context._stack`), not in the instance `__dict__`. This
module reads that stack when available and falls back to `vars(context)`
for simple mock contexts (e.g. `types.SimpleNamespace`) used in tests.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from behave_kit._core.logging import get_logger
from behave_kit._core.types import Context

logger = get_logger("context.dump")

_SERIALIZABLE_SCALARS = (str, int, float, bool, type(None))


def _is_serializable(value: object) -> bool:
    if isinstance(value, _SERIALIZABLE_SCALARS):
        return True
    if isinstance(value, (list, tuple)):
        return all(_is_serializable(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _is_serializable(val) for key, val in value.items())
    return False


def _raw_attrs(context: Context) -> dict[str, Any]:
    stack = getattr(context, "_stack", None)
    if stack is None:
        return dict(vars(context))
    merged: dict[str, Any] = {}
    for frame in reversed(list(stack)):
        merged.update(frame)
    return merged


def _serializable_attrs(context: Context) -> dict[str, Any]:
    attrs: dict[str, Any] = {}
    for name, value in _raw_attrs(context).items():
        if name.startswith("_") or name.startswith("@"):
            continue
        if _is_serializable(value):
            attrs[name] = value
        else:
            logger.warning(
                "Skipping non-serializable context attribute '%s' (%s)",
                name,
                type(value).__name__,
            )
    return attrs


def _safe_filename(name: str) -> str:
    return "".join(char if char.isalnum() else "_" for char in name) or "context"


def dump_context(context: Context, path: str | Path = "debug/") -> Path:
    """Write every JSON-serializable attribute of ``context`` to a file.

    Non-serializable attributes are skipped with a `logging.warning`.

    Returns:
        The path of the written file.
    """
    output_dir = Path(path)
    output_dir.mkdir(parents=True, exist_ok=True)
    attrs = _serializable_attrs(context)
    scenario = getattr(context, "scenario", None)
    scenario_name = getattr(scenario, "name", None) or "context"
    output_file = output_dir / f"{_safe_filename(str(scenario_name))}.json"
    output_file.write_text(json.dumps(attrs, indent=2, default=str), encoding="utf-8")
    return output_file


def dump_context_on_failure(
    context: Context,
    scenario: object,
    path: str | Path = "debug/",
) -> Path | None:
    """Call `dump_context` only when ``scenario.status`` is ``"failed"``."""
    status = getattr(scenario, "status", None)
    status_name = getattr(status, "name", status)
    if str(status_name).lower() != "failed":
        return None
    return dump_context(context, path)
