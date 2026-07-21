"""Integration tests for class-based steps wired through the kit facade."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import behave_kit as bk
from behave_kit.steps.classes import _INSTANCES_KEY, step_impl_base


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
    yield
    for kw in the_step_registry.steps:
        the_step_registry.steps[kw] = saved.get(kw, [])


def test_step_impl_base_exposed_on_facade() -> None:
    assert callable(bk.step_impl_base)
    assert callable(bk.teardown_steps)


def test_all_includes_new_exports() -> None:
    assert "step_impl_base" in bk.__all__
    assert "teardown_steps" in bk.__all__


def test_cherry_pick_imports_work() -> None:
    from behave_kit import step_impl_base as sib
    from behave_kit import teardown_steps as ts

    assert callable(sib)
    assert callable(ts)


def test_teardown_via_kit_calls_step_teardown() -> None:
    """``bk.teardown(context)`` must call ``teardown()`` on live step instances."""
    Base = step_impl_base()
    teardown_calls: list[str] = []

    class Steps(Base):
        @Base.given("an integration step")
        def step_one(self) -> None:
            self.context.ran = True

        def teardown(self) -> None:
            teardown_calls.append("teardown")

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("an integration step", "given", ctx)
    # No _behave_kit_wired needed — teardown_steps runs regardless.
    bk.teardown(ctx)
    assert teardown_calls == ["teardown"]
    assert getattr(ctx, _INSTANCES_KEY, {}) == {}
    Steps.clear()


def test_teardown_without_setup_is_safe() -> None:
    ctx = SimpleNamespace()
    # Should not raise even though setup() was never called.
    bk.teardown(ctx)


def test_full_lifecycle_with_setup_and_teardown_hooks() -> None:
    """Exercise setup() + step + teardown() through the kit's teardown()."""
    Base = step_impl_base()
    lifecycle: list[str] = []

    class Steps(Base):
        def setup(self) -> None:
            lifecycle.append("setup")
            self.context.counter = 0

        @Base.given("I increment the counter")
        def increment(self) -> None:
            self.context.counter += 1

        @Base.then("the counter should be {expected:d}")
        def check(self, expected: int) -> None:
            assert self.context.counter == expected
            lifecycle.append(f"checked={self.context.counter}")

        def teardown(self) -> None:
            lifecycle.append("teardown")

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("I increment the counter", "given", ctx)
    _run_step("I increment the counter", "given", ctx)
    _run_step("the counter should be 2", "then", ctx)
    bk.teardown(ctx)
    assert lifecycle == ["setup", "checked=2", "teardown"]
    Steps.clear()


def test_independent_bases_do_not_cross_register() -> None:
    BaseA = step_impl_base()
    BaseB = step_impl_base()

    class StepsA(BaseA):
        @BaseA.given("an isolated step from A")
        def step_a(self) -> None:
            self.context.a = True

    class StepsB(BaseB):
        @BaseB.given("an isolated step from B")
        def step_b(self) -> None:
            self.context.b = True

    StepsA.register()
    StepsB.register()
    ctx = SimpleNamespace()
    _run_step("an isolated step from A", "given", ctx)
    _run_step("an isolated step from B", "given", ctx)
    assert ctx.a is True and ctx.b is True
    StepsA.clear()
    StepsB.clear()


def test_subclass_extension_with_per_step_matcher_integration() -> None:
    from behave.matchers import RegexMatcher

    Base = step_impl_base()

    class Library(Base):
        @Base.given("a library balance of {amount:d}")
        def set_balance(self, amount: int) -> None:
            self.context.balance = amount

        @Base.when("I withdraw {amount:d}")
        def withdraw(self, amount: int) -> None:
            self.context.balance -= amount

    class Extended(Library):
        def withdraw(self, amount: int) -> None:
            if amount > self.context.balance:
                raise ValueError("Insufficient funds")
            super().withdraw(amount)

        @Base.then(
            r"the balance should be (less|greater) than (\d+)",
            matcher=RegexMatcher,
        )
        def compare(self, operator: str, amount: str) -> None:
            value = int(amount)
            if operator == "less":
                assert self.context.balance < value
            else:
                assert self.context.balance > value

    Extended.register()
    ctx = SimpleNamespace()
    _run_step("a library balance of 100", "given", ctx)
    _run_step("I withdraw 30", "when", ctx)
    _run_step("the balance should be less than 1000", "then", ctx)
    assert ctx.balance == 70
    bk.teardown(ctx)
    Extended.clear()


# --- Coexistence with other behave-kit features ---


def test_class_based_steps_coexist_with_soft_asserts() -> None:
    """A class-based step can use soft asserts via the kit's collector."""
    from behave_kit.assertions.soft import assert_soft, use_soft_asserts

    Base = step_impl_base()

    class Steps(Base):
        def setup(self) -> None:
            use_soft_asserts(self.context)

        @Base.given("a soft-asserting class step with value {value:d}")
        def step_one(self, value: int) -> None:
            assert_soft(value > 0, "value should be positive")
            assert_soft(value < 100, "value should be under 100")

        def teardown(self) -> None:
            collector = getattr(self.context, "_behave_kit_soft", None)
            if collector is not None:
                self.context.soft_report = collector.report()

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("a soft-asserting class step with value 50", "given", ctx)
    bk.teardown(ctx)
    # Both soft asserts passed — report should have 0 failures.
    assert ctx.soft_report.failure_count == 0
    Steps.clear()


def test_class_based_steps_coexist_with_scoped_cleanup() -> None:
    """A class-based step can register scoped resources cleaned up by teardown()."""
    cleanup_log: list[str] = []

    @bk.scoped("resource")
    def make_resource(context: object) -> str:
        cleanup_log.append("created")
        return "resource-value"

    Base = step_impl_base()

    class Steps(Base):
        @Base.given("a class step creates a scoped resource")
        def step_one(self) -> None:
            self.context.resource = make_resource(self.context)

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("a class step creates a scoped resource", "given", ctx)
    assert ctx.resource == "resource-value"
    bk.teardown(ctx)
    # Scoped cleanup runs during teardown().
    assert "created" in cleanup_log
    Steps.clear()


def test_setup_and_teardown_wired_via_kit_facade() -> None:
    """bk.setup() + bk.teardown() run class-based setup/teardown hooks."""
    Base = step_impl_base()
    lifecycle: list[str] = []

    class Steps(Base):
        def setup(self) -> None:
            lifecycle.append("setup")

        @Base.given("a wired step")
        def step_one(self) -> None:
            lifecycle.append("step")

        def teardown(self) -> None:
            lifecycle.append("teardown")

    Steps.register()
    ctx = SimpleNamespace()
    bk.setup(ctx)
    _run_step("a wired step", "given", ctx)
    bk.teardown(ctx)
    assert lifecycle == ["setup", "step", "teardown"]
    Steps.clear()


def test_teardown_safe_to_call_multiple_times() -> None:
    """Calling bk.teardown() twice does not raise and is a no-op the second time."""
    Base = step_impl_base()
    teardown_count: list[int] = []

    class Steps(Base):
        @Base.given("a step for double teardown")
        def step_one(self) -> None:
            pass

        def teardown(self) -> None:
            teardown_count.append(1)

    Steps.register()
    ctx = SimpleNamespace()
    _run_step("a step for double teardown", "given", ctx)
    bk.teardown(ctx)
    bk.teardown(ctx)  # no-op — instances already cleared
    assert len(teardown_count) == 1
    Steps.clear()


def test_multiple_class_based_libraries_coexist() -> None:
    """Two independent step libraries (separate bases) work in the same scenario."""
    BaseA = step_impl_base()
    BaseB = step_impl_base()

    class LibraryA(BaseA):
        @BaseA.given("library A does something")
        def step_a(self) -> None:
            self.context.from_a = "a"

    class LibraryB(BaseB):
        @BaseB.given("library B does something else")
        def step_b(self) -> None:
            self.context.from_b = "b"

    LibraryA.register()
    LibraryB.register()
    ctx = SimpleNamespace()
    _run_step("library A does something", "given", ctx)
    _run_step("library B does something else", "given", ctx)
    assert ctx.from_a == "a"
    assert ctx.from_b == "b"
    # Each class gets its own instance.
    instances = getattr(ctx, _INSTANCES_KEY)
    assert LibraryA in instances
    assert LibraryB in instances
    assert instances[LibraryA] is not instances[LibraryB]
    bk.teardown(ctx)
    LibraryA.clear()
    LibraryB.clear()


def test_class_based_and_function_based_steps_coexist() -> None:
    """Class-based steps work alongside Behave's function-based decorators."""
    from behave import given as behave_given  # type: ignore[import-not-found]

    Base = step_impl_base()

    class ClassSteps(Base):
        @Base.given("a class-based step for coexistence")
        def step_one(self) -> None:
            self.context.from_class = True

    ClassSteps.register()

    @behave_given("a function-based step for coexistence")
    def function_step(context: object) -> None:
        context.from_function = True

    try:
        ctx = SimpleNamespace()
        _run_step("a class-based step for coexistence", "given", ctx)
        _run_step("a function-based step for coexistence", "given", ctx)
        assert ctx.from_class is True
        assert ctx.from_function is True
        bk.teardown(ctx)
    finally:
        ClassSteps.clear()
        # Remove the function-based step from the registry.
        from behave.runner import the_step_registry

        for matcher in list(the_step_registry.steps["given"]):
            if getattr(matcher.func, "__name__", None) == "function_step":
                the_step_registry.steps["given"].remove(matcher)


def test_per_scenario_isolation_across_two_contexts() -> None:
    """Two contexts (simulating two scenarios) get independent instances."""
    Base = step_impl_base()

    class Steps(Base):
        @Base.given("a step that stores a value {value:d}")
        def step_one(self, value: int) -> None:
            self.context.stored = value

    Steps.register()
    ctx1 = SimpleNamespace()
    ctx2 = SimpleNamespace()
    _run_step("a step that stores a value 10", "given", ctx1)
    _run_step("a step that stores a value 20", "given", ctx2)
    assert ctx1.stored == 10
    assert ctx2.stored == 20
    # Tearing down ctx1 must not affect ctx2.
    bk.teardown(ctx1)
    assert getattr(ctx1, _INSTANCES_KEY, {}) == {}
    assert len(getattr(ctx2, _INSTANCES_KEY)) == 1
    bk.teardown(ctx2)
    Steps.clear()


def test_teardown_steps_directly_exposed_on_facade() -> None:
    """bk.teardown_steps is the same function as the module-level one."""
    from behave_kit.steps.classes import teardown_steps as module_ts

    assert bk.teardown_steps is module_ts


def test_step_impl_base_directly_exposed_on_facade() -> None:
    """bk.step_impl_base is the same function as the module-level one."""
    from behave_kit.steps.classes import step_impl_base as module_sib

    assert bk.step_impl_base is module_sib
