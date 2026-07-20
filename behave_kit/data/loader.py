"""Multi-format test data loading: CSV, JSON, YAML, XLSX.

Each format loader raises `DataLoadError` (never a bare `ImportError` or
`FileNotFoundError`) with a suggestion naming the missing optional
dependency or the invalid path.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from behave_kit._core import compat
from behave_kit._core.errors import DataLoadError


def _require_file(path: Path) -> None:
    if not path.exists():
        raise DataLoadError(
            f"Data file not found: {path}",
            suggestion="Check the path is correct and relative to the working directory",
        )


def _load_csv(path: Path) -> list[dict[str, Any]]:
    _require_file(path)
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _load_json(path: Path) -> dict[str, Any] | list[Any]:
    _require_file(path)
    with path.open(encoding="utf-8") as f:
        return json.load(f)  # type: ignore[no-any-return]


def _load_yaml(path: Path) -> dict[str, Any] | list[Any]:
    _require_file(path)
    if not compat.HAS_YAML:
        raise DataLoadError(
            f"Cannot load '{path}': PyYAML is not installed",
            suggestion="pip install behave-kit[yaml]",
        )
    import yaml

    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)  # type: ignore[no-any-return]


def _load_xlsx(path: Path) -> list[dict[str, Any]]:
    _require_file(path)
    if not compat.HAS_OPENPYXL:
        raise DataLoadError(
            f"Cannot load '{path}': openpyxl is not installed",
            suggestion="pip install behave-kit[excel]",
        )
    import openpyxl

    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheet = workbook.active
    rows_iter = sheet.iter_rows(values_only=True)
    try:
        headers = [str(header) for header in next(rows_iter)]
    except StopIteration:
        return []
    return [dict(zip(headers, row, strict=False)) for row in rows_iter]


_LOADERS: dict[str, Callable[[Path], dict[str, Any] | list[Any]]] = {
    ".csv": _load_csv,
    ".json": _load_json,
    ".yaml": _load_yaml,
    ".yml": _load_yaml,
    ".xlsx": _load_xlsx,
    ".xls": _load_xlsx,
}


def load_data(path: str | Path) -> dict[str, Any] | list[Any]:
    """Load ``path`` and return its parsed content, dispatched by extension.

    Raises:
        DataLoadError: if the file is missing, the extension is unsupported,
            or a required optional dependency (``pyyaml``, ``openpyxl``) is
            not installed.
    """
    file_path = Path(path)
    loader = _LOADERS.get(file_path.suffix.lower())
    if loader is None:
        raise DataLoadError(
            f"Unsupported file extension '{file_path.suffix}' for {file_path}",
            suggestion=f"Supported extensions: {', '.join(sorted(_LOADERS))}",
        )
    return loader(file_path)


def load_examples_from(path: str | Path) -> list[dict[str, Any]]:
    """Load ``path`` and normalize the result to a list of dicts."""
    data = load_data(path)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    raise DataLoadError(f"Cannot normalize data from {path} into a list of dicts")
