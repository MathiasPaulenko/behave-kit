"""Unit tests for behave_kit.steps.classes (class-based step implementations)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from behave.matchers import RegexMatcher
from behave.step_registry import AmbiguousStep

from behave_kit._core.errors import StepError
from behave_kit.steps.classes import (
    _INSTANCES_KEY,
    _StepEntry,
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
    """Ensure each test starts and ends with a clean global step registry."""
    from behave.runner import the_step_registry

    saved = {kw: list(steps) for kw, steps in the_step_registry.steps.items()}
    yield
    for kw in the_step_registry.steps:
        the_step_registry.steps[kw] = saved.get(kw, [])


# --- step_impl_base ---


def test_step_impl_base_returns_distinct_bases() -> None:
    base_a = step_impl_base()
    base_b = step_impl_base()
    assert base_a is not base_b
    assert base_a is not base_b


def test_register_adds_steps_to_global_registry() -> None:
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("a class-based step for {value}")
        def step_one(self, value: str) -> None:
            self.context.value = value

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("a class-based step for hello", "given", ctx)
    assert ctx.value == "hello"
    Steps.clear()


def test_self_context_is_bound_automatically() -> None:
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("I set self dot context dot x to {value:d}")
        def step_set(self, value: int) -> None:
            self.context.x = value
            self._captured = value

        @Base.then("self dot context dot x should be {expected:d}")
        def step_check(self, expected: int) -> None:
            assert self.context.x == expected
            assert self._captured == expected

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("I set self dot context dot x to 42", "given", ctx)
    _run_step("self dot context dot x should be 42", "then", ctx)
    assert ctx.x == 42
    Steps.clear()


def test_instance_is_reused_within_a_scenario() -> None:
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("I record a call")
        def step_record(self) -> None:
            self.context.calls = getattr(self.context, "calls", 0) + 1

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("I record a call", "given", ctx)
    _run_step("I record a call", "given", ctx)
    instances = getattr(ctx, _INSTANCES_KEY)
    assert len(instances) == 1
    assert ctx.calls == 2
    Steps.clear()


def test_setup_hook_runs_once_per_scenario() -> None:
    Base = step_impl_base()
    setup_calls: list[str] = []

    class Steps(Base):
        def setup(self) -> None:
            setup_calls.append("setup")

        @Base.given("a step that triggers setup")
        def step_one(self) -> None:
            self.context.ready = True

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("a step that triggers setup", "given", ctx)
    _run_step("a step that triggers setup", "given", ctx)
    assert setup_calls == ["setup"]
    assert ctx.ready is True
    Steps.clear()


def test_teardown_hook_runs_via_teardown_steps() -> None:
    Base = step_impl_base()
    teardown_calls: list[str] = []

    class Steps(Base):
        @Base.given("a step that creates an instance")
        def step_one(self) -> None:
            self.context.alive = True

        def teardown(self) -> None:
            teardown_calls.append("teardown")

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("a step that creates an instance", "given", ctx)
    teardown_steps(ctx)
    assert teardown_calls == ["teardown"]
    # After teardown, instances are cleared
    assert getattr(ctx, _INSTANCES_KEY, {}) == {}
    Steps.clear()


def test_teardown_steps_is_noop_when_no_instances() -> None:
    ctx = SimpleNamespace()
    teardown_steps(ctx)  # should not raise


def test_teardown_steps_swallows_exceptions_in_hook() -> None:
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("a step")
        def step_one(self) -> None:
            pass

        def teardown(self) -> None:
            raise RuntimeError("boom")

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("a step", "given", ctx)
    # Should not raise
    teardown_steps(ctx)
    Steps.clear()


def test_register_is_idempotent() -> None:
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("an idempotent step {n:d}")
        def step_one(self, n: int) -> None:
            self.context.n = n

    Steps.register()
    Steps.register()  # second call should be a no-op
    ctx = SimpleNamespace()
    _run_step("an idempotent step 5", "given", ctx)
    assert ctx.n == 5
    Steps.clear()


def test_clear_removes_registered_steps() -> None:
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("a clearable step")
        def step_one(self) -> None:
            self.context.ran = True

    Steps.register()
    Steps.clear()
    from behave.runner import the_step_registry

    step = SimpleNamespace(name="a clearable step", step_type="given")
    match = the_step_registry.find_match(step)
    assert match is None


def test_clear_without_register_is_noop() -> None:
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("a never-registered step")
        def step_one(self) -> None:
            pass

    Steps.clear()  # should not raise


def test_subclass_override_is_used() -> None:
    Base = step_impl_base()

    class Parent(Base):
        @Base.given("an overridable step")
        def step_one(self) -> None:
            self.context.source = "parent"

    class Child(Parent):
        def step_one(self) -> None:
            self.context.source = "child"

    Child.register()
    ctx = SimpleNamespace()
    _run_step("an overridable step", "given", ctx)
    assert ctx.source == "child"
    Child.clear()


def test_subclass_adds_new_steps() -> None:
    Base = step_impl_base()

    class Parent(Base):
        @Base.given("a parent step")
        def parent_step(self) -> None:
            self.context.from_parent = True

    class Child(Parent):
        @Base.when("a child step")
        def child_step(self) -> None:
            self.context.from_child = True

    Child.register()
    ctx = SimpleNamespace()
    _run_step("a parent step", "given", ctx)
    _run_step("a child step", "when", ctx)
    assert ctx.from_parent is True
    assert ctx.from_child is True
    Child.clear()


def test_register_skips_steps_not_on_class() -> None:
    Base = step_impl_base()

    class SiblingA(Base):
        @Base.given("a step from sibling A")
        def step_a(self) -> None:
            self.context.from_a = True

    class SiblingB(Base):
        @Base.given("a step from sibling B")
        def step_b(self) -> None:
            self.context.from_b = True

    # Registering B should skip A's entry (step_a not on B).
    SiblingB.register()
    ctx = SimpleNamespace()
    _run_step("a step from sibling B", "given", ctx)
    assert ctx.from_b is True
    from behave.runner import the_step_registry

    match = the_step_registry.find_match(
        SimpleNamespace(name="a step from sibling A", step_type="given")
    )
    assert match is None  # step_a was skipped because SiblingB doesn't define it
    SiblingB.clear()


def test_per_step_matcher_with_regex() -> None:
    Base = step_impl_base()

    class Steps(Base):
        @Base.then(
            r"the value should be (less|greater) than (\d+)",
            matcher=RegexMatcher,
        )
        def compare(self, operator: str, amount: str) -> None:
            self.context.operator = operator
            self.context.amount = int(amount)

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("the value should be less than 100", "then", ctx)
    assert ctx.operator == "less"
    assert ctx.amount == 100
    Steps.clear()


def test_default_matcher_by_name() -> None:
    Base = step_impl_base(default_matcher="re")

    class Steps(Base):
        @Base.then(r"the regex value should be (\d+)")
        def check(self, value: str) -> None:
            self.context.value = int(value)

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("the regex value should be 99", "then", ctx)
    assert ctx.value == 99
    Steps.clear()


def test_unknown_matcher_name_raises() -> None:
    with pytest.raises(StepError, match="Unknown step matcher"):
        step_impl_base(default_matcher="nonexistent")


def test_invalid_matcher_type_raises() -> None:
    with pytest.raises(StepError, match="matcher must be"):
        step_impl_base(default_matcher=42)  # type: ignore[arg-type]


def test_ambiguous_step_raises() -> None:
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("a conflicting step")
        def step_one(self) -> None:
            pass

    Steps.register()
    # Re-add the same pattern via a different class to trigger AmbiguousStep
    OtherBase = step_impl_base()

    class OtherSteps(OtherBase):
        @OtherBase.given("a conflicting step")
        def step_one(self) -> None:
            pass

    with pytest.raises(AmbiguousStep):
        OtherSteps.register()
    Steps.clear()


def test_async_step_method_rejected() -> None:
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("an async step")
        async def step_one(self) -> None:  # type: ignore[unused-async]
            pass

    with pytest.raises(StepError, match="Async step method"):
        Steps.register()


def test_ambiguous_step_with_specific_matcher_raises() -> None:
    """AmbiguousStep is raised when two classes register the same pattern via a matcher class."""
    BaseA = step_impl_base()
    BaseB = step_impl_base()

    class StepsA(BaseA):
        @BaseA.given(r"a regex conflict step (\d+)", matcher=RegexMatcher)
        def step_one(self, value: str) -> None:
            pass

    class StepsB(BaseB):
        @BaseB.given(r"a regex conflict step (\d+)", matcher=RegexMatcher)
        def step_one(self, value: str) -> None:
            pass

    StepsA.register()
    with pytest.raises(AmbiguousStep):
        StepsB.register()
    StepsA.clear()


def test_given_when_then_step_decorators_all_work() -> None:
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("a given step")
        def g(self) -> None:
            self.context.g = True

        @Base.when("a when step")
        def w(self) -> None:
            self.context.w = True

        @Base.then("a then step")
        def t(self) -> None:
            self.context.t = True

        @Base.step("a generic step")
        def s(self) -> None:
            self.context.s = True

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("a given step", "given", ctx)
    _run_step("a when step", "when", ctx)
    _run_step("a then step", "then", ctx)
    _run_step("a generic step", "step", ctx)
    assert ctx.g and ctx.w and ctx.t and ctx.s
    Steps.clear()


def test_title_case_decorators_alias_lowercase() -> None:
    Base = step_impl_base()
    assert Base.Given is Base.given
    assert Base.When is Base.when
    assert Base.Then is Base.then
    assert Base.Step is Base.step


def test_step_entry_dataclass_fields() -> None:
    entry = _StepEntry("given", "pattern", "func", None)
    assert entry.keyword == "given"
    assert entry.pattern == "pattern"
    assert entry.func_name == "func"
    assert entry.matcher is None


def test_property_on_step_class_works() -> None:
    Base = step_impl_base()

    class Steps(Base):
        @property
        def balance(self) -> int:
            return getattr(self.context, "balance", 0)

        @balance.setter
        def balance(self, value: int) -> None:
            self.context.balance = value

        @Base.given("I have a balance of {amount:d}")
        def set_balance(self, amount: int) -> None:
            self.balance = amount

        @Base.then("the balance should be {expected:d}")
        def check_balance(self, expected: int) -> None:
            assert self.balance == expected

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("I have a balance of 100", "given", ctx)
    _run_step("the balance should be 100", "then", ctx)
    assert ctx.balance == 100
    Steps.clear()


def test_separate_bases_have_independent_registries() -> None:
    BaseA = step_impl_base()
    BaseB = step_impl_base()

    class StepsA(BaseA):
        @BaseA.given("a step from base A")
        def step_a(self) -> None:
            self.context.from_a = True

    class StepsB(BaseB):
        @BaseB.given("a step from base B")
        def step_b(self) -> None:
            self.context.from_b = True

    StepsA.register()
    StepsB.register()
    ctx = SimpleNamespace()
    _run_step("a step from base A", "given", ctx)
    _run_step("a step from base B", "given", ctx)
    assert ctx.from_a is True
    assert ctx.from_b is True
    StepsA.clear()
    StepsB.clear()


def test_user_init_with_defaults_works() -> None:
    Base = step_impl_base()

    class Steps(Base):
        def __init__(self, multiplier: int = 2) -> None:
            super().__init__()
            self.multiplier = multiplier

        @Base.given("I multiply {value:d}")
        def multiply(self, value: int) -> None:
            self.context.result = value * self.multiplier

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("I multiply 5", "given", ctx)
    assert ctx.result == 10
    Steps.clear()


# --- Additional coverage: dedup, re-registration, multi-class instances ---


def test_register_dedups_exact_same_matcher_object() -> None:
    """Re-adding the same matcher object via _add_matcher_to_registry is a no-op."""
    from behave.matchers import ParseMatcher

    from behave_kit.steps.classes import _add_matcher_to_registry, _StepEntry

    Base = step_impl_base()
    entry = _StepEntry("given", "a dedup step", "step_one", None)

    class Steps(Base):
        @Base.given("a dedup step")
        def step_one(self) -> None:
            self.context.ran = True

    matcher_obj = ParseMatcher(Steps.step_one, "a dedup step", step_type="given")
    # First add — should return the matcher.
    added = _add_matcher_to_registry(entry, matcher_obj)
    assert added is matcher_obj
    # Second add of the exact same object — should dedup and return None.
    added_again = _add_matcher_to_registry(entry, matcher_obj)
    assert added_again is None
    # Clean up the registry.
    from behave.runner import the_step_registry

    the_step_registry.steps["given"].remove(matcher_obj)


def test_register_dedups_same_pattern_and_location() -> None:
    """Two distinct matcher objects with same pattern + location are deduped."""
    from behave.matchers import ParseMatcher

    from behave_kit.steps.classes import _add_matcher_to_registry, _StepEntry

    Base = step_impl_base()
    entry = _StepEntry("given", "a location-dedup step", "step_one", None)

    class Steps(Base):
        @Base.given("a location-dedup step")
        def step_one(self) -> None:
            pass

    # Two distinct matcher objects wrapping the same function — same location.
    matcher_a = ParseMatcher(Steps.step_one, "a location-dedup step", step_type="given")
    matcher_b = ParseMatcher(Steps.step_one, "a location-dedup step", step_type="given")
    assert matcher_a is not matcher_b
    assert matcher_a.location == matcher_b.location

    added_a = _add_matcher_to_registry(entry, matcher_a)
    assert added_a is matcher_a
    # Same pattern + same location — should dedup.
    added_b = _add_matcher_to_registry(entry, matcher_b)
    assert added_b is None

    from behave.runner import the_step_registry

    the_step_registry.steps["given"].remove(matcher_a)


def test_clear_is_idempotent() -> None:
    """Calling clear() twice is a no-op."""
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("a clearable step for idempotent clear")
        def step_one(self) -> None:
            pass

    Steps.register()
    Steps.clear()
    Steps.clear()  # should not raise


def test_reregister_after_clear_works() -> None:
    """A class can be registered again after clear()."""
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("a re-registerable step")
        def step_one(self) -> None:
            self.context.ran = True

    Steps.register()
    Steps.clear()
    # Re-registering after clear should work and re-add the step.
    Steps.register()
    ctx = SimpleNamespace()
    _run_step("a re-registerable step", "given", ctx)
    assert ctx.ran is True
    Steps.clear()


def test_two_classes_get_separate_instances_per_scenario() -> None:
    """Each class gets its own instance; state doesn't leak between classes."""
    Base = step_impl_base()

    class StepsA(Base):
        @Base.given("class A sets its flag")
        def step_a(self) -> None:
            self.flag = "a"

        @Base.then("class A flag should be a")
        def check_a(self) -> None:
            assert self.flag == "a"

    class StepsB(Base):
        @Base.given("class B sets its flag")
        def step_b(self) -> None:
            self.flag = "b"

        @Base.then("class B flag should be b")
        def check_b(self) -> None:
            assert self.flag == "b"

    StepsA.register()
    StepsB.register()
    ctx = SimpleNamespace()
    _run_step("class A sets its flag", "given", ctx)
    _run_step("class B sets its flag", "given", ctx)
    _run_step("class A flag should be a", "then", ctx)
    _run_step("class B flag should be b", "then", ctx)
    instances = getattr(ctx, _INSTANCES_KEY)
    assert len(instances) == 2
    assert instances[StepsA].flag == "a"
    assert instances[StepsB].flag == "b"
    StepsA.clear()
    StepsB.clear()


def test_setup_runs_once_per_class_per_scenario() -> None:
    """With multiple classes, each setup() runs once when its first step runs."""
    Base = step_impl_base()
    setup_log: list[str] = []

    class StepsA(Base):
        def setup(self) -> None:
            setup_log.append("A")

        @Base.given("trigger A setup")
        def step_a(self) -> None:
            pass

    class StepsB(Base):
        def setup(self) -> None:
            setup_log.append("B")

        @Base.given("trigger B setup")
        def step_b(self) -> None:
            pass

    StepsA.register()
    StepsB.register()
    ctx = SimpleNamespace()
    _run_step("trigger A setup", "given", ctx)
    _run_step("trigger A setup", "given", ctx)
    _run_step("trigger B setup", "given", ctx)
    _run_step("trigger B setup", "given", ctx)
    assert setup_log == ["A", "B"]
    StepsA.clear()
    StepsB.clear()


def test_teardown_runs_for_all_classes() -> None:
    """teardown_steps calls teardown() on every live instance."""
    Base = step_impl_base()
    teardown_log: list[str] = []

    class StepsA(Base):
        @Base.given("a step from A for teardown")
        def step_a(self) -> None:
            pass

        def teardown(self) -> None:
            teardown_log.append("A")

    class StepsB(Base):
        @Base.given("a step from B for teardown")
        def step_b(self) -> None:
            pass

        def teardown(self) -> None:
            teardown_log.append("B")

    StepsA.register()
    StepsB.register()
    ctx = SimpleNamespace()
    _run_step("a step from A for teardown", "given", ctx)
    _run_step("a step from B for teardown", "given", ctx)
    teardown_steps(ctx)
    assert sorted(teardown_log) == ["A", "B"]
    StepsA.clear()
    StepsB.clear()


def test_step_method_receives_positional_args_for_unnamed_groups() -> None:
    """Unnamed regex groups are passed as positional args."""
    Base = step_impl_base()

    class Steps(Base):
        @Base.then(r"the value should be (less|greater) than (\d+)", matcher=RegexMatcher)
        def compare(self, operator: str, amount: str) -> None:
            self.context.operator = operator
            self.context.amount = int(amount)

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("the value should be less than 50", "then", ctx)
    assert ctx.operator == "less"
    assert ctx.amount == 50
    Steps.clear()


def test_step_method_can_return_a_value() -> None:
    """The wrapper propagates the step method's return value."""
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("a step that returns {value:d}")
        def step_one(self, value: int) -> int:
            return value * 2

    Steps.register()
    from behave.runner import the_step_registry

    step = SimpleNamespace(name="a step that returns 21", step_type="given")
    match = the_step_registry.find_match(step)
    assert match is not None
    ctx = SimpleNamespace()
    result = match.func(ctx, 21)
    assert result == 42
    Steps.clear()


def test_default_matcher_with_class_object() -> None:
    """default_matcher accepts a Matcher subclass, not just a name string."""
    from behave.matchers import RegexMatcher

    Base = step_impl_base(default_matcher=RegexMatcher)

    class Steps(Base):
        @Base.then(r"a regex default matcher step (\d+)")
        def step_one(self, value: str) -> None:
            self.context.value = int(value)

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("a regex default matcher step 77", "then", ctx)
    assert ctx.value == 77
    Steps.clear()


def test_per_step_matcher_overrides_default_matcher() -> None:
    """A per-step matcher overrides the base's default_matcher."""
    from behave.matchers import ParseMatcher, RegexMatcher

    Base = step_impl_base(default_matcher=ParseMatcher)

    class Steps(Base):
        @Base.then("a parse default step {value:d}")
        def parse_step(self, value: int) -> None:
            self.context.parse_value = value

        @Base.then(r"a regex override step (\d+)", matcher=RegexMatcher)
        def regex_step(self, value: str) -> None:
            self.context.regex_value = int(value)

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("a parse default step 10", "then", ctx)
    _run_step("a regex override step 20", "then", ctx)
    assert ctx.parse_value == 10
    assert ctx.regex_value == 20
    Steps.clear()


def test_self_context_is_same_object_as_step_context() -> None:
    """self.context must be the exact same object passed to the wrapper."""
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("a step that captures its context")
        def step_one(self) -> None:
            self.context.captured_self_context = self.context

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("a step that captures its context", "given", ctx)
    assert ctx.captured_self_context is ctx
    Steps.clear()


def test_instances_dict_is_created_on_first_use() -> None:
    """The first step call creates the instances dict on context."""
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("a step that creates the instances dict")
        def step_one(self) -> None:
            pass

    Steps.register()
    ctx = SimpleNamespace()
    assert getattr(ctx, _INSTANCES_KEY, None) is None
    _run_step("a step that creates the instances dict", "given", ctx)
    assert hasattr(ctx, _INSTANCES_KEY)
    assert isinstance(getattr(ctx, _INSTANCES_KEY), dict)
    Steps.clear()


def test_teardown_steps_clears_instances_even_when_hook_raises() -> None:
    """Instances are cleared even if a teardown hook raises."""
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("a step before a raising teardown")
        def step_one(self) -> None:
            pass

        def teardown(self) -> None:
            raise RuntimeError("boom")

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("a step before a raising teardown", "given", ctx)
    assert len(getattr(ctx, _INSTANCES_KEY)) == 1
    teardown_steps(ctx)  # should not raise
    assert getattr(ctx, _INSTANCES_KEY, {}) == {}
    Steps.clear()


def test_super_call_in_subclass_works() -> None:
    """A subclass method can call super() to extend parent behavior."""
    Base = step_impl_base()

    class Parent(Base):
        @Base.given("a parent value of {value:d}")
        def set_value(self, value: int) -> None:
            self.context.value = value
            self.context.parent_called = True

    class Child(Parent):
        def set_value(self, value: int) -> None:
            super().set_value(value)
            self.context.child_called = True
            self.context.value *= 2

    Child.register()
    ctx = SimpleNamespace()
    _run_step("a parent value of 5", "given", ctx)
    assert ctx.parent_called is True
    assert ctx.child_called is True
    assert ctx.value == 10  # doubled by child
    Child.clear()


def test_init_with_required_args_raises_at_step_call() -> None:
    """A class whose __init__ requires args fails when the instance is created."""
    Base = step_impl_base()

    class Steps(Base):
        def __init__(self, required: int) -> None:
            super().__init__()
            self.required = required

        @Base.given("a step requiring init args")
        def step_one(self) -> None:
            pass

    Steps.register()
    ctx = SimpleNamespace()
    with pytest.raises(TypeError):
        _run_step("a step requiring init args", "given", ctx)
    Steps.clear()


def test_step_keyword_works_with_find_match() -> None:
    """The generic 'step' keyword registers under the 'step' bucket."""
    Base = step_impl_base()

    class Steps(Base):
        @Base.step("a generic step for find_match")
        def step_one(self) -> None:
            self.context.generic_ran = True

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("a generic step for find_match", "step", ctx)
    assert ctx.generic_ran is True
    Steps.clear()


def test_no_setup_hook_means_no_setup_call() -> None:
    """If a class doesn't define setup(), the base's no-op runs silently."""
    Base = step_impl_base()
    setup_calls: list[str] = []

    class Steps(Base):
        @Base.given("a step without a setup hook")
        def step_one(self) -> None:
            pass

    # No setup() override — the base's no-op should run without error.
    Steps.register()
    ctx = SimpleNamespace()
    _run_step("a step without a setup hook", "given", ctx)
    assert setup_calls == []
    Steps.clear()


def test_no_teardown_hook_means_no_teardown_call() -> None:
    """If a class doesn't override teardown(), the default no-op runs silently."""
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("a step without a teardown hook")
        def step_one(self) -> None:
            pass

    # No teardown() override — the base's no-op should run without error.
    Steps.register()
    ctx = SimpleNamespace()
    _run_step("a step without a teardown hook", "given", ctx)
    teardown_steps(ctx)  # should not raise
    assert getattr(ctx, _INSTANCES_KEY, {}) == {}
    Steps.clear()


def test_step_entry_equality_and_repr() -> None:
    """_StepEntry is a dataclass with sensible defaults."""
    entry_a = _StepEntry("given", "pattern", "func", None)
    entry_b = _StepEntry("given", "pattern", "func", None)
    assert entry_a == entry_b
    entry_c = _StepEntry("given", "other", "func", None)
    assert entry_a != entry_c


def test_registration_record_default_is_empty_list() -> None:
    """_RegistrationRecord defaults to an empty matchers list."""
    from behave_kit.steps.classes import _RegistrationRecord

    record = _RegistrationRecord()
    assert record.matchers == []
    # Each instance gets its own list (not shared).
    record2 = _RegistrationRecord()
    record.matchers.append("x")
    assert record2.matchers == []
