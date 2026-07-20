"""Exception hierarchy shared across behave-kit.

Every public function that can fail raises a subclass of `BehaveKitError`
with an actionable message: what happened, why (cause), and what to do
about it (suggestion).
"""

from __future__ import annotations


class BehaveKitError(Exception):
    """Base exception for all behave-kit errors."""

    def __init__(
        self,
        message: str,
        *,
        cause: BaseException | None = None,
        suggestion: str | None = None,
    ) -> None:
        self.message = message
        self.cause = cause
        self.suggestion = suggestion
        super().__init__(self._format())

    def _format(self) -> str:
        msg = self.message
        if self.suggestion:
            msg += f"\n  Suggestion: {self.suggestion}"
        return msg


class ConfigError(BehaveKitError):
    """Raised when `behave.toml` is invalid or a profile cannot be found."""


class EnvVarError(BehaveKitError):
    """Raised when a required environment variable is missing or invalid."""


class FixtureError(BehaveKitError):
    """Raised when a fixture is missing or has a circular dependency."""


class DataLoadError(BehaveKitError):
    """Raised when test data cannot be loaded (missing file, bad format, missing dependency)."""


class ScopeError(BehaveKitError):
    """Raised when a `TypedContext` attribute is accessed or set without being declared."""


class StepError(BehaveKitError):
    """Raised when a step is ambiguous or a parameter type is invalid."""
