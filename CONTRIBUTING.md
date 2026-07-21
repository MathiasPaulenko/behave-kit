# Contributing to behave-kit

Thank you for your interest in contributing! This document covers setup,
development commands, and the release process.

## Setup

```bash
git clone https://github.com/MathiasPaulenko/behave-kit.git
cd behave-kit
pip install -e ".[dev,yaml,excel,dotenv]"
pre-commit install
pre-commit run --all-files
```

## Development Commands

| Command | Description |
| :--- | :--- |
| `make dev` | Install with dev dependencies |
| `make lint` | Run ruff check + mypy |
| `make lint-fix` | Run ruff check with --fix |
| `make format` | Run ruff format |
| `make format-check` | Check formatting without changes |
| `make test` | Run pytest |
| `make test-cov` | Run pytest with coverage |
| `make build` | Build sdist + wheel |
| `make clean` | Remove build artifacts |

## Pre-PR Checklist

- [ ] `make lint` passes with 0 errors
- [ ] `make format-check` passes
- [ ] `make test-cov` passes with coverage >= 90%
- [ ] All public functions have type hints
- [ ] Tests cover happy path + edge cases
- [ ] Documentation updated if public APIs or behavior changed
- [ ] CHANGELOG.md updated (if user-facing changes)
- [ ] Backward compatibility considered

## Release Process

1. Update `CHANGELOG.md` with a new `[Unreleased]` -> `[X.Y.Z]` section
2. Bump `version` in `pyproject.toml`
3. Run `make lint`, `make format-check`, and `make test-cov`
4. Commit and push to `main`
5. CI detects the version bump, creates the tag, builds, publishes to PyPI,
   and creates a GitHub Release automatically
