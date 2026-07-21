"""Pure, side-effect-free deep comparison.

Every function here takes plain values in and returns a `DiffResult` out.
No Behave dependency, no context, no I/O — fully unit-testable.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


@dataclass(frozen=True)
class Diff:
    """A single difference found while comparing ``actual`` to ``expected``."""

    path: str
    expected: object
    actual: object
    message: str


@dataclass(frozen=True)
class DiffResult:
    """Outcome of a `deep_compare` call."""

    equal: bool
    diffs: list[Diff] = field(default_factory=list)


@dataclass(frozen=True)
class CompareOptions:
    """Tunable behavior for `deep_compare`."""

    ignore_keys: frozenset[str] = frozenset()
    float_tolerance: float = 1e-9
    ignore_order: bool = False
    datetime_tolerance: timedelta | None = None
    custom_matchers: dict[type, Callable[[Any, Any], bool]] = field(default_factory=dict)


def deep_compare(
    actual: object,
    expected: object,
    options: CompareOptions | None = None,
) -> DiffResult:
    """Recursively compare ``actual`` to ``expected`` and report all differences."""
    options = options or CompareOptions()
    diffs: list[Diff] = []
    _compare(actual, expected, "", options, diffs, set())
    return DiffResult(equal=not diffs, diffs=diffs)


def _join(path: str, key: object) -> str:
    return f"{path}.{key}" if path else str(key)


def _mismatch(path: str, expected: object, actual: object) -> Diff:
    return Diff(
        path=path or "<root>",
        expected=expected,
        actual=actual,
        message=f"expected {expected!r}, got {actual!r}",
    )


def _custom_matcher(
    actual: object,
    expected: object,
    custom_matchers: dict[type, Callable[[Any, Any], bool]],
) -> Callable[[Any, Any], bool] | None:
    """Return the most specific custom matcher that accepts both values."""
    candidates = [
        cls for cls in custom_matchers if isinstance(actual, cls) and isinstance(expected, cls)
    ]
    if not candidates:
        return None
    for candidate in candidates:
        if all(candidate is other or issubclass(candidate, other) for other in candidates):
            return custom_matchers[candidate]
    return custom_matchers[candidates[0]]


def _compare(
    actual: object,
    expected: object,
    path: str,
    options: CompareOptions,
    diffs: list[Diff],
    seen: set[tuple[int, int]],
) -> None:
    if actual is expected:
        return

    pair = (id(actual), id(expected))
    if pair in seen:
        return

    matcher = _custom_matcher(actual, expected, options.custom_matchers)
    if matcher is not None:
        if not matcher(actual, expected):
            diffs.append(
                Diff(
                    path=path or "<root>",
                    expected=expected,
                    actual=actual,
                    message=f"custom matcher failed for {type(expected).__name__}",
                )
            )
        return

    if isinstance(expected, bool) or isinstance(actual, bool):
        if type(actual) is not type(expected) or actual != expected:
            diffs.append(_mismatch(path, expected, actual))
        return
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        if math.isnan(actual) or math.isnan(expected):
            diffs.append(_mismatch(path, expected, actual))
            return
        if abs(float(actual) - float(expected)) > options.float_tolerance:
            diffs.append(_mismatch(path, expected, actual))
        return
    if isinstance(expected, datetime) and isinstance(actual, datetime):
        tolerance = options.datetime_tolerance
        if tolerance is None:
            if actual != expected:
                diffs.append(_mismatch(path, expected, actual))
        else:
            try:
                delta = abs(actual - expected)
            except TypeError:
                diffs.append(_mismatch(path, expected, actual))
                return
            if delta > tolerance:
                diffs.append(_mismatch(path, expected, actual))
        return

    if isinstance(actual, (list, tuple, dict, set, Mapping)) and isinstance(
        expected, (list, tuple, dict, set, Mapping)
    ):
        seen.add(pair)

    if isinstance(expected, Mapping) and isinstance(actual, Mapping):
        _compare_mapping(actual, expected, path, options, diffs, seen)
        return
    if isinstance(expected, (list, tuple)) and isinstance(actual, (list, tuple)):
        _compare_sequence(actual, expected, path, options, diffs, seen)
        return
    if isinstance(expected, set) and isinstance(actual, set):
        _compare_set(actual, expected, path, diffs)
        return
    if actual != expected:
        diffs.append(_mismatch(path, expected, actual))


def _compare_mapping(
    actual: Mapping[Any, Any],
    expected: Mapping[Any, Any],
    path: str,
    options: CompareOptions,
    diffs: list[Diff],
    seen: set[tuple[int, int]],
) -> None:
    actual_keys = set(actual.keys()) - options.ignore_keys
    expected_keys = set(expected.keys()) - options.ignore_keys
    for key in sorted(expected_keys - actual_keys, key=str):
        diffs.append(
            Diff(
                path=_join(path, key),
                expected=expected[key],
                actual=None,
                message=f"missing key '{key}'",
            )
        )
    for key in sorted(actual_keys - expected_keys, key=str):
        diffs.append(
            Diff(
                path=_join(path, key),
                expected=None,
                actual=actual[key],
                message=f"unexpected key '{key}'",
            )
        )
    for key in sorted(actual_keys & expected_keys, key=str):
        _compare(actual[key], expected[key], _join(path, key), options, diffs, seen)


def _compare_sequence(
    actual: Sequence[Any],
    expected: Sequence[Any],
    path: str,
    options: CompareOptions,
    diffs: list[Diff],
    seen: set[tuple[int, int]],
) -> None:
    if options.ignore_order:
        _compare_sequence_unordered(actual, expected, path, options, diffs, seen)
        return
    if len(actual) != len(expected):
        diffs.append(
            Diff(
                path=path or "<root>",
                expected=list(expected),
                actual=list(actual),
                message=f"length mismatch: expected {len(expected)}, got {len(actual)}",
            )
        )
    for index, expected_item in enumerate(expected):
        if index >= len(actual):
            break
        _compare(actual[index], expected_item, f"{path}[{index}]", options, diffs, seen)


def _compare_sequence_unordered(
    actual: Sequence[Any],
    expected: Sequence[Any],
    path: str,
    options: CompareOptions,
    diffs: list[Diff],
    seen: set[tuple[int, int]],
) -> None:
    remaining = list(actual)
    for index, expected_item in enumerate(expected):
        item_path = _join(path, index)
        best_index: int | None = None
        best_probe: list[Diff] | None = None
        for candidate_index, actual_item in enumerate(remaining):
            probe: list[Diff] = []
            _compare(actual_item, expected_item, item_path, options, probe, seen)
            if not probe:
                best_index = candidate_index
                best_probe = probe
                break
            if best_probe is None or len(probe) < len(best_probe):
                best_index = candidate_index
                best_probe = probe
        if best_probe is not None and best_index is not None:
            if best_probe:
                diffs.extend(best_probe)
            remaining.pop(best_index)
        else:
            diffs.append(
                Diff(
                    path=item_path or "<root>",
                    expected=expected_item,
                    actual=None,
                    message=f"no matching item for expected[{index}]",
                )
            )
    for extra_index, extra_item in enumerate(remaining):
        extra_path = _join(path, f"?{extra_index}")
        diffs.append(
            Diff(
                path=extra_path or "<root>",
                expected=None,
                actual=extra_item,
                message=f"unexpected item {extra_item!r}",
            )
        )


def _compare_set(actual: set[Any], expected: set[Any], path: str, diffs: list[Diff]) -> None:
    missing = expected - actual
    extra = actual - expected
    if missing or extra:
        diffs.append(
            Diff(
                path=path or "<root>",
                expected=expected,
                actual=actual,
                message=f"sets differ: missing={missing}, extra={extra}",
            )
        )
