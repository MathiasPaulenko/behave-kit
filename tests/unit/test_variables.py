"""Tests for behave_kit.env.variables."""

import pytest

from behave_kit._core.errors import EnvVarError
from behave_kit.env.variables import env


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BK_TEST_VAR", raising=False)


def test_env_reads_str_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BK_TEST_VAR", "hello")
    assert env("BK_TEST_VAR") == "hello"


def test_env_converts_int(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BK_TEST_VAR", "42")
    assert env("BK_TEST_VAR", var_type=int) == 42


def test_env_invalid_int_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BK_TEST_VAR", "not-a-number")
    with pytest.raises(EnvVarError):
        env("BK_TEST_VAR", var_type=int)


@pytest.mark.parametrize("raw", ["true", "1", "yes", "on", "TRUE", "Yes"])
def test_env_bool_true_variants(monkeypatch: pytest.MonkeyPatch, raw: str) -> None:
    monkeypatch.setenv("BK_TEST_VAR", raw)
    assert env("BK_TEST_VAR", var_type=bool) is True


@pytest.mark.parametrize("raw", ["false", "0", "no", "off", "FALSE"])
def test_env_bool_false_variants(monkeypatch: pytest.MonkeyPatch, raw: str) -> None:
    monkeypatch.setenv("BK_TEST_VAR", raw)
    assert env("BK_TEST_VAR", var_type=bool) is False


def test_env_bool_invalid_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BK_TEST_VAR", "maybe")
    with pytest.raises(EnvVarError):
        env("BK_TEST_VAR", var_type=bool)


def test_env_required_missing_raises() -> None:
    with pytest.raises(EnvVarError, match="BK_TEST_VAR"):
        env("BK_TEST_VAR")


def test_env_not_required_missing_returns_none() -> None:
    assert env("BK_TEST_VAR", required=False) is None


def test_env_default_used_when_missing() -> None:
    assert env("BK_TEST_VAR", default="fallback") == "fallback"


def test_env_default_not_used_when_present(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BK_TEST_VAR", "actual")
    assert env("BK_TEST_VAR", default="fallback") == "actual"


def test_env_converts_float(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BK_TEST_VAR", "3.14")
    assert env("BK_TEST_VAR", var_type=float) == 3.14


def test_env_converts_default(monkeypatch: pytest.MonkeyPatch) -> None:
    assert env("BK_TEST_VAR", var_type=int, default="30") == 30


def test_env_rejects_bool_as_int() -> None:
    with pytest.raises(EnvVarError):
        env("BK_TEST_VAR", var_type=int, default="true")
