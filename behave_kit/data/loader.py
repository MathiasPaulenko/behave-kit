"""Multi-format test data loading: CSV, JSON, YAML, XLSX.

Each format loader raises `DataLoadError` (never a bare parser or file-system
exception) with a suggestion naming the missing optional dependency or the
invalid path.
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
    try:
        if not path.is_file():
            raise DataLoadError(
                f"Data file not found or is not a file: {path}",
                suggestion="Check the path is correct and relative to the working directory",
            )
    except OSError as exc:
        raise DataLoadError(
            f"Data file not found or is not a file: {path}",
            cause=exc,
            suggestion="Check the path is correct and relative to the working directory",
        ) from exc


def _load_csv(path: Path) -> list[dict[str, Any]]:
    _require_file(path)
    try:
        with path.open(newline="", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    except csv.Error as exc:
        raise DataLoadError(
            f"Cannot parse CSV '{path}': {exc}",
            cause=exc,
            suggestion="Check the file uses valid CSV syntax and encoding",
        ) from exc
    except OSError as exc:
        raise DataLoadError(
            f"Cannot read CSV '{path}': {exc}",
            cause=exc,
            suggestion="Check file permissions and encoding",
        ) from exc


def _load_json(path: Path) -> dict[str, Any] | list[Any]:
    _require_file(path)
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise DataLoadError(
            f"Cannot parse JSON '{path}': {exc}",
            cause=exc,
            suggestion="Check the file is valid JSON",
        ) from exc
    except OSError as exc:
        raise DataLoadError(
            f"Cannot read JSON '{path}': {exc}",
            cause=exc,
            suggestion="Check file permissions",
        ) from exc
    if data is None:
        raise DataLoadError(
            f"JSON file '{path}' is empty or contains null",
            suggestion="Provide a JSON object or array",
        )
    return data  # type: ignore[no-any-return]


def _load_yaml(path: Path) -> dict[str, Any] | list[Any]:
    _require_file(path)
    if not compat.HAS_YAML:
        raise DataLoadError(
            f"Cannot load '{path}': PyYAML is not installed",
            suggestion="pip install behave-kit[yaml]",
        )
    import yaml

    try:
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise DataLoadError(
            f"Cannot parse YAML '{path}': {exc}",
            cause=exc,
            suggestion="Check the file is valid YAML",
        ) from exc
    except OSError as exc:
        raise DataLoadError(
            f"Cannot read YAML '{path}': {exc}",
            cause=exc,
            suggestion="Check file permissions",
        ) from exc
    if data is None:
        raise DataLoadError(
            f"YAML file '{path}' is empty or contains null",
            suggestion="Provide a YAML mapping or list",
        )
    return data  # type: ignore[no-any-return]


def _load_xlsx(path: Path) -> list[dict[str, Any]]:
    _require_file(path)
    if not compat.HAS_OPENPYXL:
        raise DataLoadError(
            f"Cannot load '{path}': openpyxl is not installed",
            suggestion="pip install behave-kit[excel]",
        )
    import openpyxl

    try:
        workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    except OSError as exc:
        raise DataLoadError(
            f"Cannot read Excel file '{path}': {exc}",
            cause=exc,
            suggestion="Check file permissions",
        ) from exc
    except Exception as exc:
        raise DataLoadError(
            f"Cannot parse Excel file '{path}': {exc}",
            cause=exc,
            suggestion="Check the file is a valid .xlsx workbook",
        ) from exc

    sheet = workbook.active
    if sheet is None:
        raise DataLoadError(
            f"Excel workbook '{path}' has no active worksheet",
            suggestion="Create a workbook with at least one visible worksheet",
        )

    try:
        rows_iter = sheet.iter_rows(values_only=True)
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
}


def load_data(path: str | Path) -> dict[str, Any] | list[Any]:
    """Load ``path`` and return its parsed content, dispatched by extension.

    Raises:
        DataLoadError: if the file is missing, the extension is unsupported,
            or a required optional dependency (``pyyaml``, ``openpyxl``) is
            not installed.
    """
    file_path = Path(path)
    _require_file(file_path)
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
    if not isinstance(data, list):
        data = [data]
    if not all(isinstance(item, dict) for item in data):
        raise DataLoadError(f"Cannot normalize data from {path} into a list of dicts")
    return data
