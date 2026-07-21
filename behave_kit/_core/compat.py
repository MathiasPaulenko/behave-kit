"""Runtime compatibility detection: interpreter/behave versions and optional deps.

Never installs anything automatically — only exposes boolean flags so callers
can raise an actionable error naming the missing extra.
"""

from __future__ import annotations

import sys

PYTHON_VERSION: tuple[int, int, int] = sys.version_info[:3]

try:
    import behave

    BEHAVE_VERSION: str | None = getattr(behave, "__version__", None)
except ImportError:  # pragma: no cover - behave is a required dependency
    BEHAVE_VERSION = None

try:
    import yaml  # noqa: F401

    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    import openpyxl  # noqa: F401

    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

try:
    import dotenv  # noqa: F401

    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False
