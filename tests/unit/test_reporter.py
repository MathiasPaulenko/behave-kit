"""Tests for behave_kit.assertions.reporter."""

from behave_kit.assertions.reporter import SoftAssertReport, SoftFailure


def test_empty_report_str_says_none() -> None:
    report = SoftAssertReport()
    assert str(report) == "Soft assertion failures (0): none"
    assert report.failure_count == 0
    assert not report.has_failures


def test_report_with_failures_lists_messages() -> None:
    report = SoftAssertReport(
        failures=[
            SoftFailure(message="first"),
            SoftFailure(message="second"),
        ]
    )
    text = str(report)
    assert "Soft assertion failures (2)" in text
    assert "1. first" in text
    assert "2. second" in text
    assert report.has_failures


def test_report_with_values_shows_expected_and_got() -> None:
    report = SoftAssertReport(failures=[SoftFailure(message="mismatch", expected=2, actual=1)])
    text = str(report)
    assert "Expected: 2, Got: 1" in text


def test_soft_failure_without_values_has_no_values() -> None:
    failure = SoftFailure(message="just a message")
    assert not failure.has_values


def test_soft_failure_with_only_expected_has_values() -> None:
    failure = SoftFailure(message="missing", expected=42)
    assert failure.has_values
