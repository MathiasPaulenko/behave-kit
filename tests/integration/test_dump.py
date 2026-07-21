"""Integration tests for behave_kit.context.dump."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from behave_kit.context.dump import dump_context, dump_context_on_failure


def test_dump_context_writes_json(tmp_path: Path) -> None:
    context = SimpleNamespace(user="alice", count=3, scenario=SimpleNamespace(name="login test"))
    output_file = dump_context(context, path=tmp_path)
    assert output_file.exists()
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data["user"] == "alice"
    assert data["count"] == 3


def test_dump_context_skips_non_serializable_with_warning(tmp_path: Path) -> None:
    class Unserializable:
        pass

    context = SimpleNamespace(user="alice", driver=Unserializable())
    output_file = dump_context(context, path=tmp_path)
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert "user" in data
    assert "driver" not in data


def test_dump_context_creates_output_directory(tmp_path: Path) -> None:
    target_dir = tmp_path / "nested" / "debug"
    context = SimpleNamespace(user="alice")
    dump_context(context, path=target_dir)
    assert target_dir.exists()


def test_dump_context_on_failure_dumps_when_failed(tmp_path: Path) -> None:
    context = SimpleNamespace(user="alice")
    scenario = SimpleNamespace(status="failed", name="failing scenario")
    output_file = dump_context_on_failure(context, scenario, path=tmp_path)
    assert output_file is not None
    assert output_file.exists()


def test_dump_context_on_failure_skips_when_passed(tmp_path: Path) -> None:
    context = SimpleNamespace(user="alice")
    scenario = SimpleNamespace(status="passed", name="passing scenario")
    output_file = dump_context_on_failure(context, scenario, path=tmp_path)
    assert output_file is None
    assert not any(tmp_path.iterdir())


def test_dump_context_merges_behave_style_stack_layers(tmp_path: Path) -> None:
    context = SimpleNamespace(
        _stack=[
            {"user": "override", "@layer": "scenario"},
            {"user": "base", "base_url": "https://x.com", "@layer": "feature"},
        ]
    )
    output_file = dump_context(context, path=tmp_path)
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data["user"] == "override"
    assert data["base_url"] == "https://x.com"
    assert "@layer" not in data


def test_dump_context_tolerates_non_string_attribute_names(tmp_path: Path) -> None:
    context = SimpleNamespace(user="alice")
    context.__dict__[1] = "value"
    output_file = dump_context(context, path=tmp_path)
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data["user"] == "alice"
    assert "1" not in data


def test_dump_context_rejects_existing_non_directory_path(tmp_path: Path) -> None:
    from behave_kit._core.errors import BehaveKitError

    context = SimpleNamespace(user="alice")
    file_path = tmp_path / "not_a_dir.json"
    file_path.write_text("{}", encoding="utf-8")
    with pytest.raises(BehaveKitError, match="not a directory"):
        dump_context(context, path=file_path)


def test_dump_context_with_no_stack_falls_back_to_vars(tmp_path: Path) -> None:
    """When ``context._stack`` is None, dump falls back to ``vars(context)``."""
    context = SimpleNamespace(user="alice")
    assert getattr(context, "_stack", None) is None
    output_file = dump_context(context, path=tmp_path)
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data["user"] == "alice"


def test_dump_context_with_empty_stack_dumps_no_user_attrs(tmp_path: Path) -> None:
    """An empty ``_stack`` yields no user attributes (vars fallback is skipped)."""
    context = SimpleNamespace(_stack=[], user="alice")
    output_file = dump_context(context, path=tmp_path)
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data == {}


def test_dump_context_on_failure_with_status_enum_name(tmp_path: Path) -> None:
    """Status objects exposing a `.name` attribute are also handled."""
    context = SimpleNamespace(user="alice")
    scenario = SimpleNamespace(status=SimpleNamespace(name="failed"), name="enum status")
    output_file = dump_context_on_failure(context, scenario, path=tmp_path)
    assert output_file is not None
    assert output_file.exists()


def test_dump_context_skips_private_and_at_layer_keys(tmp_path: Path) -> None:
    context = SimpleNamespace(
        _stack=[
            {"user": "alice", "_private": "secret", "@layer": "scenario", "public": 1},
        ]
    )
    output_file = dump_context(context, path=tmp_path)
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert "user" in data
    assert "public" in data
    assert "_private" not in data
    assert "@layer" not in data


def test_dump_context_skips_non_string_keys_in_stack(tmp_path: Path) -> None:
    context = SimpleNamespace(_stack=[{1: "value", "user": "alice"}])
    output_file = dump_context(context, path=tmp_path)
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data == {"user": "alice"}
