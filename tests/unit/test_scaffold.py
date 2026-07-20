"""Sanity checks for the project scaffolding."""

import behave_kit


def test_package_imports() -> None:
    assert behave_kit is not None


def test_version_is_defined() -> None:
    assert isinstance(behave_kit.__version__, str)
    assert behave_kit.__version__ != ""
