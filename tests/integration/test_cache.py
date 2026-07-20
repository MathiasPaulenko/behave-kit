"""Integration tests for behave_kit.data.cache."""

from behave_kit._core.types import Scope
from behave_kit.data.cache import DataCache


def test_cache_miss_returns_none() -> None:
    cache = DataCache()
    assert cache.get("users.csv") is None


def test_cache_hit_returns_stored_data() -> None:
    cache = DataCache()
    cache.set("users.csv", Scope.SCENARIO, [{"name": "alice"}])
    assert cache.get("users.csv", Scope.SCENARIO) == [{"name": "alice"}]


def test_cache_distinguishes_by_scope() -> None:
    cache = DataCache()
    cache.set("users.csv", Scope.SCENARIO, "scenario-data")
    cache.set("users.csv", Scope.FEATURE, "feature-data")
    assert cache.get("users.csv", Scope.SCENARIO) == "scenario-data"
    assert cache.get("users.csv", Scope.FEATURE) == "feature-data"


def test_invalidate_clears_only_matching_scope() -> None:
    cache = DataCache()
    cache.set("users.csv", Scope.SCENARIO, "scenario-data")
    cache.set("users.csv", Scope.FEATURE, "feature-data")
    cache.invalidate(Scope.SCENARIO)
    assert cache.get("users.csv", Scope.SCENARIO) is None
    assert cache.get("users.csv", Scope.FEATURE) == "feature-data"


def test_cache_path_normalization_mixed_string_and_path() -> None:
    from pathlib import Path

    cache = DataCache()
    cache.set(Path("a/b.csv"), Scope.SCENARIO, [1, 2, 3])
    assert cache.get("a/b.csv", Scope.SCENARIO) == [1, 2, 3]
