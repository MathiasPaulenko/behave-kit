"""Tests for behave_kit.timeout."""

from __future__ import annotations

import time
from collections.abc import Iterator
from unittest.mock import patch

import pytest

from behave_kit.timeout import (
    _IS_WINDOWS,
    _TIMEOUT_HANDLER_KEY,
    SignalTimeoutHandler,
    ThreadTimeoutHandler,
    _parse_timeout_tag,
    _parse_timeout_value,
    _select_handler,
    setup_timeout,
    timeout_after_scenario,
    timeout_before_scenario,
)

# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class FakeFeature:
    """Minimal stand-in for behave's Feature model."""

    def __init__(self, tags: list[str] | None = None) -> None:
        self.tags = tags or []


class FakeScenario:
    """Minimal stand-in for behave's Scenario model."""

    def __init__(
        self,
        tags: list[str] | None = None,
        feature: FakeFeature | None = None,
    ) -> None:
        self.tags = tags or []
        self.feature = feature


class FakeContext:
    """Minimal stand-in for behave's Context."""

    def __init__(self) -> None:
        pass

    def __setattr__(self, name: str, value: object) -> None:
        super().__setattr__(name, value)

    def __getattr__(self, name: str) -> object:
        raise AttributeError(name)


@pytest.fixture
def ctx() -> FakeContext:
    return FakeContext()


@pytest.fixture
def reset_handler_key(ctx: FakeContext) -> Iterator[None]:
    """Ensure _behave_kit_timeout_handler is cleaned up after each test."""
    yield
    if hasattr(ctx, "_behave_kit_timeout_handler"):
        delattr(ctx, "_behave_kit_timeout_handler")


# ---------------------------------------------------------------------------
# _parse_timeout_value
# ---------------------------------------------------------------------------


def test_parse_timeout_value_valid() -> None:
    assert _parse_timeout_value("timeout:10", "timeout") == 10.0


def test_parse_timeout_value_float() -> None:
    assert _parse_timeout_value("timeout:0.5", "timeout") == 0.5


def test_parse_timeout_value_wrong_tag() -> None:
    assert _parse_timeout_value("other:10", "timeout") is None


def test_parse_timeout_value_no_prefix() -> None:
    assert _parse_timeout_value("timeout", "timeout") is None


def test_parse_timeout_value_invalid_number() -> None:
    assert _parse_timeout_value("timeout:abc", "timeout") is None


def test_parse_timeout_value_negative() -> None:
    assert _parse_timeout_value("timeout:-5", "timeout") is None


def test_parse_timeout_value_custom_tag_name() -> None:
    assert _parse_timeout_value("limit:30", "limit") == 30.0


def test_parse_timeout_value_zero() -> None:
    assert _parse_timeout_value("timeout:0", "timeout") == 0.0


# ---------------------------------------------------------------------------
# _parse_timeout_tag
# ---------------------------------------------------------------------------


def test_parse_timeout_tag_from_scenario() -> None:
    scenario = FakeScenario(tags=["timeout:15"])
    assert _parse_timeout_tag(scenario, "timeout") == 15.0


def test_parse_timeout_tag_from_feature() -> None:
    feature = FakeFeature(tags=["timeout:60"])
    scenario = FakeScenario(feature=feature)
    assert _parse_timeout_tag(scenario, "timeout") == 60.0


def test_parse_timeout_tag_scenario_overrides_feature() -> None:
    feature = FakeFeature(tags=["timeout:60"])
    scenario = FakeScenario(tags=["timeout:10"], feature=feature)
    assert _parse_timeout_tag(scenario, "timeout") == 10.0


def test_parse_timeout_tag_no_tags() -> None:
    scenario = FakeScenario()
    assert _parse_timeout_tag(scenario, "timeout") is None


def test_parse_timeout_tag_no_feature() -> None:
    scenario = FakeScenario(tags=["other:10"])
    assert _parse_timeout_tag(scenario, "timeout") is None


def test_parse_timeout_tag_feature_with_no_tags() -> None:
    feature = FakeFeature()
    scenario = FakeScenario(feature=feature)
    assert _parse_timeout_tag(scenario, "timeout") is None


def test_parse_timeout_tag_mixed_tags() -> None:
    scenario = FakeScenario(tags=["smoke", "timeout:5", "regression"])
    assert _parse_timeout_tag(scenario, "timeout") == 5.0


def test_parse_timeout_tag_custom_tag_name() -> None:
    scenario = FakeScenario(tags=["limit:42"])
    assert _parse_timeout_tag(scenario, "limit") == 42.0


# ---------------------------------------------------------------------------
# setup_timeout
# ---------------------------------------------------------------------------


def test_setup_timeout_sets_default(ctx: FakeContext) -> None:
    setup_timeout(ctx, default_timeout=30)
    assert ctx._behave_kit_timeout_default == 30


def test_setup_timeout_sets_tag_name(ctx: FakeContext) -> None:
    setup_timeout(ctx, default_timeout=10, timeout_tag="limit")
    assert ctx._behave_kit_timeout_tag == "limit"


def test_setup_timeout_default_tag_name(ctx: FakeContext) -> None:
    setup_timeout(ctx, default_timeout=10)
    assert ctx._behave_kit_timeout_tag == "timeout"


def test_setup_timeout_zero_default(ctx: FakeContext) -> None:
    setup_timeout(ctx, default_timeout=0)
    assert ctx._behave_kit_timeout_default == 0


def test_setup_timeout_negative_raises(ctx: FakeContext) -> None:
    with pytest.raises(ValueError, match="non-negative"):
        setup_timeout(ctx, default_timeout=-1)


def test_setup_timeout_reads_env_var(ctx: FakeContext, monkeypatch) -> None:
    monkeypatch.setenv("BEHAVE_SCENARIO_TIMEOUT", "25")
    setup_timeout(ctx)
    assert ctx._behave_kit_timeout_default == 25.0


def test_setup_timeout_env_var_defaults_to_zero(ctx: FakeContext, monkeypatch) -> None:
    monkeypatch.delenv("BEHAVE_SCENARIO_TIMEOUT", raising=False)
    setup_timeout(ctx)
    assert ctx._behave_kit_timeout_default == 0.0


def test_setup_timeout_explicit_arg_ignores_env_var(ctx: FakeContext, monkeypatch) -> None:
    monkeypatch.setenv("BEHAVE_SCENARIO_TIMEOUT", "25")
    setup_timeout(ctx, default_timeout=30)
    assert ctx._behave_kit_timeout_default == 30


def test_setup_timeout_env_var_negative_raises(ctx: FakeContext, monkeypatch) -> None:
    monkeypatch.setenv("BEHAVE_SCENARIO_TIMEOUT", "-5")
    with pytest.raises(ValueError, match="non-negative"):
        setup_timeout(ctx)


# ---------------------------------------------------------------------------
# timeout_before_scenario / timeout_after_scenario
# ---------------------------------------------------------------------------


def test_before_scenario_no_timeout_when_default_zero(ctx: FakeContext) -> None:
    setup_timeout(ctx, default_timeout=0)
    scenario = FakeScenario()
    timeout_before_scenario(ctx, scenario)
    assert getattr(ctx, "_behave_kit_timeout_handler", None) is None


def test_before_scenario_no_timeout_no_setup(ctx: FakeContext) -> None:
    scenario = FakeScenario()
    timeout_before_scenario(ctx, scenario)
    assert getattr(ctx, "_behave_kit_timeout_handler", None) is None


def test_before_scenario_uses_default(ctx: FakeContext) -> None:
    setup_timeout(ctx, default_timeout=30)
    scenario = FakeScenario()
    timeout_before_scenario(ctx, scenario)
    assert hasattr(ctx, "_behave_kit_timeout_handler")


def test_before_scenario_tag_overrides_default(ctx: FakeContext) -> None:
    setup_timeout(ctx, default_timeout=30)
    scenario = FakeScenario(tags=["timeout:5"])
    timeout_before_scenario(ctx, scenario)
    handler = ctx._behave_kit_timeout_handler
    assert handler.timeout == 5.0


def test_before_scenario_feature_tag_used(ctx: FakeContext) -> None:
    setup_timeout(ctx, default_timeout=30)
    feature = FakeFeature(tags=["timeout:60"])
    scenario = FakeScenario(feature=feature)
    timeout_before_scenario(ctx, scenario)
    handler = ctx._behave_kit_timeout_handler
    assert handler.timeout == 60.0


def test_before_scenario_scenario_tag_overrides_feature_tag(ctx: FakeContext) -> None:
    setup_timeout(ctx, default_timeout=30)
    feature = FakeFeature(tags=["timeout:60"])
    scenario = FakeScenario(tags=["timeout:10"], feature=feature)
    timeout_before_scenario(ctx, scenario)
    handler = ctx._behave_kit_timeout_handler
    assert handler.timeout == 10.0


def test_after_scenario_noop_without_handler(ctx: FakeContext) -> None:
    scenario = FakeScenario()
    timeout_after_scenario(ctx, scenario)


def test_after_scenario_cleans_up_handler(ctx: FakeContext) -> None:
    setup_timeout(ctx, default_timeout=30)
    scenario = FakeScenario()
    timeout_before_scenario(ctx, scenario)
    assert hasattr(ctx, "_behave_kit_timeout_handler")
    timeout_after_scenario(ctx, scenario)
    assert getattr(ctx, "_behave_kit_timeout_handler", None) is None


def test_timeout_zero_tag_disables(ctx: FakeContext) -> None:
    """A @timeout:0 tag should disable the timeout even if default is set."""
    setup_timeout(ctx, default_timeout=30)
    scenario = FakeScenario(tags=["timeout:0"])
    timeout_before_scenario(ctx, scenario)
    assert getattr(ctx, "_behave_kit_timeout_handler", None) is None


# ---------------------------------------------------------------------------
# SignalTimeoutHandler (Unix only)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(_IS_WINDOWS, reason="SIGALRM not available on Windows")
class TestSignalTimeoutHandler:
    def test_does_not_raise_when_within_timeout(self) -> None:
        with SignalTimeoutHandler(1.0):
            pass

    def test_raises_timeout_error_when_exceeded(self) -> None:
        with pytest.raises(TimeoutError, match="exceeded timeout"), SignalTimeoutHandler(0.05):
            time.sleep(0.3)

    def test_zero_timeout_is_noop(self) -> None:
        with SignalTimeoutHandler(0):
            time.sleep(0.05)

    def test_restores_previous_handler(self) -> None:
        import signal as sig

        original = sig.getsignal(sig.SIGALRM)
        with SignalTimeoutHandler(1.0):
            pass
        restored = sig.getsignal(sig.SIGALRM)
        assert restored == original

    def test_cancels_timer_on_exit(self) -> None:
        import signal as sig

        with SignalTimeoutHandler(10.0):
            pass
        # After exit, the itimer should be 0
        remaining, _ = sig.getitimer(sig.ITIMER_REAL)
        assert remaining == 0.0


# ---------------------------------------------------------------------------
# ThreadTimeoutHandler (all platforms, but especially Windows)
# ---------------------------------------------------------------------------


class TestThreadTimeoutHandler:
    def test_does_not_raise_when_within_timeout(self) -> None:
        with ThreadTimeoutHandler(1.0):
            pass

    def test_raises_timeout_error_when_exceeded(self) -> None:
        with pytest.raises(TimeoutError, match="exceeded timeout"), ThreadTimeoutHandler(0.05):
            time.sleep(0.3)

    def test_zero_timeout_is_noop(self) -> None:
        with ThreadTimeoutHandler(0):
            time.sleep(0.05)

    def test_cancels_timer_on_normal_exit(self) -> None:
        handler = ThreadTimeoutHandler(10.0)
        with handler:
            pass
        # Timer should have been cancelled — _entered is False after exit
        assert handler._entered is False
        assert handler._timer is None

    def test_does_not_raise_if_exception_already_present(self) -> None:
        handler = ThreadTimeoutHandler(0.05)
        handler.__enter__()
        time.sleep(0.15)
        # If there's already an exception, __exit__ should not raise
        # (the existing exception takes priority)
        handler.__exit__(ValueError, ValueError("existing"), None)

    def test_timer_is_daemon(self) -> None:
        handler = ThreadTimeoutHandler(10.0)
        handler.__enter__()
        assert handler._timer is not None
        assert handler._timer.daemon is True
        handler.__exit__(None, None, None)


# ---------------------------------------------------------------------------
# _select_handler
# ---------------------------------------------------------------------------


def test_select_handler_returns_thread_on_windows() -> None:
    with patch("behave_kit.timeout._IS_WINDOWS", True):
        handler = _select_handler(5.0)
        assert isinstance(handler, ThreadTimeoutHandler)


def test_select_handler_returns_signal_on_unix() -> None:
    with patch("behave_kit.timeout._IS_WINDOWS", False):
        handler = _select_handler(5.0)
        assert isinstance(handler, SignalTimeoutHandler)


def test_select_handler_default_on_current_platform() -> None:
    handler = _select_handler(5.0)
    if _IS_WINDOWS:
        assert isinstance(handler, ThreadTimeoutHandler)
    else:
        assert isinstance(handler, SignalTimeoutHandler)


# ---------------------------------------------------------------------------
# Integration: hooks flow
# ---------------------------------------------------------------------------


def test_full_hook_flow_with_default_timeout(ctx: FakeContext) -> None:
    """setup_timeout + before + after should work end-to-end."""
    setup_timeout(ctx, default_timeout=30)
    scenario = FakeScenario()
    timeout_before_scenario(ctx, scenario)
    assert hasattr(ctx, "_behave_kit_timeout_handler")
    timeout_after_scenario(ctx, scenario)
    assert getattr(ctx, "_behave_kit_timeout_handler", None) is None


def test_full_hook_flow_with_tag_override(ctx: FakeContext) -> None:
    setup_timeout(ctx, default_timeout=30)
    scenario = FakeScenario(tags=["timeout:5"])
    timeout_before_scenario(ctx, scenario)
    handler = ctx._behave_kit_timeout_handler
    assert handler.timeout == 5.0
    timeout_after_scenario(ctx, scenario)


def test_full_hook_flow_no_timeout(ctx: FakeContext) -> None:
    setup_timeout(ctx, default_timeout=0)
    scenario = FakeScenario()
    timeout_before_scenario(ctx, scenario)
    assert getattr(ctx, "_behave_kit_timeout_handler", None) is None
    timeout_after_scenario(ctx, scenario)


def test_custom_tag_name_in_hooks(ctx: FakeContext) -> None:
    setup_timeout(ctx, default_timeout=30, timeout_tag="limit")
    scenario = FakeScenario(tags=["limit:15"])
    timeout_before_scenario(ctx, scenario)
    handler = ctx._behave_kit_timeout_handler
    assert handler.timeout == 15.0
    timeout_after_scenario(ctx, scenario)


def test_invalid_tag_value_falls_back_to_default(ctx: FakeContext) -> None:
    setup_timeout(ctx, default_timeout=20)
    scenario = FakeScenario(tags=["timeout:abc"])
    timeout_before_scenario(ctx, scenario)
    handler = ctx._behave_kit_timeout_handler
    assert handler.timeout == 20.0
    timeout_after_scenario(ctx, scenario)


def test_negative_tag_value_falls_back_to_default(ctx: FakeContext) -> None:
    setup_timeout(ctx, default_timeout=20)
    scenario = FakeScenario(tags=["timeout:-5"])
    timeout_before_scenario(ctx, scenario)
    handler = ctx._behave_kit_timeout_handler
    assert handler.timeout == 20.0
    timeout_after_scenario(ctx, scenario)


# ---------------------------------------------------------------------------
# teardown_timeout from hooks.py
# ---------------------------------------------------------------------------


def test_teardown_timeout_noop_without_handler(ctx: FakeContext) -> None:
    from behave_kit.hooks import teardown_timeout

    teardown_timeout(ctx)


def test_teardown_timeout_cleans_up(ctx: FakeContext) -> None:
    from behave_kit.hooks import teardown_timeout

    setup_timeout(ctx, default_timeout=30)
    scenario = FakeScenario()
    timeout_before_scenario(ctx, scenario)
    ctx.scenario = scenario
    teardown_timeout(ctx)
    assert getattr(ctx, "_behave_kit_timeout_handler", None) is None


# ---------------------------------------------------------------------------
# SignalTimeoutHandler with mocked signal (covers Unix code on Windows)
# ---------------------------------------------------------------------------


class TestSignalTimeoutHandlerMocked:
    """Test SignalTimeoutHandler logic with mocked signal module.

    These tests run on all platforms and cover the SignalTimeoutHandler
    code paths that would otherwise be skipped on Windows.
    """

    def test_enter_sets_signal_and_timer(self) -> None:
        calls: list[tuple[str, ...]] = []

        def fake_signal(signum: int, handler: object) -> object:
            calls.append(("signal", str(signum)))
            return lambda *_a: None

        def fake_setitimer(which: int, seconds: float) -> None:
            calls.append(("setitimer", str(which), str(seconds)))

        with patch("behave_kit.timeout.signal") as mock_sig:
            mock_sig.SIGALRM = 14
            mock_sig.ITIMER_REAL = 0
            mock_sig.signal = fake_signal
            mock_sig.setitimer = fake_setitimer

            handler = SignalTimeoutHandler(5.0)
            handler.__enter__()

        assert ("signal", "14") in calls
        assert any(c[0] == "setitimer" and c[2] == "5.0" for c in calls)

    def test_exit_cancels_timer_and_restores_handler(self) -> None:
        calls: list[str] = []

        def original_handler(*_a: object) -> None:
            pass

        def fake_signal(signum: int, handler: object) -> object:
            return original_handler

        def fake_setitimer(which: int, seconds: float) -> None:
            calls.append(f"setitimer:{seconds}")

        with patch("behave_kit.timeout.signal") as mock_sig:
            mock_sig.SIGALRM = 14
            mock_sig.ITIMER_REAL = 0
            mock_sig.signal = fake_signal
            mock_sig.setitimer = fake_setitimer

            handler = SignalTimeoutHandler(5.0)
            handler.__enter__()
            handler.__exit__(None, None, None)

        assert "setitimer:0" in calls

    def test_zero_timeout_enter_is_noop(self) -> None:
        with patch("behave_kit.timeout.signal") as mock_sig:
            mock_sig.SIGALRM = 14
            mock_sig.ITIMER_REAL = 0

            handler = SignalTimeoutHandler(0)
            handler.__enter__()
            mock_sig.signal.assert_not_called()
            mock_sig.setitimer.assert_not_called()

    def test_zero_timeout_exit_is_noop(self) -> None:
        with patch("behave_kit.timeout.signal") as mock_sig:
            mock_sig.SIGALRM = 14
            mock_sig.ITIMER_REAL = 0

            handler = SignalTimeoutHandler(0)
            handler.__enter__()
            handler.__exit__(None, None, None)
            mock_sig.setitimer.assert_not_called()

    def test_handle_timeout_raises_timeout_error(self) -> None:
        handler = SignalTimeoutHandler(5.0)
        with pytest.raises(TimeoutError, match="exceeded timeout of 5.0s"):
            handler._handle_timeout(14, None)


# ---------------------------------------------------------------------------
# Regression tests for bug fixes
# ---------------------------------------------------------------------------


def test_parse_timeout_value_rejects_inf() -> None:
    """inf is not a valid timeout — it would create a handler that never fires."""
    assert _parse_timeout_value("timeout:inf", "timeout") is None


def test_parse_timeout_value_rejects_nan() -> None:
    """nan is not a valid timeout — nan > 0 is False, behaviour is confusing."""
    assert _parse_timeout_value("timeout:nan", "timeout") is None


def test_parse_timeout_value_rejects_negative_inf() -> None:
    """-inf is not a valid timeout."""
    assert _parse_timeout_value("timeout:-inf", "timeout") is None


def test_setup_timeout_rejects_inf_default(ctx: FakeContext) -> None:
    with pytest.raises(ValueError, match="finite"):
        setup_timeout(ctx, default_timeout=float("inf"))


def test_setup_timeout_rejects_nan_default(ctx: FakeContext) -> None:
    with pytest.raises(ValueError, match="finite"):
        setup_timeout(ctx, default_timeout=float("nan"))


def test_setup_timeout_rejects_empty_tag(ctx: FakeContext) -> None:
    with pytest.raises(ValueError, match="non-empty string"):
        setup_timeout(ctx, default_timeout=10, timeout_tag="")


def test_setup_timeout_rejects_none_tag(ctx: FakeContext) -> None:
    with pytest.raises(ValueError, match="non-empty string"):
        setup_timeout(ctx, default_timeout=10, timeout_tag=None)  # type: ignore[arg-type]


def test_thread_handler_reentrancy_raises() -> None:
    """ThreadTimeoutHandler.__enter__ twice should raise RuntimeError."""
    handler = ThreadTimeoutHandler(10.0)
    handler.__enter__()
    try:
        with pytest.raises(RuntimeError, match="not reentrant"):
            handler.__enter__()
    finally:
        handler.__exit__(None, None, None)


def test_thread_handler_exit_without_enter_is_noop() -> None:
    """ThreadTimeoutHandler.__exit__ without __enter__ should be a no-op."""
    handler = ThreadTimeoutHandler(10.0)
    handler.__exit__(None, None, None)


def test_signal_handler_exit_without_enter_is_noop() -> None:
    """SignalTimeoutHandler.__exit__ without __enter__ should be a no-op."""
    handler = SignalTimeoutHandler(10.0)
    handler.__exit__(None, None, None)


def test_signal_handler_reentrancy_raises() -> None:
    """SignalTimeoutHandler.__enter__ twice should raise RuntimeError."""
    with patch("behave_kit.timeout.signal") as mock_sig:
        mock_sig.SIGALRM = 14
        mock_sig.ITIMER_REAL = 0
        mock_sig.signal = lambda *_a: None
        mock_sig.setitimer = lambda *_a: None

        handler = SignalTimeoutHandler(5.0)
        handler.__enter__()
        try:
            with pytest.raises(RuntimeError, match="not reentrant"):
                handler.__enter__()
        finally:
            handler.__exit__(None, None, None)


def test_after_scenario_preserves_existing_exception(ctx: FakeContext) -> None:
    """If scenario already failed, timeout_after_scenario should not mask it."""
    # Use ThreadTimeoutHandler directly — this test is about the ThreadTimer
    # fallback behaviour (SignalTimeoutHandler raises immediately during step
    # execution, so there's nothing to check in after_scenario).
    handler = ThreadTimeoutHandler(0.05)
    handler.__enter__()
    setattr(ctx, _TIMEOUT_HANDLER_KEY, handler)
    # Simulate the timer firing
    handler._timed_out = True

    class ScenarioWithException:
        tags: list[str] = []
        feature = None
        exception = ValueError("original step failure")

    scenario = ScenarioWithException()
    # Should NOT raise TimeoutError because the scenario has an existing exception
    timeout_after_scenario(ctx, scenario)


def test_after_scenario_raises_when_no_existing_exception(ctx: FakeContext) -> None:
    """If scenario has no exception and timer fired, TimeoutError should be raised."""
    handler = ThreadTimeoutHandler(0.05)
    handler.__enter__()
    setattr(ctx, _TIMEOUT_HANDLER_KEY, handler)
    handler._timed_out = True

    class ScenarioNoException:
        tags: list[str] = []
        feature = None
        exception = None

    scenario = ScenarioNoException()
    with pytest.raises(TimeoutError, match="exceeded timeout"):
        timeout_after_scenario(ctx, scenario)


def test_after_scenario_with_non_exception_attr(ctx: FakeContext) -> None:
    """If scenario.exception is not a BaseException, it should be ignored."""
    handler = ThreadTimeoutHandler(0.05)
    handler.__enter__()
    setattr(ctx, _TIMEOUT_HANDLER_KEY, handler)
    handler._timed_out = True

    class ScenarioWithBadException:
        tags: list[str] = []
        feature = None
        exception = "not an exception"  # type: ignore[assignment]

    scenario = ScenarioWithBadException()
    with pytest.raises(TimeoutError, match="exceeded timeout"):
        timeout_after_scenario(ctx, scenario)


def test_setup_timeout_idempotent(ctx: FakeContext) -> None:
    """Calling setup_timeout twice should update values, not crash."""
    setup_timeout(ctx, default_timeout=10)
    assert ctx._behave_kit_timeout_default == 10
    setup_timeout(ctx, default_timeout=30)
    assert ctx._behave_kit_timeout_default == 30


def test_parse_timeout_value_scientific_notation() -> None:
    """Scientific notation like 1e2 should be accepted as 100.0."""
    assert _parse_timeout_value("timeout:1e2", "timeout") == 100.0


def test_parse_timeout_value_with_spaces() -> None:
    """Values with leading/trailing spaces should be accepted (float() handles them)."""
    assert _parse_timeout_value("timeout: 5 ", "timeout") == 5.0
