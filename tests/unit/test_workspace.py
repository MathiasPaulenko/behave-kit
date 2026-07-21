"""Tests for behave_kit.workspace."""

from pathlib import Path

from behave_kit.workspace import temp_workspace


def test_temp_workspace_creates_and_yields_directory() -> None:
    with temp_workspace() as tmp:
        assert tmp.is_dir()
        assert tmp.exists()
        assert Path.cwd() == tmp


def test_temp_workspace_restores_cwd_on_exit() -> None:
    original = Path.cwd()
    with temp_workspace():
        assert Path.cwd() != original
    assert Path.cwd() == original


def test_temp_workspace_restores_cwd_on_exception() -> None:
    original = Path.cwd()
    try:
        with temp_workspace():
            raise ValueError("boom")
    except ValueError:
        pass
    assert Path.cwd() == original


def test_temp_workspace_cleans_up_by_default() -> None:
    with temp_workspace() as tmp:
        pass
    assert not tmp.exists()


def test_temp_workspace_can_create_files() -> None:
    with temp_workspace() as tmp:
        file_path = tmp / "test.txt"
        file_path.write_text("hello")
        assert file_path.read_text() == "hello"
