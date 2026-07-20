"""Integration tests for behave_kit.fixtures.manager."""

from types import SimpleNamespace

import pytest

from behave_kit._core.errors import FixtureError
from behave_kit._core.types import Scope
from behave_kit.fixtures import FixtureManager, fixture


def test_setup_by_tag_runs_matching_fixture() -> None:
    @fixture("tag_setup_test_1")
    def my_fixture(context: SimpleNamespace) -> None:
        context.db = "connected"

    manager = FixtureManager()
    context = SimpleNamespace()
    scenario = SimpleNamespace(tags=["tag_setup_test_1"])
    manager.setup_for_scenario(context, scenario)
    assert context.db == "connected"
    manager.teardown_scenario(context)


def test_setup_with_dependency_order() -> None:
    call_order: list[str] = []

    @fixture("dep_order_test_base")
    def base(context: SimpleNamespace) -> None:
        call_order.append("base")

    @fixture("dep_order_test_child", requires="dep_order_test_base")
    def child(context: SimpleNamespace) -> None:
        call_order.append("child")

    manager = FixtureManager()
    context = SimpleNamespace()
    scenario = SimpleNamespace(tags=["dep_order_test_child"])
    manager.setup_for_scenario(context, scenario)
    assert call_order == ["base", "child"]
    manager.teardown_scenario(context)


def test_teardown_runs_in_reverse_order() -> None:
    teardown_order: list[str] = []

    @fixture("reverse_test_a")
    def fixture_a(context: SimpleNamespace) -> tuple:
        def setup(ctx: SimpleNamespace) -> None:
            ctx.a = True

        def teardown(ctx: SimpleNamespace) -> None:
            teardown_order.append("a")

        return setup, teardown

    @fixture("reverse_test_b", requires="reverse_test_a")
    def fixture_b(context: SimpleNamespace) -> tuple:
        def setup(ctx: SimpleNamespace) -> None:
            ctx.b = True

        def teardown(ctx: SimpleNamespace) -> None:
            teardown_order.append("b")

        return setup, teardown

    manager = FixtureManager()
    context = SimpleNamespace()
    scenario = SimpleNamespace(tags=["reverse_test_b"])
    manager.setup_for_scenario(context, scenario)
    manager.teardown_scenario(context)
    assert teardown_order == ["b", "a"]


def test_feature_scope_setup_and_teardown() -> None:
    @fixture("feature_scope_test_1", scope=Scope.FEATURE)
    def my_fixture(context: SimpleNamespace) -> tuple:
        def setup(ctx: SimpleNamespace) -> None:
            ctx.server = "running"

        def teardown(ctx: SimpleNamespace) -> None:
            ctx.server = "stopped"

        return setup, teardown

    manager = FixtureManager()
    context = SimpleNamespace()
    feature = SimpleNamespace(tags=["feature_scope_test_1"])
    manager.setup_for_feature(context, feature)
    assert context.server == "running"
    manager.teardown_feature(context)
    assert context.server == "stopped"


def test_scenario_teardown_does_not_touch_feature_fixtures() -> None:
    @fixture("isolation_test_feature", scope=Scope.FEATURE)
    def feature_fixture(context: SimpleNamespace) -> tuple:
        def setup(ctx: SimpleNamespace) -> None:
            ctx.feature_data = "set"

        def teardown(ctx: SimpleNamespace) -> None:
            ctx.feature_data = "cleared"

        return setup, teardown

    manager = FixtureManager()
    context = SimpleNamespace()
    feature = SimpleNamespace(tags=["isolation_test_feature"])
    manager.setup_for_feature(context, feature)

    scenario = SimpleNamespace(tags=[])
    manager.setup_for_scenario(context, scenario)
    manager.teardown_scenario(context)
    assert context.feature_data == "set"

    manager.teardown_feature(context)
    assert context.feature_data == "cleared"


def test_multiple_fixtures_same_scenario() -> None:
    @fixture("multi_test_x")
    def fixture_x(context: SimpleNamespace) -> None:
        context.x = True

    @fixture("multi_test_y")
    def fixture_y(context: SimpleNamespace) -> None:
        context.y = True

    manager = FixtureManager()
    context = SimpleNamespace()
    scenario = SimpleNamespace(tags=["multi_test_x", "multi_test_y"])
    manager.setup_for_scenario(context, scenario)
    assert context.x is True
    assert context.y is True
    manager.teardown_scenario(context)


def test_fixture_not_found_raises_with_suggestion() -> None:
    @fixture("similar_name_test_2", requires="similar_name_tes")
    def my_fixture(context: SimpleNamespace) -> None:
        pass

    @fixture("similar_name_test_2_base")
    def base_fixture(context: SimpleNamespace) -> None:
        pass

    manager = FixtureManager()
    context = SimpleNamespace()
    scenario = SimpleNamespace(tags=["similar_name_test_2"])
    with pytest.raises(FixtureError, match="not found"):
        manager.setup_for_scenario(context, scenario)


def test_tag_without_matching_fixture_is_ignored() -> None:
    manager = FixtureManager()
    context = SimpleNamespace()
    scenario = SimpleNamespace(tags=["non_fixture_tag"])
    manager.setup_for_scenario(context, scenario)
    manager.teardown_scenario(context)
