"""Assertions that fail with a legible diff instead of a bare `AssertionError`."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any, Protocol

from behave_kit.assertions._matchers import CompareOptions, DiffResult, deep_compare


class _TableLike(Protocol):
    """Structural shape of a `behave.model.Table` (and compatible objects)."""

    headings: Sequence[str]
    rows: Sequence[Sequence[str]]


def _format_diff_result(result: DiffResult, msg: str) -> str:
    lines = [msg] if msg else []
    lines.append(f"Found {len(result.diffs)} difference(s):")
    for diff in result.diffs:
        lines.append(f"  at {diff.path}: {diff.message}")
    return "\n".join(lines)


def assert_json_equals(
    actual: object,
    expected: object,
    *,
    msg: str = "",
    options: CompareOptions | None = None,
) -> None:
    """Assert that ``actual`` deep-equals ``expected``, showing which keys differ."""
    result = deep_compare(actual, expected, options)
    if not result.equal:
        raise AssertionError(_format_diff_result(result, msg))


def assert_dict_contains(
    d: Mapping[Any, Any],
    subset: Mapping[Any, Any],
    *,
    msg: str = "",
) -> None:
    """Assert that ``d`` contains every key/value pair present in ``subset``."""
    missing_keys = set(subset) - set(d)
    mismatched = {
        key: (subset[key], d[key]) for key in subset if key in d and d[key] != subset[key]
    }
    if not missing_keys and not mismatched:
        return
    details = [
        f"  missing key '{key}' (expected {subset[key]!r})" for key in sorted(missing_keys, key=str)
    ]
    for key in sorted(mismatched, key=str):
        expected_value, actual_value = mismatched[key]
        details.append(f"  key '{key}': expected {expected_value!r}, got {actual_value!r}")
    lines = [msg] if msg else []
    lines.extend(details)
    raise AssertionError("\n".join(lines))


def assert_list_ordered(
    lst: Sequence[Any],
    *,
    key: Callable[[Any], Any] | None = None,
    msg: str = "",
) -> None:
    """Assert that ``lst`` is sorted, optionally by a ``key`` function."""
    key_fn = key or (lambda item: item)
    values = [key_fn(item) for item in lst]
    if values != sorted(values):
        raise AssertionError(msg or f"List is not ordered: {values!r}")


def _table_to_rows(table: _TableLike) -> list[dict[str, str]]:
    headings = list(table.headings)
    return [dict(zip(headings, list(row), strict=True)) for row in table.rows]


def assert_table_equals(actual: _TableLike, expected: _TableLike, *, msg: str = "") -> None:
    """Assert that two Behave Data Tables have the same headings and rows."""
    result = deep_compare(_table_to_rows(actual), _table_to_rows(expected))
    if not result.equal:
        raise AssertionError(_format_diff_result(result, msg))
