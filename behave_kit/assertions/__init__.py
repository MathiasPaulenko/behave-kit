"""Assertion utilities: soft assertions and diff-based comparisons.

Pure comparison logic (`_matchers`) is decoupled from the Behave-facing API
(`diff`, `soft`), which is decoupled from the failure formatting (`reporter`).
"""

from __future__ import annotations

from behave_kit.assertions._matchers import CompareOptions, Diff, DiffResult, deep_compare
from behave_kit.assertions.diff import (
    assert_dict_contains,
    assert_json_equals,
    assert_list_ordered,
    assert_table_equals,
)
from behave_kit.assertions.reporter import SoftAssertReport, SoftFailure
from behave_kit.assertions.soft import (
    SoftAssertCollector,
    assert_soft,
    assert_soft_equals,
    assert_soft_is_none,
    assert_soft_raises,
    assert_soft_true,
    soft_asserts,
    use_soft_asserts,
)

__all__ = [
    "CompareOptions",
    "Diff",
    "DiffResult",
    "deep_compare",
    "assert_dict_contains",
    "assert_json_equals",
    "assert_list_ordered",
    "assert_table_equals",
    "SoftAssertReport",
    "SoftFailure",
    "SoftAssertCollector",
    "assert_soft",
    "assert_soft_equals",
    "assert_soft_is_none",
    "assert_soft_raises",
    "assert_soft_true",
    "soft_asserts",
    "use_soft_asserts",
]
