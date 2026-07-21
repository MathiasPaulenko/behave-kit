"""Tests for behave_kit.assertions._matchers."""

from datetime import UTC, datetime, timedelta

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


def test_bool_is_not_int() -> None:
    assert not deep_compare(True, 1).equal
    assert not deep_compare(False, 0).equal
    assert not deep_compare(1, True).equal


def test_nan_is_not_equal() -> None:
    assert not deep_compare(float("nan"), 1.0).equal
    assert not deep_compare(float("nan"), float("nan")).equal


def test_mixed_aware_naive_datetime_reports_diff() -> None:
    options = CompareOptions(datetime_tolerance=timedelta(seconds=5))
    result = deep_compare(datetime.now(UTC), datetime.now(), options)
    assert not result.equal


def test_self_referential_lists_do_not_recurse_forever() -> None:
    a = [1]
    a.append(a)
    result = deep_compare(a, a)
    assert result.equal


def test_custom_matcher_matches_subclass() -> None:
    class Money:
        def __init__(self, cents: int) -> None:
            self.cents = cents

    class SpecialMoney(Money):
        pass

    options = CompareOptions(custom_matchers={Money: lambda a, b: a.cents == b.cents})
    result = deep_compare(SpecialMoney(100), SpecialMoney(100), options)
    assert result.equal


def test_ignore_order_reports_nested_diff_path() -> None:
    options = CompareOptions(ignore_order=True)
    actual = [{"id": 1, "name": "Alice"}]
    expected = [{"id": 1, "name": "Bob"}]
    result = deep_compare(actual, expected, options)
    assert not result.equal
    assert result.diffs[0].path == "0.name"


def test_deep_compare_mixed_list_and_tuple_equal() -> None:
    """Sequences of different concrete types (list vs tuple) compare by value."""
    result = deep_compare([1, 2, 3], (1, 2, 3))
    assert result.equal


def test_deep_compare_mixed_list_and_tuple_differs_by_value() -> None:
    result = deep_compare([1, 2, 3], (1, 2, 4))
    assert not result.equal
    assert result.diffs[0].path == "[2]"


def test_deep_compare_dict_vs_non_mapping_differs() -> None:
    result = deep_compare({"a": 1}, [("a", 1)])
    assert not result.equal


def test_deep_compare_empty_containers_equal() -> None:
    assert deep_compare([], []).equal
    assert deep_compare({}, {}).equal
    assert deep_compare(set(), set()).equal


def test_deep_compare_int_and_float_within_tolerance() -> None:
    assert deep_compare(1, 1.0).equal


def test_self_referential_custom_mapping_does_not_recurse_forever() -> None:
    from collections.abc import Mapping

    class SelfRef(Mapping):
        def __init__(self, key: str, value: object = None) -> None:
            self._data = {key: value if value is not None else self}

        def __getitem__(self, key):  # type: ignore[no-untyped-def]
            return self._data[key]

        def __iter__(self):  # type: ignore[no-untyped-def]
            return iter(self._data)

        def __len__(self) -> int:
            return len(self._data)

    a = SelfRef("self")
    result = deep_compare(a, a)
    assert result.equal
