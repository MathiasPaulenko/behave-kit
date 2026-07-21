"""Shared type aliases and extension Protocols.

Extension points (custom loaders, skip conditions, diff matchers, fixtures)
are defined as `Protocol` classes. Anything that structurally satisfies the
Protocol can be registered — no base-class inheritance required.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from behave.runner import Context as Context
else:
    try:
        from behave.runner import Context as Context
    except ImportError:  # pragma: no cover - behave is a required dependency
        Context = object  # type: ignore[assignment,misc]

StepPattern = str


class Scope(Enum):
    """Lifetime of a registered item (fixture, scoped attribute, cached data)."""

    SCENARIO = "scenario"
    FEATURE = "feature"
    GLOBAL = "global"


@runtime_checkable
class DataLoader(Protocol):
    """Loads test data from a file into a Python object."""

    def load(self, path: Path) -> object:
        """Load and return the data stored at ``path``.

        Args:
            path: Path to the data file.

        Returns:
            The loaded data as a Python object.
        """
        ...


@runtime_checkable
class SkipCondition(Protocol):
    """Decides whether a step or scenario should be skipped."""

    def should_skip(self, context: Context) -> bool:
        """Return ``True`` if the step/scenario should be skipped.

        Args:
            context: Behave context for the current scenario.

        Returns:
            Whether the condition to skip is met.
        """
        ...


@runtime_checkable
class DiffMatcher(Protocol):
    """Compares two values of a specific type and reports differences."""

    def matches(self, actual: object, expected: object) -> object:
        """Compare ``actual`` against ``expected`` and return a diff result.

        Args:
            actual: Value produced by the code under test.
            expected: Expected value.

        Returns:
            An object describing the comparison (e.g. ``True`` if equal, or
            a structured diff otherwise).
        """
        ...


@runtime_checkable
class FixtureFn(Protocol):
    """Sets up a resource for a scenario/feature and tears it down afterwards."""

    def __call__(self, context: Context) -> object:
        """Create and return the fixture resource for ``context``.

        Args:
            context: Behave context for the current scenario.

        Returns:
            The resource managed by this fixture.
        """
        ...

    def teardown(self, context: Context, resource: object) -> None:
        """Clean up the ``resource`` produced by this fixture.

        Args:
            context: Behave context for the current scenario.
            resource: Object returned by ``__call__``.
        """
        ...
