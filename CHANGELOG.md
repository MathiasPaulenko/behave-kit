# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
