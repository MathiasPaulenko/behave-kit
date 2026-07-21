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
- **Poll for conditions** with configurable timeout and interval
- **Assert expected exceptions** as part of soft assertion collections
- **Run data-driven steps** from CSV, JSON, YAML, or Excel files
- **Isolate environment variables** with snapshot/restore context managers
- **Navigate nested dicts** with dot notation
- **Assert execution time** with `assert_under` and `@timed`
- **Create temp directories** for filesystem-isolated tests
- **Continue after failed steps** for comprehensive test reporting
- **Execute sub-steps** with outline substitution and state isolation
- **Class-based steps** — define Given/When/Then as methods on a class with `self.context`, lifecycle hooks, and per-step matchers

behave-kit provides all of these as independent, opt-in utilities — no monkey-patching, no breaking changes.

## Installation

```bash
pip install behave-kit
```

With optional extras:

```bash
pip install "behave-kit[yaml,excel,dotenv]"
```

| Extra | Provides | Dependency |
|-------|----------|------------|
| `yaml` | YAML data loading | `pyyaml>=6.0` |
| `excel` | XLSX data loading | `openpyxl>=3.1` |
| `dotenv` | `.env` file loading | `python-dotenv>=1.0` |
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

@parameter_type("User", r"[\w.]+@[\w.]+\.[a-z]+")
def parse_user(text):
    return User(name=text)
```

### Class-based steps

Define step implementations as methods on a class, with per-scenario instances,
lifecycle hooks, and per-step matcher selection:

```python
from behave_kit import step_impl_base

Base = step_impl_base()

class AccountSteps(Base):
    @Base.given("I have a balance of {amount:d}")
    def set_balance(self, amount):
        self.balance = amount

    @Base.when("I deposit {amount:d}")
    def deposit(self, amount):
        self.balance += amount

    @Base.then("the balance should be {expected:d}")
    def check_balance(self, expected):
        assert self.balance == expected

    @property
    def balance(self):
        return getattr(self.context, "balance", 0)

    @balance.setter
    def balance(self, value):
        self.context.balance = value

    def setup(self):
        # Called once when the instance is created for a scenario
        pass

    def teardown(self):
        # Called after the scenario ends (via teardown_steps / teardown)
        pass

AccountSteps.register()
```

`self.context` is bound automatically — no `context` parameter needed.
Subclass to extend or override steps; register only the most-derived class.
Pass `matcher=RegexMatcher` to a decorator for per-step matcher selection.

### Soft exception assertions

Check that a callable raises an expected exception, collected as a soft failure:

```python
from behave_kit import assert_soft_raises

assert_soft_raises(ValueError, lambda: int("abc"))
assert_soft_raises(KeyError, lambda: {}["missing"])
# Failures are collected and reported together at teardown
```

### Data-driven steps

Run a step once per row of a data file, with column names injected as keyword arguments:

```python
from behave_kit import data_driven

@data_driven("tests/data/users.csv")
@when("I login as {username}")
def step(context, username=None, password=None):
    login(username, password)
# Runs once per row in users.csv
```

### Environment variable snapshot

Save and restore `os.environ` so tests don't leak environment variable changes:

```python
from behave_kit import env_snapshot

with env_snapshot():
    os.environ["API_KEY"] = "test"
    # ... test ...
# API_KEY restored automatically
```

### Dict navigation with `get_path`

Extract values from nested dicts using dot notation:

```python
from behave_kit import get_path

city = get_path(response, "user.address.city")           # "Berlin"
name = get_path(response, "users.0.name", default="?")   # "Alice"
```

### Time assertions

Assert that a callable completes within a time limit:

```python
from behave_kit import assert_under, timed

assert_under(2.0, lambda: client.get("/health"))

@timed(1.5)
@when("I fetch the data")
def step(context): ...
```

### Wait until

Poll a condition until it becomes true or a timeout is reached:

```python
from behave_kit import wait_until

wait_until(lambda: context.response.status_code == 200, timeout=10, interval=0.5)
```

### Temp workspace

Create an isolated temporary directory and restore the CWD on exit:

```python
from behave_kit import temp_workspace

with temp_workspace() as tmp:
    config_path = tmp / "config.json"
    config_path.write_text("{}")
# Directory is cleaned up automatically
```

### Continue after failed step

Control whether scenarios keep running remaining steps after a failure:

```python
from behave_kit import continue_after_failed, continue_on_failure

# Enable globally
continue_after_failed(True)

# Or temporarily via context manager
with continue_on_failure():
    # scenarios inside this block continue after failed steps
    ...
```

Or wire it through `setup()`:

```python
from behave_kit import setup

def before_all(context):
    setup(context, continue_after_failed=True)
```

### Sub-step execution with isolation

Execute Gherkin sub-steps with Scenario Outline variable substitution and guaranteed table/text restoration:

```python
from behave_kit import run_steps

@when("I complete the checkout flow")
def step_impl(context):
    run_steps(context, '''
        Given I have items in my cart
        When I enter shipping info for "<city>"
        Then I should see the order confirmation
    ''')
# context.table and context.text are preserved after execution
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
