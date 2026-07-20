# behave-kit

The Swiss-army knife for [Behave](https://github.com/behave/behave) — soft assertions, typed context, conditional skip, environment management, fixtures and more.

## Install

```bash
pip install behave-kit
```

With optional extras:

```bash
pip install "behave-kit[yaml,excel,dotenv,pydantic]"
```

## Basic usage

```python
from behave_kit import assert_soft, env

@then("the response should be valid")
def step(context):
    assert_soft(context.response.status_code == 200)
    api_key = env("API_KEY", required=True)
```

behave-kit is a set of independent utilities — use only what you need. See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup.

## License

MIT — see [LICENSE](LICENSE).
