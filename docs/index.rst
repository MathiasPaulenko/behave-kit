behave-kit
==========

The Swiss-army knife for `Behave <https://github.com/behave/behave>`_ — soft
assertions, typed context, conditional skip, environment management, fixtures
and more.

behave-kit is a set of independent, opt-in utilities that make Behave test
suites more robust, readable, and maintainable.  Each feature can be used
standalone or wired automatically via :func:`behave_kit.setup`.

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   quickstart
   migration

.. toctree::
   :maxdepth: 2
   :caption: Features

   soft_assertions
   typed_context
   conditional_skip
   environment_variables
   data_loading
   fixtures
   context_utilities
   step_utilities
   classy_steps
   sub_steps
   continue_after_failed
   utilities
   hooks

.. toctree::
   :maxdepth: 2
   :caption: Reference

   api


Features at a glance
--------------------

- **Soft assertions** — collect multiple failures, report them all at once
- **TypedContext** — schema-validated proxy over the Behave context
- **Conditional skip** — skip steps by env, OS, or missing dependency
- **Environment variables** — typed reads with defaults and validation
- **Data loading** — CSV, JSON, YAML, XLSX with a single ``load_data()`` call
- **Fixtures** — tag-based setup/teardown with dependency resolution
- **Context dump** — automatic context snapshot on scenario failure
- **Step suggestions** — "did you mean?" hints for undefined steps
- **Scoped attributes** — automatic cleanup of context attributes per scenario
- **Conditional steps** — ``@when_if`` runs a step only when a condition holds
- **Class-based steps** — ``step_impl_base()`` defines steps as methods on a class
- **Custom parameter types** — register converters for step parameters
- **Soft exception assertions** — ``assert_soft_raises`` for expected exceptions
- **Data-driven steps** — ``@data_driven`` runs a step once per data row
- **Environment snapshot** — ``env_snapshot`` isolates env var changes
- **Dict navigation** — ``get_path`` for dot-notation nested access
- **Time assertions** — ``assert_under`` and ``@timed`` for deadline checks
- **Polling** — ``wait_until`` for condition-based waiting with timeout
- **Temp workspace** — ``temp_workspace`` for filesystem-isolated tests
- **Continue after failed** — ``continue_after_failed`` keeps scenarios running after a failed step
- **Sub-step execution** — ``run_steps`` composes steps with outline substitution and state isolation
- **Automatic wiring** — ``setup()`` / ``teardown()`` for zero-config adoption

Three adoption levels
---------------------

**Level 1 — Automatic wiring:**

.. code-block:: python

   from behave_kit import setup, teardown

   def before_all(context):
       setup(context, env="staging")

   def after_scenario(context, scenario):
       teardown(context)

**Level 2 — Cherry-pick:**

.. code-block:: python

   from behave_kit import assert_soft, env, load_data

   @then("the response should be valid")
   def step(context):
       assert_soft(context.response.status_code == 200)
       api_key = env("API_KEY", required=True)
       users = load_data("tests/data/users.csv")

**Level 3 — Namespace:**

.. code-block:: python

   import behave_kit as bk

   @then("the response should be valid")
   def step(context):
       bk.assert_soft(context.response.status_code == 200)

Installation
------------

.. code-block:: bash

   pip install behave-kit

With optional extras:

.. code-block:: bash

   pip install "behave-kit[yaml,excel,dotenv]"

License
-------

MIT — see `LICENSE <https://github.com/MathiasPaulenko/behave-kit/blob/main/LICENSE>`_.
