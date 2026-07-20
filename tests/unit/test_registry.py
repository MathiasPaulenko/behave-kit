"""Tests for behave_kit._core.registry."""

import pytest

from behave_kit._core.errors import FixtureError
from behave_kit._core.registry import Registry
from behave_kit._core.types import Scope


def test_register_and_get() -> None:
    registry: Registry[int] = Registry()
    registry.register("answer", 42)
    assert registry.get("answer") == 42


def test_register_duplicate_name_raises() -> None:
    registry: Registry[int] = Registry()
    registry.register("answer", 42)
    with pytest.raises(FixtureError):
        registry.register("answer", 43)


def test_get_missing_raises() -> None:
    registry: Registry[int] = Registry()
    with pytest.raises(FixtureError):
        registry.get("missing")


def test_scope_defaults_to_scenario() -> None:
    registry: Registry[int] = Registry()
    registry.register("answer", 42)
    assert registry.scope_of("answer") == Scope.SCENARIO


def test_names_filtered_by_scope() -> None:
    registry: Registry[str] = Registry()
    registry.register("browser", "chrome", scope=Scope.SCENARIO)
    registry.register("database", "postgres", scope=Scope.FEATURE)
    assert set(registry.names()) == {"browser", "database"}
    assert registry.names(scope=Scope.SCENARIO) == ["browser"]
    assert registry.names(scope=Scope.FEATURE) == ["database"]


def test_resolve_dependencies_simple_chain() -> None:
    registry: Registry[str] = Registry()
    registry.register("browser", "chrome")
    registry.register("logged_in", "session", requires=["browser"])
    order = registry.resolve_dependencies("logged_in")
    assert order == ["browser", "logged_in"]


def test_resolve_dependencies_no_deps() -> None:
    registry: Registry[str] = Registry()
    registry.register("browser", "chrome")
    assert registry.resolve_dependencies("browser") == ["browser"]


def test_resolve_dependencies_missing_dependency_raises() -> None:
    registry: Registry[str] = Registry()
    registry.register("logged_in", "session", requires=["browser"])
    with pytest.raises(FixtureError):
        registry.resolve_dependencies("logged_in")


def test_resolve_dependencies_detects_circular() -> None:
    registry: Registry[str] = Registry()
    registry.register("a", "A", requires=["b"])
    registry.register("b", "B", requires=["a"])
    with pytest.raises(FixtureError):
        registry.resolve_dependencies("a")


def test_resolve_dependencies_diamond() -> None:
    registry: Registry[str] = Registry()
    registry.register("base", "B")
    registry.register("left", "L", requires=["base"])
    registry.register("right", "R", requires=["base"])
    registry.register("top", "T", requires=["left", "right"])
    order = registry.resolve_dependencies("top")
    assert order.index("base") < order.index("left")
    assert order.index("base") < order.index("right")
    assert order.index("left") < order.index("top")
    assert order.index("right") < order.index("top")
    assert order[-1] == "top"
