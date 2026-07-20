"""behave-kit — utilities for robust Behave test suites.

Three adoption levels:

1. **Automatic wiring** — ``behave_kit.setup(context)`` in ``before_all``.
2. **Cherry-pick** — ``from behave_kit.assertions import assert_soft``.
3. **Namespace** — ``import behave_kit as bk; bk.assert_soft(...)``.
"""

from __future__ import annotations

__version__ = "1.0.0"

from behave_kit._core.types import Scope
from behave_kit.assertions import (
    CompareOptions,
    assert_dict_contains,
    assert_json_equals,
    assert_list_ordered,
    assert_soft,
    assert_soft_equals,
    assert_soft_is_none,
    assert_soft_true,
    assert_table_equals,
    deep_compare,
    soft_asserts,
    use_soft_asserts,
)
from behave_kit.context import (
    TypedContext,
    cleanup_scoped,
    dump_context,
    dump_context_on_failure,
    scoped,
)
from behave_kit.data import DataCache, data_provider, get_provider, load_data, load_examples_from
from behave_kit.env import KitConfig, env
from behave_kit.fixtures import fixture
from behave_kit.hooks import setup, teardown
from behave_kit.skip import skip_if_env, skip_if_missing, skip_if_no_browser, skip_on_os
from behave_kit.steps import (
    convert,
    parameter_type,
    register_builtin_types,
    setup_suggestions,
    when_if,
)

__all__ = [
    "__version__",
    # assertions
    "assert_soft",
    "assert_soft_equals",
    "assert_soft_true",
    "assert_soft_is_none",
    "assert_json_equals",
    "assert_dict_contains",
    "assert_list_ordered",
    "assert_table_equals",
    "soft_asserts",
    "use_soft_asserts",
    "CompareOptions",
    "deep_compare",
    # context
    "TypedContext",
    "dump_context",
    "dump_context_on_failure",
    "scoped",
    "cleanup_scoped",
    # skip
    "skip_if_env",
    "skip_on_os",
    "skip_if_missing",
    "skip_if_no_browser",
    # env
    "env",
    "KitConfig",
    # data
    "load_data",
    "load_examples_from",
    "data_provider",
    "get_provider",
    "DataCache",
    # steps
    "parameter_type",
    "convert",
    "register_builtin_types",
    "setup_suggestions",
    "when_if",
    # fixtures
    "fixture",
    "Scope",
    # hooks
    "setup",
    "teardown",
]
