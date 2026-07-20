"""Tests for behave_kit._core.errors."""

import pytest

from behave_kit._core.errors import (
    BehaveKitError,
    ConfigError,
    DataLoadError,
    EnvVarError,
    FixtureError,
    ScopeError,
    StepError,
)


def test_base_error_message_without_suggestion() -> None:
    err = BehaveKitError("something went wrong")
    assert str(err) == "something went wrong"
    assert err.message == "something went wrong"
    assert err.suggestion is None
    assert err.cause is None


def test_base_error_message_with_suggestion() -> None:
    err = BehaveKitError("something went wrong", suggestion="try this instead")
    assert str(err) == "something went wrong\n  Suggestion: try this instead"


def test_base_error_carries_cause() -> None:
    original = ValueError("boom")
    err = BehaveKitError("wrapped", cause=original)
    assert err.cause is original


@pytest.mark.parametrize(
    "subclass",
    [ConfigError, EnvVarError, FixtureError, DataLoadError, ScopeError, StepError],
)
def test_subclasses_are_behave_kit_errors(subclass: type[BehaveKitError]) -> None:
    err = subclass("boom", suggestion="fix it")
    assert isinstance(err, BehaveKitError)
    assert str(err) == "boom\n  Suggestion: fix it"


def test_subclasses_are_distinguishable() -> None:
    with pytest.raises(ConfigError):
        raise ConfigError("bad config")
    with pytest.raises(BehaveKitError):
        raise EnvVarError("missing var")
