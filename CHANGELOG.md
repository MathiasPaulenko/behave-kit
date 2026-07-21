# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
