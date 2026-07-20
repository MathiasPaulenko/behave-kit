"""Tests for behave_kit.data.providers."""

import pytest

from behave_kit._core.errors import FixtureError
from behave_kit.data.providers import data_provider, get_provider


def test_data_provider_registers_and_get_returns_it() -> None:
    @data_provider("users_test_1")
    def build_users() -> list[dict[str, str]]:
        return [{"name": "alice"}]

    provider = get_provider("users_test_1")
    assert provider() == [{"name": "alice"}]


def test_data_provider_duplicate_name_raises() -> None:
    @data_provider("duplicate_test")
    def first() -> list[dict[str, str]]:
        return []

    with pytest.raises(FixtureError):

        @data_provider("duplicate_test")
        def second() -> list[dict[str, str]]:
            return []


def test_get_provider_missing_raises() -> None:
    with pytest.raises(FixtureError):
        get_provider("does_not_exist_provider")
