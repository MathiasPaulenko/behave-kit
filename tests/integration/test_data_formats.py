"""Integration tests for real CSV/JSON/YAML/XLSX data loading."""

import json
from pathlib import Path

import pytest

from behave_kit._core.errors import DataLoadError
from behave_kit.data import loader


def test_csv_real_file(tmp_path: Path) -> None:
    path = tmp_path / "users.csv"
    path.write_text("name,age\nalice,30\n", encoding="utf-8")
    assert loader.load_data(path) == [{"name": "alice", "age": "30"}]


def test_json_real_file(tmp_path: Path) -> None:
    path = tmp_path / "data.json"
    path.write_text(json.dumps([{"id": 1}, {"id": 2}]), encoding="utf-8")
    assert loader.load_data(path) == [{"id": 1}, {"id": 2}]


def test_yaml_real_file_with_pyyaml(tmp_path: Path) -> None:
    path = tmp_path / "data.yaml"
    path.write_text("key: value\nnested:\n  a: 1\n", encoding="utf-8")
    assert loader.load_data(path) == {"key": "value", "nested": {"a": 1}}


def test_yaml_without_pyyaml_raises_with_extra_hint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "data.yaml"
    path.write_text("key: value\n", encoding="utf-8")
    monkeypatch.setattr(loader.compat, "HAS_YAML", False)
    with pytest.raises(DataLoadError, match=r"behave-kit\[yaml\]"):
        loader.load_data(path)


def test_xlsx_real_file_with_openpyxl(tmp_path: Path) -> None:
    openpyxl = pytest.importorskip("openpyxl")
    path = tmp_path / "data.xlsx"
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(["name", "age"])
    sheet.append(["alice", 30])
    workbook.save(path)
    assert loader.load_data(path) == [{"name": "alice", "age": 30}]


def test_xlsx_without_openpyxl_raises_with_extra_hint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "data.xlsx"
    path.write_bytes(b"placeholder")
    monkeypatch.setattr(loader.compat, "HAS_OPENPYXL", False)
    with pytest.raises(DataLoadError, match=r"behave-kit\[excel\]"):
        loader.load_data(path)
