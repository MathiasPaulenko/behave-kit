"""`temp_workspace` — isolated temporary directory for filesystem tests.

Creates a temporary directory, changes the working directory into it, and
restores both on exit. Useful for tests that create or read files without
polluting the project tree.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory


@contextmanager
def temp_workspace(
    *,
    prefix: str = "behave_kit_",
) -> Iterator[Path]:
    """Yield a temporary directory and restore the CWD on exit.

    Args:
        prefix: Prefix for the temporary directory name.

    Yields:
        ``Path`` to the temporary directory (the CWD while inside the block).
    """
    original_cwd = Path.cwd()
    with TemporaryDirectory(prefix=prefix) as tmp_name:
        tmp_path = Path(tmp_name)
        os.chdir(tmp_path)
        try:
            yield tmp_path
        finally:
            os.chdir(original_cwd)
