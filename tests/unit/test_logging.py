"""Tests for behave_kit._core.logging."""

import logging

from behave_kit._core.logging import get_logger


def test_get_logger_returns_namespaced_logger() -> None:
    logger = get_logger("assertions")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "behave_kit.assertions"


def test_get_logger_returns_same_instance_for_same_name() -> None:
    assert get_logger("fixtures") is get_logger("fixtures")
