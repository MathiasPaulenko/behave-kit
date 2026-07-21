"""`env_snapshot` — save and restore environment variables.

Context manager that snapshots ``os.environ`` on entry and restores it on
exit, so tests that set environment variables do not leak state.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager


@contextmanager
def env_snapshot() -> Iterator[None]:
    """Snapshot ``os.environ`` and restore it on exit.

    Any additions, modifications, or deletions made to environment variables
    inside the block are reverted when the block exits — even if an exception
    is raised.
    """
    snapshot = dict(os.environ)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(snapshot)
