"""Tests for the public facade ``behave_kit`` package."""

from __future__ import annotations

import behave_kit as bk


def test_namespace_import_exposes_core_api() -> None:
    assert callable(bk.assert_soft)
    assert callable(bk.env)
    assert callable(bk.load_data)
    assert callable(bk.setup)
    assert callable(bk.teardown)
    assert callable(bk.fixture)
    assert callable(bk.skip_if_env)
    assert callable(bk.parameter_type)
    assert callable(bk.when_if)
    assert callable(bk.use_soft_asserts)
    assert callable(bk.dump_context)
    assert callable(bk.dump_context_on_failure)
    assert callable(bk.scoped)
    assert bk.TypedContext is not None
    assert bk.KitConfig is not None


def test_cherry_pick_imports_work() -> None:
    from behave_kit import (
        KitConfig,
        TypedContext,
        assert_dict_contains,
        assert_json_equals,
        assert_list_ordered,
        assert_soft,
        assert_soft_equals,
        assert_soft_is_none,
        assert_soft_true,
        assert_table_equals,
        data_provider,
        dump_context,
        dump_context_on_failure,
        env,
        fixture,
        load_data,
        load_examples_from,
        parameter_type,
        scoped,
        setup,
        skip_if_env,
        skip_if_missing,
        skip_if_no_browser,
        skip_on_os,
        soft_asserts,
        teardown,
        use_soft_asserts,
        when_if,
    )

    assert callable(assert_soft)
    assert callable(assert_json_equals)
    assert callable(assert_dict_contains)
    assert callable(assert_list_ordered)
    assert callable(assert_table_equals)
    assert callable(assert_soft_equals)
    assert callable(assert_soft_true)
    assert callable(assert_soft_is_none)
    assert callable(soft_asserts)
    assert callable(use_soft_asserts)
    assert TypedContext is not None
    assert callable(dump_context)
    assert callable(dump_context_on_failure)
    assert callable(scoped)
    assert callable(skip_if_env)
    assert callable(skip_on_os)
    assert callable(skip_if_missing)
    assert callable(skip_if_no_browser)
    assert callable(env)
    assert KitConfig is not None
    assert callable(load_data)
    assert callable(load_examples_from)
    assert callable(data_provider)
    assert callable(parameter_type)
    assert callable(when_if)
    assert callable(fixture)
    assert callable(setup)
    assert callable(teardown)


def test_all_is_complete() -> None:
    expected = {
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
        # context
        "TypedContext",
        "dump_context",
        "dump_context_on_failure",
        "scoped",
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
        # steps
        "parameter_type",
        "when_if",
        # fixtures
        "fixture",
        # hooks
        "setup",
        "teardown",
    }
    assert set(bk.__all__) == expected


def test_version_is_string() -> None:
    assert isinstance(bk.__version__, str)
    assert bk.__version__ != ""
