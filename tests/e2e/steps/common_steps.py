"""E2E step implementations using behave-kit — dogfooding."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from behave import given, then, when  # type: ignore[import-not-found]

from behave_kit import (
    TypedContext,
    assert_soft,
    env,
    fixture,
    load_data,
    use_soft_asserts,
)
from behave_kit._core.errors import EnvVarError, ScopeError

# --- Soft asserts steps ---


@given("I have a soft assert collector active")
def step_activate_soft_asserts(context: object) -> None:
    use_soft_asserts(context)


@when('I assert that "{value}" is soft-true')
def step_assert_soft_true(context: object, value: str) -> None:
    assert_soft(value == "True", f"Expected True, got {value}")


@when('I assert that "{value}" is soft-true with message "{message}"')
def step_assert_soft_true_with_message(context: object, value: str, message: str) -> None:
    assert_soft(value == "True", message)


@then("the soft assert collector should have {count:d} failures")
def step_check_failure_count(context: object, count: int) -> None:
    collector = context._behave_kit_soft
    report = collector.report()
    actual = len(report.failures)
    assert actual == count, f"Expected {count} failures, got {actual}"


@then("I clear the soft assert failures")
def step_clear_soft_assert_failures(context: object) -> None:
    collector = getattr(context, "_behave_kit_soft", None)
    if collector is not None:
        collector.clear()


# --- Skip steps ---


@when('I run a step that skips on env "{env_name}"')
def step_skip_on_env(context: object, env_name: str) -> None:
    from behave_kit import skip_if_env

    @skip_if_env(env_name)
    def inner(ctx: object) -> str:
        return "ran"

    try:
        inner(context)
        context._skip_skipped = False
    except Exception as exc:
        if "skip" in str(exc).lower():
            context._skip_skipped = True
        else:
            raise


@then("the step should be skipped")
def step_verify_skipped(context: object) -> None:
    assert getattr(context, "_skip_skipped", False), "Step should have been skipped"


@then("the step should not be skipped")
def step_verify_not_skipped(context: object) -> None:
    assert not getattr(context, "_skip_skipped", True), "Step should not have been skipped"


# --- Fixture steps ---


@given("a browser fixture is registered")
def step_register_browser_fixture(context: object) -> None:
    @fixture("browser")
    def browser_fixture(ctx: object) -> tuple:
        def setup_fn(c: object) -> None:
            c._browser_started = True

        def teardown_fn(c: object) -> None:
            c._browser_torn_down = True

        return (setup_fn, teardown_fn)

    context._fixture_registered = True


@when('I run a scenario with the "{tag}" tag')
def step_run_scenario_with_tag(context: object, tag: str) -> None:
    manager = getattr(context, "_behave_kit_fixtures", None)
    if manager is not None:
        manager.setup_for_scenario(context, type("Obj", (), {"tags": [tag]})())
    context._fixture_setup_done = True


@then("the browser fixture should be set up")
def step_verify_fixture_setup(context: object) -> None:
    assert getattr(context, "_browser_started", False), "Fixture should have been set up"


@then("the browser fixture should be torn down after the scenario")
def step_verify_fixture_teardown(context: object) -> None:
    manager = getattr(context, "_behave_kit_fixtures", None)
    if manager is not None:
        manager.teardown_scenario(context)
    assert getattr(context, "_browser_torn_down", False), "Fixture should have been torn down"


# --- Env vars steps ---


@when('I read env var "{var_name}" with default "{default}"')
def step_read_env_with_default(context: object, var_name: str, default: str) -> None:
    value = env(var_name, required=False, default=default, context=context)
    context._env_value = value


@when('I set env var "{var_name}" to "{value}"')
def step_set_env_var(context: object, var_name: str, value: str) -> None:
    os.environ[var_name] = value


@then('the value should be "{expected}"')
def step_verify_value(context: object, expected: str) -> None:
    actual = context._env_value
    assert str(actual) == expected, f"Expected '{expected}', got '{actual}'"


@when('I read env var "{var_name}" as required')
def step_read_env_required(context: object, var_name: str) -> None:
    try:
        env(var_name, required=True, context=context)
        context._env_error = None
    except EnvVarError as exc:
        context._env_error = exc


@then("it should raise an EnvVarError")
def step_verify_env_error(context: object) -> None:
    error = getattr(context, "_env_error", None)
    assert error is not None, "Expected an EnvVarError to be raised"


# --- Data loading steps ---


@given('a CSV file "{filename}" with columns "{columns}"')
def step_create_csv(context: object, filename: str, columns: str) -> None:
    tmpdir = Path(tempfile.mkdtemp())
    filepath = tmpdir / filename
    col_names = columns.split(",")
    lines = [",".join(col_names)]
    lines.append("Alice,30")
    lines.append("Bob,25")
    filepath.write_text("\n".join(lines) + "\n", encoding="utf-8")
    context._data_dir = tmpdir


@given('a JSON file "{filename}" with key "{key}" and value "{value}"')
def step_create_json(context: object, filename: str, key: str, value: str) -> None:
    tmpdir = Path(tempfile.mkdtemp())
    filepath = tmpdir / filename
    filepath.write_text(f'{{"{key}": "{value}"}}\n', encoding="utf-8")
    context._data_dir = tmpdir


@when('I load data from "{filename}"')
def step_load_data(context: object, filename: str) -> None:
    data_dir = context._data_dir
    filepath = data_dir / filename
    data = load_data(str(filepath))
    context._loaded_data = data


@then("the result should be a list of {count:d} records")
def step_verify_list_count(context: object, count: int) -> None:
    data = context._loaded_data
    assert isinstance(data, list), f"Expected list, got {type(data)}"
    assert len(data) == count, f"Expected {count} records, got {len(data)}"


@then('the first record should have name "{name}"')
def step_verify_first_record(context: object, name: str) -> None:
    data = context._loaded_data
    assert data[0]["name"] == name, f"Expected name '{name}', got '{data[0]['name']}'"


@then('the result should have key "{key}" with value "{value}"')
def step_verify_key_value(context: object, key: str, value: str) -> None:
    data = context._loaded_data
    assert key in data, f"Key '{key}' not found in data"
    assert str(data[key]) == value, f"Expected '{value}', got '{data[key]}'"


# --- TypedContext steps ---


class _TestSchema:
    driver: str
    base_url: str


@given('a TypedContext with schema declaring "driver" and "base_url"')
def step_create_typed_context_full(context: object) -> None:
    typed = TypedContext(context, _TestSchema)
    context._typed_ctx = typed


@given('a TypedContext with schema declaring "driver"')
def step_create_typed_context_driver_only(context: object) -> None:
    class _DriverOnlySchema:
        driver: str

    typed = TypedContext(context, _DriverOnlySchema)
    context._typed_ctx = typed


@when('I setup the context with driver "{driver}" and base_url "{base_url}"')
def step_setup_typed_context(context: object, driver: str, base_url: str) -> None:
    typed = context._typed_ctx
    typed.setup(driver=driver, base_url=base_url)


@then('the typed context driver should be "{value}"')
def step_verify_typed_driver(context: object, value: str) -> None:
    typed = context._typed_ctx
    assert typed.driver == value, f"Expected '{value}', got '{typed.driver}'"


@then('the typed context base_url should be "{value}"')
def step_verify_typed_base_url(context: object, value: str) -> None:
    typed = context._typed_ctx
    assert typed.base_url == value, f"Expected '{value}', got '{typed.base_url}'"


@when('I try to access "{attr}" from the typed context')
def step_access_undeclared(context: object, attr: str) -> None:
    typed = context._typed_ctx
    try:
        getattr(typed, attr)
        context._scope_error = None
    except ScopeError as exc:
        context._scope_error = exc


@then("it should raise a ScopeError")
def step_verify_scope_error(context: object) -> None:
    error = getattr(context, "_scope_error", None)
    assert error is not None, "Expected a ScopeError to be raised"
