"""Second-pass bug hunting tests for behave_kit.steps.classes.

Focuses on subtler issues:
- Missing compile() validation for custom matchers
- Dedup/ambiguity semantics with shared locations
- Parent+child registration interactions
- use_step_matcher global state interaction
- Context variants (slots, frozen dataclasses)
- Re-registration after clear() with same patterns
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from behave.matchers import RegexMatcher
from behave.step_registry import AmbiguousStep

from behave_kit._core.errors import StepError
from behave_kit.steps.classes import (
    _INSTANCES_KEY,
    _registration_records,
    step_impl_base,
    teardown_steps,
)


def _run_step(step_text: str, step_type: str, context: object) -> None:
    """Invoke the matcher for ``step_text`` directly on ``context``."""
    from behave.runner import the_step_registry

    step = SimpleNamespace(name=step_text, step_type=step_type)
    match = the_step_registry.find_match(step)
    assert match is not None, f"No match found for {step_text!r}"
    args: list[object] = []
    kwargs: dict[str, object] = {}
    for arg in match.arguments:
        if arg.name is not None:
            kwargs[arg.name] = arg.value
        else:
            args.append(arg.value)
    match.func(context, *args, **kwargs)


@pytest.fixture(autouse=True)
def _clean_registry() -> object:
    """Isolate each test from the global Behave step registry."""
    from behave.runner import the_step_registry

    saved = {kw: list(steps) for kw, steps in the_step_registry.steps.items()}
    saved_records = dict(_registration_records)
    _registration_records.clear()
    yield
    for kw in the_step_registry.steps:
        the_step_registry.steps[kw] = saved.get(kw, [])
    _registration_records.clear()
    _registration_records.update(saved_records)


# --- Bug E: Missing compile() validation for custom matchers ---


def test_bug_e_malformed_regex_with_regex_matcher_fails_at_registration() -> None:
    """A malformed regex pattern with matcher=RegexMatcher should fail at register().

    BUG: ``_build_matcher`` constructs the matcher but never calls
    ``compile()``.  Behave's ``add_step_definition`` calls
    ``is_good_step_definition`` which calls ``compile()`` to validate
    the pattern early.  Without this, a malformed regex is silently
    added and only fails at match time with a confusing error.
    """
    Base = step_impl_base()

    class Steps(Base):
        # Unclosed group — invalid regex.
        @Base.given("a malformed regex step (with unclosed group", matcher=RegexMatcher)
        def step_one(self) -> None:
            pass

    with pytest.raises((re_error_type(), StepError), match="unclosed|malformed|regex|step"):
        Steps.register()


def re_error_type() -> type:
    import re

    return re.error


def test_bug_e_malformed_regex_with_default_matcher_fails_at_registration() -> None:
    """A malformed regex with default_matcher=RegexMatcher should fail at register()."""
    Base = step_impl_base(default_matcher=RegexMatcher)

    class Steps(Base):
        @Base.given("a malformed default regex step (unclosed")
        def step_one(self) -> None:
            pass

    with pytest.raises((re_error_type(), StepError)):
        Steps.register()


# --- Bug F: Two classes from same base, same pattern, different impls ---


def test_bug_f_two_classes_same_pattern_different_impls_raises_ambiguous() -> None:
    """Two classes from the same base registering the same pattern should raise.

    BUG: ``_add_matcher_to_registry`` dedups on
    ``existing.pattern == matcher_obj.pattern and
    matcher_obj.location == existing.location``.  Since ``functools.wraps``
    makes ``unwrap_function`` return the original method, two methods
    with the same name from different classes have DIFFERENT locations
    (different ``co_filename``/``co_firstlineno``).  So the dedup
    check correctly does NOT dedup, and the ambiguity check raises
    ``AmbiguousStep``.  This test verifies that behavior is preserved.
    """
    Base = step_impl_base()

    class StepsA(Base):
        @Base.given("a shared pattern bug-f step")
        def step_one(self) -> None:
            self.context.from_a = True

    class StepsB(Base):
        @Base.given("a shared pattern bug-f step")
        def step_one(self) -> None:
            self.context.from_b = True

    StepsA.register()
    with pytest.raises(AmbiguousStep):
        StepsB.register()
    StepsA.clear()
    StepsB.clear()


# --- Bug G: Registering both parent and child ---


def test_bug_g_register_parent_then_child_dedups_inherited_steps() -> None:
    """Registering parent then child should dedup inherited steps, not raise.

    When ``Child`` inherits a step from ``Parent`` (no override),
    ``getattr(Child, func_name)`` returns the SAME function as
    ``getattr(Parent, func_name)``.  ``_make_step_wrapper`` creates a
    new wrapper, but ``functools.wraps`` sets ``__wrapped__`` to the
    same original method, so ``unwrap_function`` returns the same
    method and ``FileLocation.for_function`` returns the same location.
    The dedup check should then dedup (same pattern, same location).
    """
    Base = step_impl_base()

    class Parent(Base):
        @Base.given("a bug-g inherited step")
        def step_one(self) -> None:
            self.context.from_parent = True

    class Child(Parent):
        pass

    Parent.register()
    # This should NOT raise AmbiguousStep — the inherited step is the
    # same definition (same pattern, same location).
    Child.register()

    # Both should be in _registration_records.
    assert Parent in _registration_records
    assert Child in _registration_records

    # The child's record should have 0 matchers (deduped).
    child_record = _registration_records[Child]
    assert len(child_record.matchers) == 0, (
        f"Child should have 0 matchers (deduped), got {len(child_record.matchers)}"
    )

    Parent.clear()
    Child.clear()


def test_bug_g_register_child_then_parent_dedups() -> None:
    """Registering child then parent should also dedup, not raise."""
    Base = step_impl_base()

    class Parent(Base):
        @Base.given("a bug-g reverse inherited step")
        def step_one(self) -> None:
            self.context.from_parent = True

    class Child(Parent):
        pass

    Child.register()
    Parent.register()  # should not raise

    assert Parent in _registration_records
    assert Child in _registration_records

    # Parent's matchers should be 0 (deduped, child already registered).
    parent_record = _registration_records[Parent]
    assert len(parent_record.matchers) == 0

    Child.clear()
    Parent.clear()


def test_bug_g_register_child_with_override_then_parent_raises() -> None:
    """If child overrides a method, parent registration should raise AmbiguousStep.

    The overridden method has a different location (different
    ``co_firstlineno``), so the dedup check fails and the ambiguity
    check raises.
    """
    Base = step_impl_base()

    class Parent(Base):
        @Base.given("a bug-g override step")
        def step_one(self) -> None:
            self.context.from_parent = True

    class Child(Parent):
        def step_one(self) -> None:
            self.context.from_child = True

    Child.register()
    with pytest.raises(AmbiguousStep):
        Parent.register()
    Child.clear()
    Parent.clear()


# --- Bug H: use_step_matcher interaction ---


def test_bug_h_use_step_matcher_affects_none_matcher_path() -> None:
    """When matcher=None, Behave's current global matcher is used.

    This is the intended behavior — documenting it as a regression test.
    If someone changes the semantics, this test will catch it.

    Note: Behave's ``add_step_definition`` SILENTLY IGNORES bad step
    definitions (returns without adding).  So switching to a matcher
    that can't compile the pattern results in the step not being
    registered — no error is raised at registration time.  This is
    Behave's built-in behavior for the ``matcher=None`` path and is
    outside our control.
    """
    from behave import use_step_matcher

    Base = step_impl_base()

    class Steps(Base):
        @Base.given("a bug-h parse step with {value:d}")
        def step_one(self, value: int) -> None:
            self.context.value = value

    # Default matcher is Parse — pattern compiles fine.
    use_step_matcher("parse")
    Steps.register()
    ctx = SimpleNamespace()
    _run_step("a bug-h parse step with 42", "given", ctx)
    assert ctx.value == 42
    Steps.clear()

    # Switch to regex and re-register.  "{value:d}" is not valid regex
    # for matching a digit, but re.compile may or may not accept it
    # depending on Python version.  Behave's add_step_definition
    # silently ignores bad step definitions, so the step is NOT
    # registered.  This is Behave's behavior, not our bug.
    use_step_matcher("re")
    try:
        Steps.register()
        # The step may or may not have been added (depends on whether
        # re.compile accepts the pattern).  Either way, no exception
        # is raised by register() itself — that's the documented
        # Behave behavior for the matcher=None path.
    finally:
        use_step_matcher("parse")
    Steps.clear()


# --- Bug I: Context variants ---


def test_bug_i_context_with_slots_fails_clearly() -> None:
    """A context class with __slots__ and no _behave_kit_step_instances slot.

    BUG: If the context uses ``__slots__`` without a slot for
    ``_behave_kit_step_instances``, ``setattr(context, _INSTANCES_KEY,
    instances)`` raises ``AttributeError``.  The error message should
    be clear, not a confusing AttributeError from deep inside the
    wrapper.
    """

    class SlottedContext:
        __slots__ = ("value",)

    Base = step_impl_base()

    class Steps(Base):
        @Base.given("a bug-i slotted context step")
        def step_one(self) -> None:
            pass

    Steps.register()
    ctx = SlottedContext()
    with pytest.raises(AttributeError, match=_INSTANCES_KEY):
        _run_step("a bug-i slotted context step", "given", ctx)
    Steps.clear()


def test_bug_i_teardown_steps_with_slotted_context_is_noop() -> None:
    """teardown_steps on a slotted context without instances should be a no-op."""

    class SlottedContext:
        __slots__ = ("value",)

    ctx = SlottedContext()
    # getattr(ctx, _INSTANCES_KEY, None) returns None (no __dict__).
    # teardown_steps should be a no-op.
    teardown_steps(ctx)  # should not raise


# --- Bug J: clear() doesn't clear local_registry ---


def test_bug_j_clear_then_reregister_does_not_double_register() -> None:
    """After clear(), re-registering should not double-register steps.

    BUG: ``clear()`` removes matchers from Behave's registry and
    removes the class from ``_registration_records``, but the
    ``local_registry`` (closure) still has the entries.  Re-registering
    should re-add the steps cleanly, not double-register.
    """
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("a bug-j reregister step")
        def step_one(self) -> None:
            self.context.ran = True

    Steps.register()
    Steps.clear()
    Steps.register()  # should not raise AmbiguousStep
    ctx = SimpleNamespace()
    _run_step("a bug-j reregister step", "given", ctx)
    assert ctx.ran is True
    Steps.clear()


def test_bug_j_multiple_clear_reregister_cycles() -> None:
    """Multiple clear()/register() cycles should work."""
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("a bug-j cyclic step")
        def step_one(self) -> None:
            self.context.ran = True

    for _ in range(5):
        Steps.register()
        ctx = SimpleNamespace()
        _run_step("a bug-j cyclic step", "given", ctx)
        assert ctx.ran is True
        Steps.clear()


# --- Bug K: Instance identity across steps in the same scenario ---


def test_bug_k_same_instance_used_across_all_steps() -> None:
    """All steps in a scenario share the same instance for a given class."""
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("a bug-k step that sets a marker")
        def step_one(self) -> None:
            self.marker = "set"

        @Base.when("a bug-k step that reads the marker")
        def step_two(self) -> None:
            assert self.marker == "set"
            self.context.marker_read = True

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("a bug-k step that sets a marker", "given", ctx)
    _run_step("a bug-k step that reads the marker", "when", ctx)
    assert ctx.marker_read is True
    instances = getattr(ctx, _INSTANCES_KEY)
    assert len(instances) == 1  # only one instance for Steps
    Steps.clear()


# --- Bug L: setup() called only once even if first step fails ---


def test_bug_l_setup_called_once_even_if_step_raises() -> None:
    """setup() should run once even if the first step method raises."""
    Base = step_impl_base()
    setup_calls: list[int] = []

    class Steps(Base):
        def setup(self) -> None:
            setup_calls.append(1)

        @Base.given("a bug-l failing step")
        def step_one(self) -> None:
            raise RuntimeError("step failed")

        @Base.then("a bug-l subsequent step")
        def step_two(self) -> None:
            self.context.ran = True

    Steps.register()
    ctx = SimpleNamespace()

    with pytest.raises(RuntimeError, match="step failed"):
        _run_step("a bug-l failing step", "given", ctx)

    # Second step should use the same instance (setup not called again).
    _run_step("a bug-l subsequent step", "then", ctx)
    assert ctx.ran is True
    assert len(setup_calls) == 1, f"setup() called {len(setup_calls)} times; expected 1"
    Steps.clear()


# --- Bug M: teardown_steps called twice clears instances ---


def test_bug_m_teardown_steps_called_twice_is_safe() -> None:
    """Calling teardown_steps twice should be safe (no-op the second time)."""
    Base = step_impl_base()
    teardown_calls: list[int] = []

    class Steps(Base):
        @Base.given("a bug-m step")
        def step_one(self) -> None:
            pass

        def teardown(self) -> None:
            teardown_calls.append(1)

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("a bug-m step", "given", ctx)
    teardown_steps(ctx)
    teardown_steps(ctx)  # no-op
    assert len(teardown_calls) == 1
    Steps.clear()


# --- Bug N: Step method that is a classmethod or staticmethod ---


def test_bug_n_classmethod_step_works_but_no_context() -> None:
    """A classmethod step works but doesn't receive self.context.

    Decorators are applied bottom-up: ``@classmethod`` runs first,
    then ``@Base.given`` wraps the classmethod descriptor (returning
    it unchanged).  At call time, ``instance.step_one`` is a bound
    classmethod (bound to the class), so ``cls`` is already provided.
    The wrapper creates an instance and binds context, but the
    classmethod doesn't receive ``self`` or ``context`` — it only
    receives ``cls``.  This is unusual but not a bug; it's just
    how classmethods interact with the wrapper.
    """
    Base = step_impl_base()
    calls: list[str] = []

    class Steps(Base):
        @Base.given("a bug-n classmethod step")
        @classmethod
        def step_one(cls) -> None:
            calls.append(cls.__name__)

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("a bug-n classmethod step", "given", ctx)
    assert calls == ["Steps"]
    Steps.clear()


# --- Bug O: Pattern that matches but with wrong number of groups ---


def test_bug_o_regex_pattern_with_no_groups_passes_positional() -> None:
    """A regex pattern with no groups should pass no positional args."""
    Base = step_impl_base()

    class Steps(Base):
        @Base.then(r"a bug-o no-group step", matcher=RegexMatcher)
        def step_one(self) -> None:
            self.context.ran = True

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("a bug-o no-group step", "then", ctx)
    assert ctx.ran is True
    Steps.clear()


def test_bug_o_regex_pattern_with_many_groups() -> None:
    """A regex pattern with many groups should pass all as positional args."""
    Base = step_impl_base()

    class Steps(Base):
        @Base.then(
            r"a bug-o multi-group step (\w+) (\d+) (\w+)",
            matcher=RegexMatcher,
        )
        def step_one(self, a: str, b: str, c: str) -> None:
            self.context.result = f"{a}-{b}-{c}"

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("a bug-o multi-group step hello 42 world", "then", ctx)
    assert ctx.result == "hello-42-world"
    Steps.clear()


# --- Bug P: Instance not cleared if teardown_steps not called ---


def test_bug_p_instances_persist_if_teardown_not_called() -> None:
    """If teardown_steps is never called, instances persist on context.

    This is documented behavior — the user is responsible for calling
    teardown_steps (or bk.teardown).  But it means a long-lived
    context (e.g., a feature-level context) would accumulate instances.
    This test documents that behavior.
    """
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("a bug-p persistent step")
        def step_one(self) -> None:
            pass

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("a bug-p persistent step", "given", ctx)
    assert hasattr(ctx, _INSTANCES_KEY)
    assert len(getattr(ctx, _INSTANCES_KEY)) == 1
    # Without teardown_steps, the instance persists.
    # This is expected — the user must call teardown_steps.
    Steps.clear()


# --- Bug Q: default_matcher validation at step_impl_base() time ---


def test_bug_q_invalid_default_matcher_raises_at_base_creation() -> None:
    """An invalid default_matcher should raise at step_impl_base() time."""
    with pytest.raises(StepError, match="Unknown step matcher"):
        step_impl_base(default_matcher="nonexistent")

    with pytest.raises(StepError, match="matcher must be"):
        step_impl_base(default_matcher=42)  # type: ignore[arg-type]


def test_bug_q_default_matcher_class_object() -> None:
    """A Matcher subclass as default_matcher should work."""
    Base = step_impl_base(default_matcher=RegexMatcher)

    class Steps(Base):
        @Base.then(r"a bug-q class default step (\d+)")
        def step_one(self, value: str) -> None:
            self.context.value = int(value)

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("a bug-q class default step 99", "then", ctx)
    assert ctx.value == 99
    Steps.clear()
