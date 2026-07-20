"""Tag-based fixtures with lifecycle and dependency resolution."""

from __future__ import annotations

from behave_kit.fixtures.manager import FixtureManager
from behave_kit.fixtures.registry import fixture

__all__ = [
    "fixture",
    "FixtureManager",
]
