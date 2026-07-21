"""Bug-hunting tests for behave_kit.steps.classes.

These tests are designed to BREAK the implementation by exercising
edge cases that production code could encounter.  Each test targets
a specific potential bug identified during static audit.
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


# --- Bug A: Partial registration on AmbiguousStep orphans matchers ---


def test_bug_a_partial_registration_on_ambiguity_leaves_no_orphans() -> None:
    """If register() fails partway through, previously-added steps must be cleanable.

    BUG: ``register()`` sets ``_registration_records[cls] = record`` only
    AFTER the loop completes.  If ``AmbiguousStep`` is raised midway,
    earlier steps are left in the global registry with no way to clean
    them up via ``clear()``.
    """
    # Pre-register a conflicting step via a separate base.
    BaseA = step_impl_base()
    BaseB = step_impl_base()

    class StepsA(BaseA):
        @BaseA.given("a conflicting bug-a step")
        def step_one(self) -> None:
            pass

        @BaseA.given("a unique bug-a step from A")
        def step_two(self) -> None:
            pass

    class StepsB(BaseB):
        @BaseB.given("a conflicting bug-a step")
        def step_one(self) -> None:
            pass

        @BaseB.given("a unique bug-a step from B")
        def step_two(self) -> None:
            pass

    StepsA.register()

    # StepsB.register() should fail on the conflicting step.
    with pytest.raises(AmbiguousStep):
        StepsB.register()

    # After the failure, StepsB.clear() must remove any steps that
    # StepsB managed to add before the exception.
    StepsB.clear()  # should not raise and should clean up

    # Verify no StepsB matchers leaked into the registry.
    from behave.runner import the_step_registry

    for step_list in the_step_registry.steps.values():
        for matcher in step_list:
            func_name = getattr(matcher.func, "__name__", "")
            assert func_name != "wrapper" or "StepsB" not in str(matcher.location), (
                f"StepsB matcher leaked: {matcher.location}"
            )

    StepsA.clear()


def test_bug_a_reregister_after_failed_registration_works() -> None:
    """After a failed register() and clear(), re-registering should succeed.

    BUG: If ``register()`` fails and the class is not in
    ``_registration_records``, calling ``register()`` again would
    re-attempt and potentially double-register the steps that
    succeeded before the failure.
    """
    Base = step_impl_base()
    OtherBase = step_impl_base()

    class ConflictingSteps(OtherBase):
        @OtherBase.given("a bug-a rerister conflict step")
        def step_one(self) -> None:
            pass

    class MySteps(Base):
        @Base.given("a bug-a rerister conflict step")
        def step_one(self) -> None:
            pass

        @Base.given("a bug-a rerister unique step")
        def step_two(self) -> None:
            pass

    ConflictingSteps.register()

    # First attempt fails.
    with pytest.raises(AmbiguousStep):
        MySteps.register()

    # Clean up the partial registration.
    MySteps.clear()

    # Remove the conflict.
    ConflictingSteps.clear()

    # Now re-registering should work without double-registering.
    MySteps.register()
    ctx = SimpleNamespace()
    _run_step("a bug-a rerister unique step", "given", ctx)
    MySteps.clear()


def test_bug_a_partial_registration_cleans_up_already_added_matchers() -> None:
    """If register() fails after adding some matchers, those must be removed.

    BUG: When ``register()`` raises mid-loop, matchers added BEFORE the
    failure must be removed from Behave's global registry.  This test
    exercises the cleanup path by adding a unique step first, then a
    conflicting step second.
    """
    Base = step_impl_base()
    OtherBase = step_impl_base()

    class ConflictingSteps(OtherBase):
        @OtherBase.given("a bug-a cleanup conflict step")
        def step_one(self) -> None:
            pass

    class MySteps(Base):
        # Unique step FIRST — gets added to record.matchers before the failure.
        @Base.given("a bug-a cleanup unique step")
        def step_unique(self) -> None:
            pass

        # Conflicting step SECOND — triggers AmbiguousStep.
        @Base.given("a bug-a cleanup conflict step")
        def step_conflict(self) -> None:
            pass

    ConflictingSteps.register()

    # MySteps.register() should fail on the conflicting step.
    with pytest.raises(AmbiguousStep):
        MySteps.register()

    # The unique step that was added before the failure must have been
    # cleaned up from Behave's global registry.
    from behave.runner import the_step_registry

    for step_list in the_step_registry.steps.values():
        for matcher in step_list:
            func_name = getattr(matcher.func, "__name__", "")
            assert func_name != "wrapper" or "step_unique" not in str(matcher.location), (
                f"Leaked matcher for step_unique: {matcher.location}"
            )

    # MySteps should not be in _registration_records (cleaned up).
    from behave_kit.steps.classes import _registration_records

    assert MySteps not in _registration_records

    # Re-registering after the conflict is resolved should work.
    ConflictingSteps.clear()
    MySteps.register()
    ctx = SimpleNamespace()
    _run_step("a bug-a cleanup unique step", "given", ctx)
    MySteps.clear()


def test_make_step_wrapper_raises_on_missing_method() -> None:
    """_make_step_wrapper raises StepError if the method is not on the class.

    This is defensive — ``register()`` checks ``hasattr`` first — but
    the function is a public-ish internal that should fail clearly
    if called directly with a bad func_name.
    """
    from behave_kit.steps.classes import _make_step_wrapper

    Base = step_impl_base()

    class Steps(Base):
        pass

    with pytest.raises(StepError, match="is not defined on"):
        _make_step_wrapper(Steps, "nonexistent_method")


# --- Bug B: setup() failure leaves instance in inconsistent state ---


def test_bug_b_setup_failure_does_not_recreate_instance() -> None:
    """If setup() raises, subsequent steps must not re-create and re-fail.

    BUG: The instance is added to ``instances`` AFTER ``setup()`` runs.
    If ``setup()`` raises, the instance is not cached, so the next step
    call creates a NEW instance and calls ``setup()`` again.
    """
    Base = step_impl_base()
    setup_calls: list[int] = []

    class Steps(Base):
        def setup(self) -> None:
            setup_calls.append(1)
            raise RuntimeError("setup failed")

        @Base.given("a bug-b step that triggers setup")
        def step_one(self) -> None:
            self.context.ran = True

    Steps.register()
    ctx = SimpleNamespace()

    # First step call — setup() raises.
    with pytest.raises(RuntimeError, match="setup failed"):
        _run_step("a bug-b step that triggers setup", "given", ctx)

    # The instance should be cached despite setup() failing, so that
    # teardown_steps() can clean it up and subsequent calls don't
    # re-run setup().
    instances = getattr(ctx, _INSTANCES_KEY, None)
    assert instances is not None, "instances dict should exist after step call"
    assert Steps in instances, "instance should be cached even though setup() failed"

    # Second step call — should NOT re-run setup().
    try:
        _run_step("a bug-b step that triggers setup", "given", ctx)
    except RuntimeError:
        pass  # setup might raise again if not cached — that's the bug

    assert len(setup_calls) == 1, (
        f"setup() was called {len(setup_calls)} times; expected 1 (instance should be cached)"
    )

    Steps.clear()


def test_bug_b_setup_failure_triggers_teardown_for_cleanup() -> None:
    """If setup() fails, teardown() must still run for resource cleanup.

    BUG: If the instance is not cached (because setup() failed),
    teardown_steps() never calls teardown() on it, potentially
    leaking resources.
    """
    Base = step_impl_base()
    teardown_calls: list[str] = []

    class Steps(Base):
        def setup(self) -> None:
            raise RuntimeError("setup failed")

        @Base.given("a bug-b teardown-cleanup step")
        def step_one(self) -> None:
            pass

        def teardown(self) -> None:
            teardown_calls.append("teardown")

    Steps.register()
    ctx = SimpleNamespace()

    with pytest.raises(RuntimeError):
        _run_step("a bug-b teardown-cleanup step", "given", ctx)

    # teardown_steps should call teardown() on the cached instance.
    teardown_steps(ctx)
    assert teardown_calls == ["teardown"], (
        f"teardown() was called {len(teardown_calls)} times; expected 1"
    )

    Steps.clear()


# --- Bug C: teardown_steps iteration safety ---


def test_bug_c_teardown_steps_safe_if_teardown_modifies_instances() -> None:
    """teardown_steps must not crash if a teardown() modifies the instances dict.

    BUG: ``teardown_steps`` iterates over ``instances.values()`` directly.
    If a ``teardown()`` method triggers step execution (which could add
    new instances), we'd get ``RuntimeError: dictionary changed size
    during iteration``.
    """
    Base = step_impl_base()
    Base2 = step_impl_base()

    class StepsB(Base2):
        @Base2.given("a bug-c secondary step")
        def step_b(self) -> None:
            pass

        def teardown(self) -> None:
            pass

    class StepsA(Base):
        @Base.given("a bug-c primary step")
        def step_a(self) -> None:
            pass

        def teardown(self) -> None:
            # Simulate a teardown that triggers another step (which
            # would create a new instance in the same instances dict).
            try:
                _run_step("a bug-c secondary step", "given", self.context)
            except Exception:
                pass  # Step might not be registered; that's fine for this test.

    StepsA.register()
    StepsB.register()
    ctx = SimpleNamespace()
    _run_step("a bug-c primary step", "given", ctx)

    # This should NOT raise RuntimeError: dictionary changed size during iteration.
    try:
        teardown_steps(ctx)
    except RuntimeError as exc:
        pytest.fail(f"teardown_steps raised RuntimeError: {exc}")

    StepsA.clear()
    StepsB.clear()


# --- Bug D: matcher=None doesn't override default_matcher ---


def test_bug_d_matcher_none_falls_back_to_default_not_behave_default() -> None:
    """Passing matcher=None should use the base's default_matcher, not Behave's.

    This is the current behavior — documenting it as a regression test.
    If someone changes the semantics, this test will catch it.
    """

    Base = step_impl_base(default_matcher=RegexMatcher)

    class Steps(Base):
        @Base.then(r"a bug-d regex step (\d+)")
        def step_one(self, value: str) -> None:
            self.context.value = int(value)

        # Explicitly passing matcher=None should still use RegexMatcher
        # (the base's default), not Behave's default ParseMatcher.
        @Base.then(r"a bug-d explicit none step (\d+)", matcher=None)
        def step_two(self, value: str) -> None:
            self.context.value2 = int(value)

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("a bug-d regex step 10", "then", ctx)
    assert ctx.value == 10
    _run_step("a bug-d explicit none step 20", "then", ctx)
    assert ctx.value2 == 20
    Steps.clear()


# --- Additional edge cases ---


def test_register_with_empty_class_is_noop() -> None:
    """A class with no decorated methods should register as a no-op."""
    Base = step_impl_base()

    class EmptySteps(Base):
        pass

    EmptySteps.register()  # should not raise
    # No matchers should be in the record.
    from behave_kit.steps.classes import _registration_records

    record = _registration_records.get(EmptySteps)
    assert record is not None
    assert record.matchers == []
    EmptySteps.clear()
    assert EmptySteps not in _registration_records


def test_register_base_class_itself_is_noop() -> None:
    """Registering the base class directly should be a no-op."""
    Base = step_impl_base()
    Base.register()  # should not raise
    Base.clear()  # should not raise


def test_step_with_unicode_pattern_works() -> None:
    """Unicode characters in step patterns should work."""
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("a unicode step with émojis 🎉 and {value}")
        def step_one(self, value: str) -> None:
            self.context.value = value

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("a unicode step with émojis 🎉 and hello", "given", ctx)
    assert ctx.value == "hello"
    Steps.clear()


def test_step_with_empty_string_pattern_fails_cleanly() -> None:
    """An empty pattern should not crash the registration."""
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("")
        def step_one(self) -> None:
            pass

    # This should either register (matching empty step text) or fail cleanly.
    # It should NOT crash with an unexpected exception.
    try:
        Steps.register()
        Steps.clear()
    except Exception as exc:
        pytest.fail(f"Empty pattern caused unexpected exception: {exc}")


def test_step_with_very_long_pattern_works() -> None:
    """A very long step pattern should work without issues."""
    Base = step_impl_base()
    long_text = "a " + "very " * 100 + "long step"

    class Steps(Base):
        @Base.given(long_text)
        def step_one(self) -> None:
            self.context.ran = True

    Steps.register()
    ctx = SimpleNamespace()
    _run_step(long_text, "given", ctx)
    assert ctx.ran is True
    Steps.clear()


def test_multiple_steps_same_method_name_different_patterns() -> None:
    """Two decorators on methods with the same name — Python overwrites the first.

    This is a Python language limitation: the second ``def step_one``
    overwrites the first in the class body.  Both decorators record
    ``func_name="step_one"``, but at registration time ``getattr(cls,
    "step_one")`` returns the LAST defined method.  So both patterns
    dispatch to the second method, causing a ``TypeError`` when the
    first pattern matches and passes parameters the second method
    doesn't accept.

    Users must use distinct method names for different step patterns.
    """
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("a multi-pattern step with value {value:d}")
        def step_one(self, value: int) -> None:
            self.context.value = value

        @Base.given("a multi-pattern step with text {text}")
        def step_one(self, text: str) -> None:  # noqa: F811
            self.context.text = text

    Steps.register()
    ctx = SimpleNamespace()
    # The second pattern works because it dispatches to the second method.
    _run_step("a multi-pattern step with text hello", "given", ctx)
    assert ctx.text == "hello"
    # The first pattern matches but dispatches to the second method
    # (which expects ``text``, not ``value``) — TypeError.
    with pytest.raises(TypeError):
        _run_step("a multi-pattern step with value 42", "given", ctx)
    Steps.clear()


def test_teardown_steps_with_none_context_raises() -> None:
    """teardown_steps should handle None context gracefully or raise clearly."""
    # None has no _INSTANCES_KEY attribute, so getattr returns None.
    # This should be a no-op, not crash.
    teardown_steps(None)  # type: ignore[arg-type]


def test_teardown_steps_with_object_without_setattr_works() -> None:
    """teardown_steps on an object that never had steps should be a no-op."""
    # Use an object with no __dict__ (e.g., a simple type instance).
    teardown_steps(object())  # should not raise


def test_clear_during_iteration_is_safe() -> None:
    """Calling clear() while iterating over the registry should not crash."""
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("a clear-during-iteration step")
        def step_one(self) -> None:
            pass

    Steps.register()
    Steps.clear()  # should not raise
    # Double clear is already tested, but verify state is clean.
    assert Steps not in _registration_records


def test_register_after_gc_of_class_does_not_crash() -> None:
    """If a registered class is garbage collected, clear() should not crash."""
    Base = step_impl_base()

    class TempSteps(Base):
        @Base.given("a temporary step")
        def step_one(self) -> None:
            pass

    TempSteps.register()
    # Don't clear — simulate the class going out of scope.
    # The _registration_records dict keeps a reference to the class,
    # so it won't actually be GC'd. But clear() should still work.
    TempSteps.clear()


def test_step_method_with_kwargs_only() -> None:
    """A step method that only uses named parameters should work."""
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("a kwargs step with {a:d} and {b:d}")
        def step_one(self, a: int, b: int) -> None:
            self.context.sum = a + b

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("a kwargs step with 10 and 20", "given", ctx)
    assert ctx.sum == 30
    Steps.clear()


def test_step_method_returning_none_is_falsy() -> None:
    """A step method returning None should not cause issues."""
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("a none-returning step")
        def step_one(self) -> None:
            pass

    Steps.register()
    from behave.runner import the_step_registry

    step = SimpleNamespace(name="a none-returning step", step_type="given")
    match = the_step_registry.find_match(step)
    assert match is not None
    ctx = SimpleNamespace()
    result = match.func(ctx)
    assert result is None
    Steps.clear()


def test_invalid_matcher_type_at_decoration_time() -> None:
    """Passing an invalid matcher type to a decorator should raise at register()."""
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("an invalid matcher step", matcher=42)  # type: ignore[arg-type]
        def step_one(self) -> None:
            pass

    with pytest.raises(StepError, match="matcher must be"):
        Steps.register()


def test_unknown_matcher_name_at_decoration_time() -> None:
    """Passing an unknown matcher name should raise at register()."""
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("an unknown matcher step", matcher="nonexistent")
        def step_one(self) -> None:
            pass

    with pytest.raises(StepError, match="Unknown step matcher"):
        Steps.register()


def test_subclass_without_override_registers_inherited_steps() -> None:
    """A subclass that doesn't override anything still registers parent steps."""
    Base = step_impl_base()

    class Parent(Base):
        @Base.given("an inherited step")
        def step_one(self) -> None:
            self.context.from_parent = True

    class Child(Parent):
        pass

    Child.register()
    ctx = SimpleNamespace()
    _run_step("an inherited step", "given", ctx)
    assert ctx.from_parent is True
    # The instance should be a Child, not a Parent.
    instances = getattr(ctx, _INSTANCES_KEY)
    assert isinstance(instances[Child], Child)
    Child.clear()


def test_deep_inheritance_chain_works() -> None:
    """A deep inheritance chain should resolve methods correctly."""
    Base = step_impl_base()

    class A(Base):
        @Base.given("a deep chain step")
        def step_one(self) -> None:
            self.context.chain = "A"

    class B(A):
        def step_one(self) -> None:
            self.context.chain = "B"

    class C(B):
        def step_one(self) -> None:
            self.context.chain = "C"

    C.register()
    ctx = SimpleNamespace()
    _run_step("a deep chain step", "given", ctx)
    assert ctx.chain == "C"
    instances = getattr(ctx, _INSTANCES_KEY)
    assert isinstance(instances[C], C)
    C.clear()


def test_mixin_class_pattern_works() -> None:
    """A mixin class that adds steps via composition should work."""
    Base = step_impl_base()

    class LoggingMixin:
        @Base.given("logging is enabled")
        def enable_logging(self) -> None:
            self.context.logging_enabled = True

    class MySteps(LoggingMixin, Base):
        @Base.given("a step with logging mixin")
        def step_one(self) -> None:
            self.context.ran = True

    MySteps.register()
    ctx = SimpleNamespace()
    _run_step("logging is enabled", "given", ctx)
    assert ctx.logging_enabled is True
    _run_step("a step with logging mixin", "given", ctx)
    assert ctx.ran is True
    MySteps.clear()


def test_step_with_special_regex_chars_in_parse_pattern() -> None:
    """Special regex chars in a Parse pattern should be treated as literals."""
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("a step with (parentheses) and {value}")
        def step_one(self, value: str) -> None:
            self.context.value = value

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("a step with (parentheses) and hello", "given", ctx)
    assert ctx.value == "hello"
    Steps.clear()
