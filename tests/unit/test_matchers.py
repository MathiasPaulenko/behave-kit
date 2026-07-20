"""Tests for behave_kit.assertions._matchers."""

from datetime import datetime, timedelta

from behave_kit.assertions._matchers import CompareOptions, deep_compare


def test_equal_dicts() -> None:
    result = deep_compare({"a": 1, "b": 2}, {"a": 1, "b": 2})
    assert result.equal
    assert result.diffs == []


def test_differing_dicts_report_path() -> None:
    result = deep_compare({"a": 1, "b": 3}, {"a": 1, "b": 2})
    assert not result.equal
    assert len(result.diffs) == 1
    assert result.diffs[0].path == "b"


def test_missing_key_reported() -> None:
    result = deep_compare({"a": 1}, {"a": 1, "b": 2})
    assert not result.equal
    assert any("missing key 'b'" in diff.message for diff in result.diffs)


def test_unexpected_key_reported() -> None:
    result = deep_compare({"a": 1, "b": 2}, {"a": 1})
    assert not result.equal
    assert any("unexpected key 'b'" in diff.message for diff in result.diffs)


def test_ignore_keys_skips_differences() -> None:
    options = CompareOptions(ignore_keys=frozenset({"timestamp"}))
    result = deep_compare(
        {"id": 1, "timestamp": "2024-01-01"},
        {"id": 1, "timestamp": "2025-01-01"},
        options,
    )
    assert result.equal


def test_nested_lists_report_index_path() -> None:
    result = deep_compare(
        {"users": [{"email": "a@x.com"}, {"email": "wrong@x.com"}]},
        {"users": [{"email": "a@x.com"}, {"email": "b@x.com"}]},
    )
    assert not result.equal
    assert result.diffs[0].path == "users[1].email"


def test_sequence_length_mismatch() -> None:
    result = deep_compare([1, 2], [1, 2, 3])
    assert not result.equal
    assert any("length mismatch" in diff.message for diff in result.diffs)


def test_float_within_tolerance_is_equal() -> None:
    result = deep_compare(1.0000000001, 1.0, CompareOptions(float_tolerance=1e-6))
    assert result.equal


def test_float_outside_tolerance_is_not_equal() -> None:
    result = deep_compare(1.1, 1.0, CompareOptions(float_tolerance=1e-6))
    assert not result.equal


def test_datetime_exact_match() -> None:
    now = datetime(2024, 1, 1, 12, 0, 0)
    result = deep_compare(now, now)
    assert result.equal


def test_datetime_with_tolerance() -> None:
    base = datetime(2024, 1, 1, 12, 0, 0)
    options = CompareOptions(datetime_tolerance=timedelta(seconds=5))
    result = deep_compare(base + timedelta(seconds=2), base, options)
    assert result.equal


def test_datetime_outside_tolerance() -> None:
    base = datetime(2024, 1, 1, 12, 0, 0)
    options = CompareOptions(datetime_tolerance=timedelta(seconds=1))
    result = deep_compare(base + timedelta(seconds=5), base, options)
    assert not result.equal


def test_sets_equal() -> None:
    result = deep_compare({1, 2, 3}, {3, 2, 1})
    assert result.equal


def test_sets_differ() -> None:
    result = deep_compare({1, 2}, {1, 2, 3})
    assert not result.equal
    assert "missing" in result.diffs[0].message


def test_ignore_order_matches_lists_regardless_of_position() -> None:
    options = CompareOptions(ignore_order=True)
    result = deep_compare([3, 1, 2], [1, 2, 3], options)
    assert result.equal


def test_ignore_order_detects_real_differences() -> None:
    options = CompareOptions(ignore_order=True)
    result = deep_compare([1, 2, 4], [1, 2, 3], options)
    assert not result.equal


def test_none_values_equal() -> None:
    result = deep_compare(None, None)
    assert result.equal


def test_none_vs_value_differs() -> None:
    result = deep_compare(None, "something")
    assert not result.equal


def test_custom_matcher_used_for_type() -> None:
    class Money:
        def __init__(self, cents: int) -> None:
            self.cents = cents

    options = CompareOptions(custom_matchers={Money: lambda a, b: a.cents == b.cents})
    result = deep_compare(Money(100), Money(100), options)
    assert result.equal


def test_custom_matcher_reports_failure() -> None:
    class Money:
        def __init__(self, cents: int) -> None:
            self.cents = cents

    options = CompareOptions(custom_matchers={Money: lambda a, b: a.cents == b.cents})
    result = deep_compare(Money(50), Money(100), options)
    assert not result.equal
