"""Tests for behave_kit.assertions.diff."""

from types import SimpleNamespace

import pytest

from behave_kit.assertions.diff import (
    assert_dict_contains,
    assert_json_equals,
    assert_list_ordered,
    assert_table_equals,
)


def test_assert_json_equals_passes_on_match() -> None:
    assert_json_equals({"a": 1}, {"a": 1})


def test_assert_json_equals_fails_with_diff_message() -> None:
    with pytest.raises(AssertionError, match=r"at a: expected 1, got 2"):
        assert_json_equals({"a": 2}, {"a": 1})


def test_assert_dict_contains_passes_when_subset_present() -> None:
    assert_dict_contains({"a": 1, "b": 2}, {"a": 1})


def test_assert_dict_contains_fails_on_missing_key() -> None:
    with pytest.raises(AssertionError, match="missing key 'c'"):
        assert_dict_contains({"a": 1}, {"c": 3})


def test_assert_dict_contains_fails_on_mismatch() -> None:
    with pytest.raises(AssertionError, match="key 'a'"):
        assert_dict_contains({"a": 1}, {"a": 2})


def test_assert_list_ordered_passes_for_sorted_list() -> None:
    assert_list_ordered([1, 2, 3])


def test_assert_list_ordered_fails_for_unsorted_list() -> None:
    with pytest.raises(AssertionError):
        assert_list_ordered([3, 1, 2])


def test_assert_list_ordered_with_key() -> None:
    items = [{"n": 1}, {"n": 2}, {"n": 3}]
    assert_list_ordered(items, key=lambda item: item["n"])


def test_assert_table_equals_passes_for_matching_tables() -> None:
    actual = SimpleNamespace(headings=["a", "b"], rows=[["1", "2"], ["3", "4"]])
    expected = SimpleNamespace(headings=["a", "b"], rows=[["1", "2"], ["3", "4"]])
    assert_table_equals(actual, expected)


def test_assert_table_equals_fails_for_differing_tables() -> None:
    actual = SimpleNamespace(headings=["a", "b"], rows=[["1", "2"]])
    expected = SimpleNamespace(headings=["a", "b"], rows=[["1", "9"]])
    with pytest.raises(AssertionError):
        assert_table_equals(actual, expected)
