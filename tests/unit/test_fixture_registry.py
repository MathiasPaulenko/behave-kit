"""Tests for behave_kit.fixtures.registry."""

from types import SimpleNamespace

import pytest

from behave_kit._core.errors import FixtureError
from behave_kit._core.types import Scope
from behave_kit.fixtures.registry import (
    fixture,
    fixture_names,
    fixture_scope,
    get_fixture,
    resolve_fixture_order,
)


def test_register_simple_fixture() -> None:
    @fixture("simple_test_1")
    def my_fixture(context: SimpleNamespace) -> None:
        context.value = "set"

    factory = get_fixture("simple_test_1")
    context = SimpleNamespace()
    factory(context)
    assert context.value == "set"


def test_register_fixture_with_teardown() -> None:
    @fixture("teardown_test_1")
    def my_fixture(context: SimpleNamespace) -> tuple:
        def setup(ctx: SimpleNamespace) -> None:
            ctx.db = "connected"

        def teardown(ctx: SimpleNamespace) -> None:
            ctx.db = "disconnected"

        return setup, teardown

    context = SimpleNamespace()
    factory = get_fixture("teardown_test_1")
    result = factory(context)
    assert result is not None
    setup_fn, teardown_fn = result
    setup_fn(context)
    assert context.db == "connected"
    teardown_fn(context)
    assert context.db == "disconnected"


def test_register_fixture_with_requires() -> None:
    @fixture("dep_test_1_base")
    def base(context: SimpleNamespace) -> None:
        context.base = True

    @fixture("dep_test_1_child", requires="dep_test_1_base")
    def child(context: SimpleNamespace) -> None:
        context.child = True

    order = resolve_fixture_order("dep_test_1_child")
    assert order == ["dep_test_1_base", "dep_test_1_child"]


def test_register_fixture_with_requires_list() -> None:
    @fixture("multi_dep_test_a")
    def dep_a(context: SimpleNamespace) -> None:
        context.a = True

    @fixture("multi_dep_test_b")
    def dep_b(context: SimpleNamespace) -> None:
        context.b = True

    @fixture("multi_dep_test_c", requires=["multi_dep_test_a", "multi_dep_test_b"])
    def dep_c(context: SimpleNamespace) -> None:
        context.c = True

    order = resolve_fixture_order("multi_dep_test_c")
    assert "multi_dep_test_a" in order
    assert "multi_dep_test_b" in order
    assert order.index("multi_dep_test_a") < order.index("multi_dep_test_c")
    assert order.index("multi_dep_test_b") < order.index("multi_dep_test_c")


def test_register_duplicate_name_raises() -> None:
    @fixture("dup_fixture_test")
    def first(context: SimpleNamespace) -> None:
        pass

    with pytest.raises(FixtureError):

        @fixture("dup_fixture_test")
        def second(context: SimpleNamespace) -> None:
            pass


def test_get_missing_fixture_raises() -> None:
    with pytest.raises(FixtureError):
        get_fixture("nonexistent_fixture_xyz")


def test_circular_dependency_raises() -> None:
    @fixture("circular_test_a", requires="circular_test_b")
    def fixture_a(context: SimpleNamespace) -> None:
        pass

    @fixture("circular_test_b", requires="circular_test_a")
    def fixture_b(context: SimpleNamespace) -> None:
        pass

    with pytest.raises(FixtureError, match="Circular"):
        resolve_fixture_order("circular_test_a")


def test_fixture_scope_returns_registered_scope() -> None:
    @fixture("scope_test_feature", scope=Scope.FEATURE)
    def my_fixture(context: SimpleNamespace) -> None:
        pass

    assert fixture_scope("scope_test_feature") == Scope.FEATURE


def test_fixture_names_filtered_by_scope() -> None:
    @fixture("names_test_scenario")
    def scenario_fixture(context: SimpleNamespace) -> None:
        pass

    @fixture("names_test_feature", scope=Scope.FEATURE)
    def feature_fixture(context: SimpleNamespace) -> None:
        pass

    scenario_names = fixture_names(Scope.SCENARIO)
    feature_names = fixture_names(Scope.FEATURE)
    assert "names_test_scenario" in scenario_names
    assert "names_test_feature" not in scenario_names
    assert "names_test_feature" in feature_names
