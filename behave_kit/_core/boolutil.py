"""Shared scalar-bool coercion used by soft asserts and conditional steps.

Tolerates array-like objects (e.g. numpy arrays) by falling back to
``.all()`` when ``bool(value)`` would raise.
"""

from __future__ import annotations


def as_bool(value: object) -> bool:
    """Return a scalar bool, tolerating array-like objects."""
    try:
        return bool(value)
    except (ValueError, TypeError):
        pass
    try:
        return bool(value.all())  # type: ignore[attr-defined]
    except (AttributeError, ValueError, TypeError):
        pass
    return False
