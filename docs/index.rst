behave-kit
==========

The Swiss-army knife for `Behave <https://github.com/behave/behave>`_ — soft
assertions, typed context, conditional skip, environment management, fixtures
and more.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   quickstart
   api
   migration


Overview
--------

behave-kit is a set of independent utilities that make Behave test suites more
robust, readable, and maintainable.  Each feature can be used standalone or
wired automatically via :func:`behave_kit.setup`.

Features at a glance:

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

Installation
------------

.. code-block:: bash

   pip install behave-kit

With optional extras:

.. code-block:: bash

   pip install "behave-kit[yaml,excel,dotenv,pydantic]"

License
-------

MIT — see `LICENSE <https://github.com/MathiasPaulenko/behave-kit/blob/main/LICENSE>`_.
