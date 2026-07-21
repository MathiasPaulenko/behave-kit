"""`@data_driven` — run a step once per row of a data file.

Loads test data via `behave_kit.data.load_data` and executes the decorated
step function once for each row, injecting the row's keys as keyword
arguments (with ``-`` replaced by ``_`` for valid Python identifiers).
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from pathlib import Path
from typing import Any, Concatenate, ParamSpec, TypeVar, cast

from behave_kit._core.errors import BehaveKitError
from behave_kit._core.types import Context
from behave_kit.data.loader import load_examples_from

P = ParamSpec("P")
R = TypeVar("R")


def _sanitize_key(key: str) -> str:
    return key.replace("-", "_").replace(" ", "_")


def data_driven(
    path: str | Path,
) -> Callable[
    [Callable[Concatenate[Context, P], R]],
    Callable[Concatenate[Context, P], R],
]:
    """Decorator: run the step once per row in the data file at ``path``.

    Each row (a ``dict``) is unpacked as keyword arguments into the step
    function. Column names with hyphens or spaces are converted to valid
    Python identifiers (``-`` and `` `` → ``_``).

    Usage::

        @data_driven("tests/data/users.csv")
        @when("I login as {username}")
        def step(context, username=None, password=None): ...

    Raises:
        BehaveKitError: If the data file cannot be loaded or a row is not a
            dict.
    """
    data_path = Path(path)

    def decorator(
        func: Callable[Concatenate[Context, P], R],
    ) -> Callable[Concatenate[Context, P], R]:
        """Wrap ``func`` to execute once per data row."""

        @functools.wraps(func)
        def wrapper(context: Context, *args: P.args, **kwargs: P.kwargs) -> R:
            """Execute the step for each row in the data file."""
            rows = load_examples_from(data_path)
            if not rows:
                raise BehaveKitError(
                    f"No data rows found in '{data_path}'",
                    suggestion="Ensure the file contains at least one data row",
                )
            last_result: R | None = None
            for row in rows:
                if not isinstance(row, dict):
                    raise BehaveKitError(
                        f"Data row is {type(row).__name__}, expected dict",
                        suggestion="Ensure the data file contains rows of key-value pairs",
                    )
                row_kwargs: dict[str, Any] = {_sanitize_key(k): v for k, v in row.items()}
                merged = {**row_kwargs, **kwargs}
                last_result = func(context, *args, **merged)
            return cast("R", last_result)

        return cast("Callable[Concatenate[Context, P], R]", wrapper)

    return decorator
