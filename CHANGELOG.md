# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.6.0] - 2026-10-02

### Added

- `teardown_feature(context)` — cleans up FEATURE-scoped fixtures and
  `@scoped(..., scope=Scope.FEATURE)` attributes; call from `after_feature`.
- `@parameter_type` and `register_builtin_types()` now register converters with
  Behave's parse/cfparse matcher, so `{name:Type}` placeholders work in step
  patterns (e.g. `{user:User}`, `{n:int}`).

### Changed

- `load_env_config()` now stores the resolved `KitConfig` on
  `context.kit_config` instead of replacing `context.config` — Behave's own
  `config` object (`userdata`, formatter settings) is no longer clobbered.
  `env()` and `is_env()` read `kit_config` first and still fall back to
  `context.config` for compatibility.
- `setup()` attaches the `FixtureManager` to the public `context.kit_fixtures`
  (the old `_behave_kit_fixtures` attribute is still read as a fallback) and
  the suggestions `after_step` hook to `context.kit_suggestions` (call it from
  `after_step` — Behave hooks cannot be injected).
- `run_steps()` accepts `context.active_outline` as `dict`, `behave.model.Row`,
  or any `items()`/`as_dict()`-compatible object.

### Fixed

- `run_steps()` no longer fails inside real Scenario Outlines: Behave exposes
  the outline row as `behave.model.Row`, which was rejected by the previous
  `dict`-only validation.
- `teardown()` is now fault-tolerant: an error in one teardown step (e.g. a
  Windows `TimeoutError` or a soft-assert `AssertionError`) no longer skips the
  remaining cleanup, and `continue_after_failed` is always reset.
- `data_driven` sanitizes any non-identifier column name (dots, leading digits)
  instead of only hyphens and spaces, and raises `BehaveKitError` for
  unsalvageable keys instead of a raw `TypeError`.
- `get_path` supports dicts with integer keys via numeric segments, and its
  error message no longer breaks on non-string keys.
- `deep_compare` compares integers exactly (no `float()` overflow on huge ints)
  and unordered-sequence matching no longer leaks partial `seen` state.
- `setup_timeout`/`setup` log-level validation no longer mutates the root
  logger; `setup_timeout` validates `BEHAVE_SCENARIO_TIMEOUT` and numeric
  arguments with clear `ValueError` messages.
- `timeout_after_scenario` now reads the original failure from the failed
  *step* (Behave never sets `scenario.exception`), so a Windows timeout no
  longer masks the scenario's real exception.
- `_load_xlsx` now closes the workbook after reading.
- `KitConfig.from_toml` raises `ConfigError` (not raw `ValueError`) for
  non-integer `timeouts` values and validates `base_url`/`browser` types.
- Docs: all step-decorator examples now show the correct order (behave-kit
  decorators inside `@when`/`@given`/`@then`), `sub_steps.rst` documents the
  real `SubStepError`/`Row` behaviour, `timeout.rst` describes the Windows
  fallback accurately, and `docs/conf.py` reads the version from the package.
- `release.yml`: `workflow_dispatch` no longer fails the tag check, and PyPI
  publish uses `skip-existing` instead of `continue-on-error` so real publish
  failures still gate the GitHub Release.

## [1.5.0] - 2026-08-08

### Added

- `setup_timeout(context)` now reads the default timeout from the
  `BEHAVE_SCENARIO_TIMEOUT` environment variable when `default_timeout` is not
  provided. An explicit `default_timeout` still takes precedence.

## [1.4.0] - 2026-08-06

### Added

- `setup_timeout` — configure a default per-scenario timeout on the Behave context.
- `timeout_before_scenario` / `timeout_after_scenario` — hook functions to start and cancel per-scenario timers.
- `teardown_timeout` — public teardown function for cleanup in `teardown()`.
- **Per-scenario timeout** — `@timeout:N` tags override a default, platform-aware (SIGALRM on Unix, threading.Timer on Windows).
- `@timeout:0` disables the timeout for a specific scenario.
- Feature-level timeout tags inherit to all scenarios; scenario tags override feature tags.
- Platform-aware handlers: `signal.SIGALRM` on Unix for immediate interruption, `threading.Timer` on Windows as fallback.
- New `behave_kit.timeout` module.
- README, Sphinx docs, and E2E feature coverage for per-scenario timeout.

### Fixed

- Reject `inf`, `nan`, and `-inf` as timeout tag values (would create confusing handler behaviour).
- `timeout_after_scenario` now passes the scenario's existing exception to the handler, preventing `TimeoutError` from masking the original failure.
- `setup_timeout` validates `timeout_tag` is a non-empty string and `default_timeout` is finite.
- `SignalTimeoutHandler` and `ThreadTimeoutHandler` are now reentrancy-guarded — calling `__enter__` twice raises `RuntimeError`.
- `__exit__` without prior `__enter__` is now a safe no-op on both handlers.
- Deduplicated `_TIMEOUT_KEY` constant between `hooks.py` and `timeout.py` (single source of truth).

## [1.3.1] - 2026-07-21

### Added

- `step_impl_base` — class-based Behave step implementations with per-scenario instances, `setup()`/`teardown()` lifecycle hooks, per-step matcher selection, and subclass overriding support.
- `teardown_steps` — tears down all live class-based step instances for a context; wired automatically by `setup()` / `teardown()`.
- New `behave_kit.steps.classes` module.
- README, Sphinx docs, and E2E feature coverage for class-based steps.

### Changed

- `teardown()` now tears down class-based step instances even when `setup()` was not called, supporting cherry-picked usage of `step_impl_base`.

### Fixed

- `step_impl_base`: `register()` now cleans up any matchers added before an `AmbiguousStep` (or any other exception), preventing orphaned steps in Behave's global registry and allowing clean re-registration after the conflict is resolved.
- `step_impl_base`: per-scenario instances are now cached **before** `setup()` runs, so a failing `setup()` no longer causes subsequent steps to re-create and re-fail the instance, and `teardown_steps()` can still call `teardown()` for resource cleanup when `setup()` raised.
- `teardown_steps` now iterates over a snapshot of the instances dict, preventing `RuntimeError: dictionary changed size during iteration` when a `teardown()` method triggers additional step execution that adds new instances.
- `step_impl_base`: custom matcher step definitions (via `matcher=` parameter or `default_matcher`) now validate the pattern by calling `compile()` at registration time, raising a clear `StepError` for malformed patterns instead of silently adding them and failing at match time with a confusing error.

## [1.3.0] - 2026-07-21

### Added

- `continue_after_failed` — set whether scenarios continue executing remaining steps after a failure (globally or via `continue_on_failure()` context manager).
- `run_steps` — execute Gherkin sub-steps with Scenario Outline variable substitution and guaranteed `context.table`/`context.text` restoration.
- `SubStepError` — new exception type for sub-step execution errors.
- `setup()` now accepts an optional `continue_after_failed` parameter.
- `teardown()` now resets `continue_after_failed_step` if it was wired by `setup()`.
- README and Sphinx docs updated with new features.
- Comprehensive unit, integration, and E2E tests for both new features.

### Fixed

- `continue_after_failed` now validates that `enabled` is a boolean, preventing silent falsy values like `None`.
- `run_steps` now rejects empty or whitespace-only step strings before delegating to `execute_steps`.
- `run_steps` now validates that `context.active_outline` is a dict when present, preventing incorrect list/string membership checks.
- `run_steps` now validates that `context.execute_steps` is callable before invoking it.
- `teardown()` now resets `Scenario.continue_after_failed_step` to `False` when `continue_after_failed` was wired by `setup()`, preventing state leaks between test runs.

## [1.2.0] - 2026-07-21

### Added

- `wait_until` — polling utility with configurable timeout and interval for E2E/integration tests.
- `assert_soft_raises` — soft assertion for expected exceptions, supporting single types and tuples.
- `@data_driven` — decorator to run a step once per row from CSV, JSON, YAML, or Excel files.
- `env_snapshot` — context manager to save and restore `os.environ` for test isolation.
- `get_path` — dot-notation navigation for nested dicts and lists with optional defaults.
- `@timed` / `assert_under` — time-based assertions for performance checks.
- `temp_workspace` — context manager for isolated temporary directories with CWD restoration.
- Sphinx documentation page for utilities (`docs/utilities.rst`).
- README and Sphinx docs updated with all new features.

### Fixed

- `assert_soft_raises` no longer raises `AttributeError` when passed a tuple of exception types.
- `assert_soft_raises` no longer catches `KeyboardInterrupt` or `SystemExit` (changed `except BaseException` to `except Exception`).
- `assert_soft_raises` now validates empty exception tuples.
- `@timed` now rejects negative `seconds` at decoration time.
- `@data_driven` now raises `BehaveKitError` when the data file contains no rows.

## [1.1.1] - 2026-07-21

### Fixed

- Release workflow trigger now correctly watches `master` instead of `main`.

### Changed

- Completed Google-style docstring coverage across the public API and test packages.

## [1.1.0] - 2026-07-21

### Added

- `behave_kit._core.boolutil` module for robust scalar-boolean coercion, including array-like object support.
- Expanded unit and integration test coverage for diff, matchers, loader, typed context, variables, skip conditions, and dump utilities.
- New reporter and boolean utility unit tests.
- GitHub Pages workflow for automatic Sphinx documentation deployment.

### Changed

- Hardened public APIs and fixed edge-case bugs across assertions, context, data loading, environment, fixtures, hooks, skip decorators, and conditional steps.
- Expanded Sphinx documentation with per-feature pages, extensive examples, and a complete API reference.
- README refreshed with full production content, badges, quickstart, feature list, and documentation links.

### Removed

- Dropped the optional `pydantic` extra from `pyproject.toml`.
