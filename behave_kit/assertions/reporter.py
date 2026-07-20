"""Formatting of collected soft-assertion failures into legible output."""

from __future__ import annotations

from dataclasses import dataclass, field

_UNSET = object()


@dataclass(frozen=True)
class SoftFailure:
    """A single soft assertion failure."""

    message: str
    expected: object = _UNSET
    actual: object = _UNSET

    @property
    def has_values(self) -> bool:
        return self.expected is not _UNSET or self.actual is not _UNSET


@dataclass(frozen=True)
class SoftAssertReport:
    """Aggregated report of every soft assertion failure in a scenario."""

    failures: list[SoftFailure] = field(default_factory=list)

    @property
    def failure_count(self) -> int:
        return len(self.failures)

    @property
    def has_failures(self) -> bool:
        return bool(self.failures)

    def __str__(self) -> str:
        if not self.failures:
            return "Soft assertion failures (0): none"
        lines = [f"Soft assertion failures ({len(self.failures)}):"]
        for index, failure in enumerate(self.failures, start=1):
            lines.append(f"  {index}. {failure.message}")
            if failure.has_values:
                expected = None if failure.expected is _UNSET else failure.expected
                actual = None if failure.actual is _UNSET else failure.actual
                lines.append(f"     Expected: {expected!r}, Got: {actual!r}")
        return "\n".join(lines)
