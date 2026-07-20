"""Tests for behave_kit.data.loader."""

import json
from pathlib import Path

import pytest

from behave_kit._core.errors import DataLoadError
from behave_kit.data.loader import load_data, load_examples_from


def test_load_data_dispatches_csv(tmp_path: Path) -> None:
    path = tmp_path / "users.csv"
    path.write_text("name,age\nalice,30\nbob,25\n", encoding="utf-8")
    result = load_data(path)
    assert result == [{"name": "alice", "age": "30"}, {"name": "bob", "age": "25"}]


def test_load_data_dispatches_json(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"key": "value"}), encoding="utf-8")
    assert load_data(path) == {"key": "value"}


def test_load_data_file_not_found_raises(tmp_path: Path) -> None:
    with pytest.raises(DataLoadError, match="not found"):
        load_data(tmp_path / "missing.csv")


def test_load_data_unsupported_extension_raises(tmp_path: Path) -> None:
    path = tmp_path / "data.txt"
    path.write_text("irrelevant", encoding="utf-8")
    with pytest.raises(DataLoadError, match="Unsupported"):
        load_data(path)


def test_load_examples_from_normalizes_list(tmp_path: Path) -> None:
    path = tmp_path / "users.csv"
    path.write_text("name\nalice\nbob\n", encoding="utf-8")
    result = load_examples_from(path)
    assert result == [{"name": "alice"}, {"name": "bob"}]


def test_load_examples_from_normalizes_dict(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"key": "value"}), encoding="utf-8")
    assert load_examples_from(path) == [{"key": "value"}]
