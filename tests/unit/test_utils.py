"""Tests for behave_kit.utils.get_path."""

import pytest

from behave_kit._core.errors import BehaveKitError
from behave_kit.utils import get_path


def test_get_path_simple_key() -> None:
    assert get_path({"name": "Alice"}, "name") == "Alice"


def test_get_path_nested_dict() -> None:
    data = {"user": {"address": {"city": "Berlin"}}}
    assert get_path(data, "user.address.city") == "Berlin"


def test_get_path_list_index() -> None:
    data = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
    assert get_path(data, "users.0.name") == "Alice"
    assert get_path(data, "users.1.name") == "Bob"


def test_get_path_missing_key_raises() -> None:
    with pytest.raises(BehaveKitError, match="Key 'missing'"):
        get_path({"a": 1}, "missing")


def test_get_path_missing_key_returns_default() -> None:
    assert get_path({"a": 1}, "missing", default="fallback") == "fallback"


def test_get_path_index_out_of_range_raises() -> None:
    with pytest.raises(BehaveKitError, match="out of range"):
        get_path({"items": [1, 2]}, "items.5")


def test_get_path_index_out_of_range_returns_default() -> None:
    assert get_path({"items": [1, 2]}, "items.5", default=None) is None


def test_get_path_non_dict_midway_raises() -> None:
    with pytest.raises(BehaveKitError, match="Cannot traverse into int"):
        get_path({"a": 1}, "a.b")


def test_get_path_non_dict_midway_returns_default() -> None:
    assert get_path({"a": 1}, "a.b", default="x") == "x"


def test_get_path_empty_path_raises() -> None:
    with pytest.raises(BehaveKitError, match="empty"):
        get_path({"a": 1}, "")


def test_get_path_consecutive_dots_raises() -> None:
    with pytest.raises(BehaveKitError, match="empty segment"):
        get_path({"a": {"b": 1}}, "a..b")


def test_get_path_non_numeric_list_index_raises() -> None:
    with pytest.raises(BehaveKitError, match="Cannot index list"):
        get_path({"items": [1, 2]}, "items.foo")


def test_get_path_non_numeric_list_index_returns_default() -> None:
    assert get_path({"items": [1, 2]}, "items.foo", default=-1) == -1


def test_get_path_empty_list_index_raises() -> None:
    with pytest.raises(BehaveKitError, match="List is empty"):
        get_path({"items": []}, "items.0")


def test_get_path_negative_list_index_raises() -> None:
    with pytest.raises(BehaveKitError, match="out of range"):
        get_path({"items": [1, 2, 3]}, "items.-1")


def test_get_path_negative_list_index_returns_default() -> None:
    assert get_path({"items": [1, 2, 3]}, "items.-1", default="x") == "x"
