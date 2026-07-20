# behave-kit

The Swiss-army knife for [Behave](https://github.com/behave/behave) — soft assertions, typed context, conditional skip, environment management, fixtures and more.

[![CI](https://github.com/MathiasPaulenko/behave-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/MathiasPaulenko/behave-kit/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/MathiasPaulenko/behave-kit/branch/main/graph/badge.svg)](https://codecov.io/gh/MathiasPaulenko/behave-kit)
[![PyPI](https://img.shields.io/pypi/v/behave-kit.svg)](https://pypi.org/project/behave-kit/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Why behave-kit?

Behave is great for BDD, but real test suites need more than Given/When/Then. You need to:

- **Collect multiple assertion failures** without stopping at the first one
- **Skip steps** based on environment, OS, or missing dependencies
- **Read environment variables** with type conversion and validation
- **Load test data** from CSV, JSON, YAML, or Excel files
- **Manage fixtures** with automatic setup/teardown by tag
- **Get IDE autocompletion** for context attributes
- **Debug failures** with automatic context dumps

behave-kit provides all of these as independent, opt-in utilities — no monkey-patching, no breaking changes.

## Installation

```bash
pip install behave-kit
```

With optional extras:

```bash
pip install "behave-kit[yaml,excel,dotenv,pydantic]"
```

| Extra | Provides | Dependency |
|-------|----------|------------|
| `yaml` | YAML data loading | `pyyaml>=6.0` |
| `excel` | XLSX data loading | `openpyxl>=3.1` |
| `dotenv` | `.env` file loading | `python-dotenv>=1.0` |
| `pydantic` | Schema validation | `pydantic>=2.0` |
| `docs` | Sphinx documentation build | `sphinx`, `furo`, `myst-parser` |
| `dev` | Development tools | `pytest`, `ruff`, `mypy`, `build`, `pre-commit` |

## Quickstart

### Level 1 — Automatic wiring

Add two lines to your `environment.py` and every feature is wired automatically:

```python
from behave_kit import setup, teardown

def before_all(context):
    setup(context, env="staging")

def after_scenario(context, scenario):
    teardown(context)
```

### Level 2 — Cherry-pick

Import only what you need:

```python
from behave_kit import assert_soft, env, load_data

@then("the response should be valid")
def step(context):
    assert_soft(context.response.status_code == 200)
    api_key = env("API_KEY", required=True)
    users = load_data("tests/data/users.csv")
```

### Level 3 — Namespace

```python
import behave_kit as bk

@then("the response should be valid")
def step(context):
    bk.assert_soft(context.response.status_code == 200)
```

## Features

### Soft assertions

Collect multiple failures and report them all at once:

```python
from behave_kit import assert_soft

assert_soft(response.status_code == 200)
assert_soft(response.body["count"] > 0)
assert_soft("error" not in response.body)
# All failures reported together at teardown
```

### TypedContext

Schema-validated proxy with IDE autocompletion and mypy support:

```python
from behave_kit import TypedContext

class MySchema:
    driver: str
    base_url: str

ctx = TypedContext(context, MySchema)
ctx.setup(driver="chrome", base_url="https://test.com")
print(ctx.driver)  # IDE autocompletion works
```

### Conditional skip

Skip steps by environment, OS, or missing dependency:

```python
from behave_kit import skip_if_env, skip_if_no_browser, skip_on_os, skip_if_missing

@skip_if_env("production")
@when("I run the staging-only step")
def step(context): ...

@skip_if_no_browser
@when("I open the browser")
def step(context): ...

@skip_on_os("windows")
@when("I run the unix-only step")
def step(context): ...

@skip_if_missing("selenium")
@when("I use selenium")
def step(context): ...
```

### Environment variables

Typed reads with defaults, validation, and config file fallback:

```python
from behave_kit import env

api_key = env("API_KEY", required=True)                    # str
timeout = env("TIMEOUT", var_type=int, default=30)         # int
debug = env("DEBUG", var_type=bool, default=False)         # bool
```

### Data loading

Single API for CSV, JSON, YAML, and Excel:

```python
from behave_kit import load_data

users = load_data("tests/data/users.csv")       # list[dict]
config = load_data("tests/data/config.json")    # dict
sheet = load_data("tests/data/sheet.xlsx")      # list[dict] (requires [excel])
```

### Fixtures

Tag-based setup/teardown with dependency resolution:

```python
from behave_kit import fixture

@fixture("browser")
def browser_fixture(context):
    def setup(ctx):
        ctx.browser = start_browser()
    def teardown(ctx):
        ctx.browser.quit()
    return (setup, teardown)

@fixture("database", requires="browser")
def database_fixture(context):
    ...
```

### Context dump

Automatic context snapshot on scenario failure for easier debugging:

```python
from behave_kit import dump_context_on_failure
# Wired automatically by setup(), or call manually
```

### Step suggestions

"Did you mean?" hints for undefined steps:

```python
from behave_kit import setup_suggestions
# Wired automatically by setup()
```

### Scoped attributes

Automatic cleanup of context attributes per scenario:

```python
from behave_kit import scoped

@scoped("driver")
@when("I start the driver")
def step(context):
    context.driver = start_driver()
# "driver" is automatically deleted after the scenario
```

### Conditional steps

Run a step only when a condition holds:

```python
from behave_kit import when_if

@when_if(lambda ctx: ctx.config.env == "staging")
@when("I run the staging-only step")
def step(context): ...
```

### Parameter types

Register custom Behave parameter types:

```python
from behave_kit import parameter_type

@parameter_type("User")
def parse_user(text):
    return User(name=text)
```

## Documentation

Full documentation is available at [mathiaspaulenko.github.io/behave-kit](https://mathiaspaulenko.github.io/behave-kit).

To build docs locally:

```bash
pip install "behave-kit[docs]"
cd docs && sphinx-build -b html . _build/html
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, coding standards, and contribution guidelines.

## License

MIT — see [LICENSE](LICENSE).
