"""Tests for behave_kit.context.substeps."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from behave_kit._core.errors import SubStepError
from behave_kit.context.substeps import _substitute_outline_vars, run_steps

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _FakeContext:
    """Minimal stand-in for behave.runner.Context."""

    def __init__(
        self,
        *,
        feature: object | None = None,
        active_outline: dict[str, object] | None = None,
        table: object | None = None,
        text: object | None = None,
        execute_raises: Exception | None = None,
    ) -> None:
        self.feature = feature
        self.active_outline = active_outline
        self.table = table
        self.text = text
        self._execute_raises = execute_raises
        self.execute_calls: list[str] = []

    def execute_steps(self, steps: str) -> bool:
        self.execute_calls.append(steps)
        if self._execute_raises is not None:
            raise self._execute_raises
        return True


# ---------------------------------------------------------------------------
# _substitute_outline_vars
# ---------------------------------------------------------------------------


def test_substitute_no_active_outline_returns_unchanged() -> None:
    ctx = _FakeContext(active_outline=None)
    text = "Given I see <username>"
    assert _substitute_outline_vars(ctx, text) == text


def test_substitute_replaces_known_vars() -> None:
    ctx = _FakeContext(active_outline={"username": "admin", "city": "Madrid"})
    text = "Given I log in as <username> in <city>"
    assert _substitute_outline_vars(ctx, text) == "Given I log in as admin in Madrid"


def test_substitute_handles_multiple_same_var() -> None:
    ctx = _FakeContext(active_outline={"x": "42"})
    text = "Given <x> and <x> and <x>"
    assert _substitute_outline_vars(ctx, text) == "Given 42 and 42 and 42"


def test_substitute_unknown_var_raises() -> None:
    ctx = _FakeContext(active_outline={"a": "1"})
    with pytest.raises(SubStepError, match="not found"):
        _substitute_outline_vars(ctx, "Given <b>")


def test_substitute_empty_outline_returns_unchanged() -> None:
    ctx = _FakeContext(active_outline={})
    text = "Given <username>"
    assert _substitute_outline_vars(ctx, text) == text


# ---------------------------------------------------------------------------
# run_steps
# ---------------------------------------------------------------------------


def test_run_steps_outside_feature_raises() -> None:
    ctx = _FakeContext(feature=None)
    with pytest.raises(SubStepError, match="outside of a feature"):
        run_steps(ctx, "Given I do something")


def test_run_steps_non_string_raises() -> None:
    ctx = _FakeContext(feature=object())
    with pytest.raises(SubStepError, match="must be a string"):
        run_steps(ctx, 123)  # type: ignore[arg-type]


def test_run_steps_delegates_to_execute_steps() -> None:
    ctx = _FakeContext(feature=object())
    run_steps(ctx, "Given I do something\nThen I verify")
    assert len(ctx.execute_calls) == 1
    assert "Given I do something" in ctx.execute_calls[0]


def test_run_steps_substitutes_outline_vars() -> None:
    ctx = _FakeContext(feature=object(), active_outline={"user": "admin"})
    run_steps(ctx, "Given I log in as <user>")
    assert ctx.execute_calls == ["Given I log in as admin"]


def test_run_steps_restores_table_and_text() -> None:
    original_table = SimpleNamespace()
    original_text = "original multiline"
    ctx = _FakeContext(feature=object(), table=original_table, text=original_text)
    run_steps(ctx, "Given I do something")
    assert ctx.table is original_table
    assert ctx.text is original_text


def test_run_steps_restores_table_and_text_on_failure() -> None:
    original_table = SimpleNamespace()
    original_text = "original multiline"
    ctx = _FakeContext(
        feature=object(),
        table=original_table,
        text=original_text,
        execute_raises=AssertionError("step failed"),
    )
    with pytest.raises(AssertionError, match="step failed"):
        run_steps(ctx, "Given I do something")
    assert ctx.table is original_table
    assert ctx.text is original_text


def test_run_steps_propagates_assertion_error() -> None:
    ctx = _FakeContext(
        feature=object(),
        execute_raises=AssertionError("sub-step failed"),
    )
    with pytest.raises(AssertionError, match="sub-step failed"):
        run_steps(ctx, "Given I do something")


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_substitute_no_placeholders_returns_unchanged() -> None:
    """Text without any <placeholder> is returned as-is even with active outline."""
    ctx = _FakeContext(active_outline={"user": "admin"})
    text = "Given I log in as admin"
    assert _substitute_outline_vars(ctx, text) == text


def test_substitute_replaces_integer_value() -> None:
    """Non-string outline values are converted via str()."""
    ctx = _FakeContext(active_outline={"count": 42})
    assert _substitute_outline_vars(ctx, "Given I see <count> items") == "Given I see 42 items"


def test_substitute_replaces_float_value() -> None:
    ctx = _FakeContext(active_outline={"price": 9.99})
    assert _substitute_outline_vars(ctx, "Then price is <price>") == "Then price is 9.99"


def test_substitute_replaces_bool_value() -> None:
    ctx = _FakeContext(active_outline={"flag": True})
    assert _substitute_outline_vars(ctx, "Given flag is <flag>") == "Given flag is True"


def test_substitute_preserves_text_without_angle_brackets() -> None:
    ctx = _FakeContext(active_outline={"x": "1"})
    text = "Given a normal step with no variables"
    assert _substitute_outline_vars(ctx, text) == text


def test_substitute_multiple_distinct_vars_in_one_line() -> None:
    ctx = _FakeContext(active_outline={"a": "1", "b": "2", "c": "3"})
    text = "Given <a> and <b> and <c>"
    assert _substitute_outline_vars(ctx, text) == "Given 1 and 2 and 3"


def test_substitute_var_with_spaces_in_name_raises() -> None:
    """Variable names with spaces are not in the outline, so they raise."""
    ctx = _FakeContext(active_outline={"user name": "admin"})
    # The regex <([^>]+)> captures "user name" — it IS in the dict
    result = _substitute_outline_vars(ctx, "Given <user name>")
    assert result == "Given admin"


def test_substitute_adjacent_placeholders() -> None:
    ctx = _FakeContext(active_outline={"a": "x", "b": "y"})
    assert _substitute_outline_vars(ctx, "Given <a><b>") == "Given xy"


def test_substitute_empty_angle_brackets_not_matched() -> None:
    """<> with nothing inside does not match the regex, so text is unchanged."""
    ctx = _FakeContext(active_outline={"a": "1"})
    result = _substitute_outline_vars(ctx, "Given <>")
    assert result == "Given <>"


def test_run_steps_empty_string_raises() -> None:
    """An empty string is rejected before reaching execute_steps."""
    ctx = _FakeContext(feature=object())
    with pytest.raises(SubStepError, match="empty or whitespace-only"):
        run_steps(ctx, "")
    assert ctx.execute_calls == []


def test_run_steps_multiline_step_text() -> None:
    """Multi-line step text is passed as a single string to execute_steps."""
    ctx = _FakeContext(feature=object())
    steps = "Given I do something\nWhen I do another thing\nThen I verify"
    run_steps(ctx, steps)
    assert ctx.execute_calls == [steps]


def test_run_steps_table_and_text_both_none_restores_none() -> None:
    """When table and text are both None, they stay None after restoration."""
    ctx = _FakeContext(feature=object(), table=None, text=None)
    run_steps(ctx, "Given I do something")
    assert ctx.table is None
    assert ctx.text is None


def test_run_steps_substitutes_then_restores_table() -> None:
    """Outline substitution happens, and table is restored even with substitution."""
    original_table = SimpleNamespace(rows=["a", "b"])
    ctx = _FakeContext(
        feature=object(),
        active_outline={"user": "admin"},
        table=original_table,
    )
    run_steps(ctx, "Given I log in as <user>")
    assert ctx.execute_calls == ["Given I log in as admin"]
    assert ctx.table is original_table


def test_run_steps_raises_substep_error_for_non_string_bytes() -> None:
    """bytes is not str, should raise SubStepError."""
    ctx = _FakeContext(feature=object())
    with pytest.raises(SubStepError, match="must be a string"):
        run_steps(ctx, b"Given I do something")  # type: ignore[arg-type]


def test_run_steps_feature_is_falsy_object_raises() -> None:
    """A falsy feature attribute (0, empty string) should trigger the guard."""
    ctx = _FakeContext(feature=0)
    with pytest.raises(SubStepError, match="outside of a feature"):
        run_steps(ctx, "Given I do something")


def test_run_steps_feature_is_empty_string_raises() -> None:
    ctx = _FakeContext(feature="")
    with pytest.raises(SubStepError, match="outside of a feature"):
        run_steps(ctx, "Given I do something")


def test_substitute_error_message_lists_available_vars() -> None:
    """The SubStepError suggestion should list available variable names."""
    ctx = _FakeContext(active_outline={"alpha": "1", "beta": "2"})
    with pytest.raises(SubStepError) as exc_info:
        _substitute_outline_vars(ctx, "Given <gamma>")
    error_msg = str(exc_info.value)
    assert "alpha" in error_msg
    assert "beta" in error_msg


# ---------------------------------------------------------------------------
# Input validation regressions
# ---------------------------------------------------------------------------


def test_run_steps_whitespace_only_raises() -> None:
    """Whitespace-only string is rejected before reaching execute_steps."""
    ctx = _FakeContext(feature=object())
    with pytest.raises(SubStepError, match="empty or whitespace-only"):
        run_steps(ctx, "   \n  \t  ")
    assert ctx.execute_calls == []


def test_substitute_non_dict_active_outline_raises() -> None:
    """active_outline set to a list should raise SubStepError."""
    ctx = _FakeContext(active_outline=["a", "b"])  # type: ignore[arg-type]
    with pytest.raises(SubStepError, match="must be a dict"):
        _substitute_outline_vars(ctx, "Given <a>")


def test_substitute_non_dict_active_outline_string_raises() -> None:
    """active_outline set to a string should raise SubStepError."""
    ctx = _FakeContext(active_outline="not a dict")  # type: ignore[arg-type]
    with pytest.raises(SubStepError, match="must be a dict"):
        _substitute_outline_vars(ctx, "Given <a>")


def test_run_steps_missing_execute_steps_raises() -> None:
    """Context without execute_steps method should raise SubStepError."""

    class _NoExecuteSteps:
        feature = object()
        table = None
        text = None

    ctx = _NoExecuteSteps()  # type: ignore[arg-type]
    with pytest.raises(SubStepError, match="callable execute_steps"):
        run_steps(ctx, "Given I do something")
