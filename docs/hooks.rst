Hooks and Wiring
================

The `setup()` and `teardown()` functions wire all behave-kit modules into a
Behave context with a single call.

setup()
-------

.. autofunction:: behave_kit.hooks.setup

Wires the following modules (each independently, fault-tolerant):

- **env config** — loads `behave.toml` and attaches `KitConfig` to context
- **soft asserts** — activates `SoftAssertCollector` via contextvars
- **context dump** — enables automatic context dump on scenario failure
- **suggestions** — wires "did you mean?" hints for undefined steps
- **fixtures** — creates a `FixtureManager` and attaches it to context

teardown()
----------

.. autofunction:: behave_kit.hooks.teardown

Cleans up wired modules in reverse order:

1. Teardown fixtures (runs each fixture's teardown function)
2. Cleanup scoped attributes
3. Report soft assertion failures (raises if any collected)
4. Dump context if scenario failed

Examples
--------

Full automatic wiring
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from behave_kit import setup, teardown

   def before_all(context):
       setup(context, env="staging", config_file="behave.toml")

   def before_scenario(context, scenario):
       # Re-activate soft asserts for each scenario
       from behave_kit import use_soft_asserts
       use_soft_asserts(context)
       # Setup fixtures for this scenario
       manager = context._behave_kit_fixtures
       manager.setup_for_scenario(context, scenario)

   def after_scenario(context, scenario):
       # Clear soft assert failures before teardown
       collector = getattr(context, "_behave_kit_soft", None)
       if collector is not None:
           collector.clear()
       # Teardown fixtures
       manager = context._behave_kit_fixtures
       manager.teardown_scenario(context)
       # Full teardown
       teardown(context)

Minimal wiring
~~~~~~~~~~~~~~

.. code-block:: python

   from behave_kit import setup, teardown

   def before_all(context):
       setup(context)

   def after_scenario(context, scenario):
       teardown(context)

With log level
~~~~~~~~~~~~~~

.. code-block:: python

   from behave_kit import setup

   def before_all(context):
       setup(context, env="staging", log_level="DEBUG")

Without env config
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from behave_kit import setup

   def before_all(context):
       setup(context)  # No env config, but soft asserts + fixtures + dump still wired

Idempotency
~~~~~~~~~~~

.. code-block:: python

   from behave_kit import setup

   def before_all(context):
       setup(context, env="staging")
       setup(context, env="staging")  # No-op, already wired

Fault tolerance
~~~~~~~~~~~~~~~

If one module fails to wire, the others still work:

.. code-block:: python

   from behave_kit import setup

   def before_all(context):
       # Even if behave.toml is missing, soft asserts and fixtures still work
       setup(context, env="staging", config_file="missing.toml")
       # Logs: WARNING: Failed to wire env config
