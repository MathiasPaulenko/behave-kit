Hooks and Wiring
================

The `setup()` and `teardown()` functions wire all behave-kit modules into a
Behave context with a single call.

setup()
-------

.. autofunction:: behave_kit.hooks.setup

Wires the following modules (each independently, fault-tolerant):

- **env config** — loads `behave.toml` and attaches `KitConfig` to
  ``context.kit_config`` (Behave's own ``context.config`` is untouched)
- **soft asserts** — activates `SoftAssertCollector` via contextvars
- **context dump** — enables automatic context dump on scenario failure
- **suggestions** — builds an ``after_step`` hook for "did you mean?" hints
  and attaches it to ``context.kit_suggestions`` (call it from
  ``after_step`` — Behave hooks cannot be injected)
- **fixtures** — creates a `FixtureManager` and attaches it to
  ``context.kit_fixtures``

teardown()
----------

.. autofunction:: behave_kit.hooks.teardown

Call it from ``after_scenario``.  Runs cleanup in this order:

1. Scenario fixture teardowns
2. Per-scenario timeout check (raises ``TimeoutError`` if expired)
3. Scenario-scoped attribute cleanup
4. Class-based step instance teardowns
5. Context dump if the scenario failed
6. Soft assertion report (raises ``AssertionError`` if failures collected)
7. ``continue_after_failed`` reset (only if wired by ``setup()``)

Teardown is fault-tolerant: every step runs even if an earlier one fails,
and the first error is re-raised once cleanup completes.

teardown_feature()
------------------

.. autofunction:: behave_kit.hooks.teardown_feature

Call it from ``after_feature``.  Runs FEATURE-scoped fixture teardowns and
removes attributes tracked with ``@scoped(..., scope=Scope.FEATURE)``.

Examples
--------

Full automatic wiring
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from behave_kit import setup, teardown, teardown_feature

   def before_all(context):
       setup(context, env="staging", config_file="behave.toml")

   def before_scenario(context, scenario):
       # Re-activate soft asserts for each scenario
       from behave_kit import use_soft_asserts
       use_soft_asserts(context)
       # Run fixtures matching the scenario's tags
       context.kit_fixtures.setup_for_scenario(context, scenario)

   def after_step(context, step):
       # "Did you mean?" hints for undefined steps
       context.kit_suggestions(context, step)

   def after_scenario(context, scenario):
       # Runs fixture teardowns, scoped cleanup, soft-assert report, etc.
       teardown(context)

   def before_feature(context, feature):
       context.kit_fixtures.setup_for_feature(context, feature)

   def after_feature(context, feature):
       teardown_feature(context)

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
