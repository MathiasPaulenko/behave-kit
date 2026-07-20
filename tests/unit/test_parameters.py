"""Tests for behave_kit.steps.parameters."""

from datetime import date, datetime
from decimal import Decimal

import pytest

from behave_kit._core.errors import FixtureError, StepError
from behave_kit.steps.parameters import convert, parameter_type, register_builtin_types

register_builtin_types()


def test_register_custom_type_and_convert() -> None:
    @parameter_type("upper_test", r"\w+")
    def to_upper(value: str) -> str:
        return value.upper()

    assert convert("upper_test", "hello") == "HELLO"


def test_register_duplicate_name_raises() -> None:
    @parameter_type("dup_test", r"\w+")
    def first(value: str) -> str:
        return value

    with pytest.raises(FixtureError):

        @parameter_type("dup_test", r"\w+")
        def second(value: str) -> str:
            return value


def test_convert_int() -> None:
    assert convert("int", "42") == 42


def test_convert_int_invalid_raises() -> None:
    with pytest.raises(StepError):
        convert("int", "not-a-number")


def test_convert_float() -> None:
    assert convert("float", "3.14") == pytest.approx(3.14)


def test_convert_date() -> None:
    assert convert("date", "2024-01-15") == date(2024, 1, 15)


def test_convert_datetime() -> None:
    assert convert("datetime", "2024-01-15T10:30:00") == datetime(2024, 1, 15, 10, 30, 0)


def test_convert_decimal() -> None:
    assert convert("decimal", "19.99") == Decimal("19.99")


def test_convert_email_valid() -> None:
    assert convert("email", "user@example.com") == "user@example.com"


def test_convert_email_invalid_raises() -> None:
    with pytest.raises(StepError):
        convert("email", "not-an-email")


def test_convert_url_valid() -> None:
    assert convert("url", "https://example.com") == "https://example.com"


def test_convert_url_invalid_raises() -> None:
    with pytest.raises(StepError):
        convert("url", "not a url")


def test_register_builtin_types_is_idempotent() -> None:
    register_builtin_types()
    register_builtin_types()
    assert convert("int", "1") == 1
