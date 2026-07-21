"""Tests for behave_kit.steps.data_driven."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from behave_kit._core.errors import BehaveKitError
from behave_kit.steps.data_driven import data_driven


def test_data_driven_runs_once_per_row(tmp_path: Path) -> None:
    csv_file = tmp_path / "users.csv"
    csv_file.write_text("username,password\nalice,secret\nbob,pass\n", encoding="utf-8")

    calls: list[dict[str, str]] = []

    @data_driven(csv_file)
    def step(context: object, **kwargs: str) -> None:
        calls.append(kwargs)

    step(SimpleNamespace())
    assert len(calls) == 2
    assert calls[0]["username"] == "alice"
    assert calls[0]["password"] == "secret"
    assert calls[1]["username"] == "bob"


def test_data_driven_sanitizes_column_names(tmp_path: Path) -> None:
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("user-name,pass word\nalice,secret\n", encoding="utf-8")

    calls: list[dict[str, str]] = []

    @data_driven(csv_file)
    def step(context: object, **kwargs: str) -> None:
        calls.append(kwargs)

    step(SimpleNamespace())
    assert "user_name" in calls[0]
    assert "pass_word" in calls[0]


def test_data_driven_with_json(tmp_path: Path) -> None:
    json_file = tmp_path / "items.json"
    json_file.write_text(json.dumps([{"id": "1"}, {"id": "2"}]))

    ids: list[str] = []

    @data_driven(json_file)
    def step(context: object, **kwargs: str) -> None:
        ids.append(kwargs["id"])

    step(SimpleNamespace())
    assert ids == ["1", "2"]


def test_data_driven_missing_file_raises(tmp_path: Path) -> None:
    @data_driven(tmp_path / "nonexistent.csv")
    def step(context: object, **kwargs: str) -> None:
        pass

    with pytest.raises(BehaveKitError):
        step(SimpleNamespace())


def test_data_driven_returns_last_result(tmp_path: Path) -> None:
    csv_file = tmp_path / "vals.csv"
    csv_file.write_text("val\n10\n20\n", encoding="utf-8")

    @data_driven(csv_file)
    def step(context: object, **kwargs: str) -> int:
        return int(kwargs["val"])

    result = step(SimpleNamespace())
    assert result == 20


def test_data_driven_empty_file_raises(tmp_path: Path) -> None:
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("username,password\n", encoding="utf-8")

    @data_driven(csv_file)
    def step(context: object, **kwargs: str) -> None:
        pass

    with pytest.raises(BehaveKitError, match="No data rows"):
        step(SimpleNamespace())
