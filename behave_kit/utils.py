"""`get_path` — navigate nested dicts with dot notation.

Avoids chaining ``[]`` and handling ``KeyError`` / ``TypeError`` manually
when extracting a value from a deeply nested JSON/dict response.
"""

from __future__ import annotations

from typing import Any

from behave_kit._core.errors import BehaveKitError

_MISSING = object()


def get_path(data: object, path: str, default: Any = _MISSING) -> Any:
    """Return the value at ``path`` within nested ``data``, or ``default``.

    ``path`` uses dot notation to traverse nested dicts:

        get_path(response, "user.address.city")

    Numeric segments traverse lists:

        get_path(response, "users.0.name")

    Args:
        data: The root dict or list to traverse.
        path: Dot-separated path string.
        default: Value to return when the path does not exist.
            If not provided, `BehaveKitError` is raised instead.

    Raises:
        BehaveKitError: When the path is not found and no ``default`` is given.
    """
    if not path:
        raise BehaveKitError(
            "path must not be empty",
            suggestion='Use a dot-separated path like "user.address.city"',
        )

    current: object = data
    for segment in path.split("."):
        if segment == "":
            raise BehaveKitError(
                f"Invalid path '{path}': empty segment",
                suggestion="Remove consecutive dots from the path",
            )
        if isinstance(current, dict):
            if segment not in current:
                if default is not _MISSING:
                    return default
                raise BehaveKitError(
                    f"Key '{segment}' not found in path '{path}'",
                    suggestion=f"Available keys: {', '.join(sorted(current)) or '(none)'}",
                )
            current = current[segment]
        elif isinstance(current, list):
            try:
                index = int(segment)
            except ValueError as exc:
                if default is not _MISSING:
                    return default
                raise BehaveKitError(
                    f"Cannot index list with '{segment}' in path '{path}'",
                    cause=exc,
                    suggestion="Use a numeric index for list segments",
                ) from exc
            if index < 0 or index >= len(current):
                if default is not _MISSING:
                    return default
                raise BehaveKitError(
                    f"Index {index} out of range for list of length {len(current)} "
                    f"in path '{path}'",
                    suggestion=(
                        f"Valid indices: 0-{len(current) - 1}" if current else "List is empty"
                    ),
                )
            current = current[index]
        else:
            if default is not _MISSING:
                return default
            raise BehaveKitError(
                f"Cannot traverse into {type(current).__name__} at '{segment}' "
                f"in path '{path}'",
                suggestion="Check the path matches the data structure",
            )

    return current
