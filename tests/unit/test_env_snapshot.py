"""Tests for behave_kit.env.snapshot."""

import os

from behave_kit.env.snapshot import env_snapshot


def test_env_snapshot_restores_on_exit() -> None:
    os.environ["BK_SNAPSHOT_TEST"] = "before"
    with env_snapshot():
        os.environ["BK_SNAPSHOT_TEST"] = "during"
        os.environ["BK_NEW_VAR"] = "new"
    assert os.environ["BK_SNAPSHOT_TEST"] == "before"
    assert "BK_NEW_VAR" not in os.environ


def test_env_snapshot_restores_deleted_var() -> None:
    os.environ["BK_SNAPSHOT_DELETE"] = "keep"
    with env_snapshot():
        del os.environ["BK_SNAPSHOT_DELETE"]
    assert os.environ["BK_SNAPSHOT_DELETE"] == "keep"


def test_env_snapshot_restores_on_exception() -> None:
    os.environ["BK_SNAPSHOT_EXC"] = "before"
    try:
        with env_snapshot():
            os.environ["BK_SNAPSHOT_EXC"] = "during"
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    assert os.environ["BK_SNAPSHOT_EXC"] == "before"


def test_env_snapshot_no_changes_preserves_state() -> None:
    os.environ["BK_SNAPSHOT_NOOP"] = "unchanged"
    with env_snapshot():
        pass
    assert os.environ["BK_SNAPSHOT_NOOP"] == "unchanged"
