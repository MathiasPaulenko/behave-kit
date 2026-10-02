Context Utilities
=================

Tools for managing the Behave context: automatic dumps on failure and scoped
attribute cleanup.

Context dump on failure
-----------------------

When a scenario fails, `dump_context()` writes every JSON-serializable
context attribute to a file for post-mortem debugging.

.. autofunction:: behave_kit.context.dump.dump_context

.. autofunction:: behave_kit.context.dump.dump_context_on_failure

Examples
~~~~~~~~

**Automatic (via `setup()`):**

.. code-block:: python

   from behave_kit import setup

   def before_all(context):
       setup(context, env="staging")

   # Context dump on failure is wired automatically.
   # Failed scenarios produce a JSON file in debug/.

**Manual:**

.. code-block:: python

   from behave_kit import dump_context_on_failure

   def after_scenario(context, scenario):
       dump_context_on_failure(context, scenario, path="debug/")

**Always dump (not just on failure):**

.. code-block:: python

   from behave_kit import dump_context

   def after_scenario(context, scenario):
       dump_context(context, path="debug/")

Output format
~~~~~~~~~~~~~

The dump file is named after the scenario and contains all serializable
attributes:

.. code-block:: json

   {
     "base_url": "https://example.com",
     "status_code": 500,
     "user": {"name": "Alice", "age": 30},
     "tags": ["browser", "api"]
   }

Non-serializable attributes (e.g. WebDriver instances, file handles) are
skipped with a warning.

Scoped attributes
-----------------

The `@scoped` decorator tracks context attributes and automatically deletes
them after the scenario, preventing leaks between scenarios.

.. autofunction:: behave_kit.context.scoped.scoped

.. autofunction:: behave_kit.context.scoped.cleanup_scoped

Examples
~~~~~~~~

**Basic usage:**

.. code-block:: python

   from behave_kit import scoped

   @when("I start the driver")
   @scoped("driver")
   def step(context):
       context.driver = start_driver()
   # context.driver is automatically deleted after the scenario

.. note::

   Like all behave-kit step decorators, ``@scoped`` must be placed
   *inside* (below) the Behave ``@given``/``@when``/``@then`` decorator so
   the wrapped function is what Behave registers.

**Multiple scoped attributes:**

.. code-block:: python

   @when("I start a browser session")
   @scoped("browser")
   @scoped("session")
   def step(context):
       context.browser = start_browser()
       context.session = create_session()

**Feature-scoped attributes:**

.. code-block:: python

   from behave_kit import scoped, Scope

   @given("I have a database connection")
   @scoped("database", scope=Scope.FEATURE)
   def step(context):
       context.database = connect_to_database()
   # context.database is cleaned up by teardown_feature() in after_feature

**Manual cleanup:**

.. code-block:: python

   from behave_kit import cleanup_scoped

   def after_scenario(context, scenario):
       cleanup_scoped(context)  # delete all scenario-scoped attributes

Why scoped attributes matter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Behave already pops its scenario context layer after each scenario, so
`@scoped` is most useful for two things: **deterministic cleanup inside
teardown** (attributes are deleted even if they were set on an outer layer,
e.g. in ``before_scenario`` or a shared object) and **feature-scoped
attributes** cleaned by ``teardown_feature()``:

.. code-block:: python

   @given("I have a shared resource")
   @scoped("shared_resource", scope=Scope.FEATURE)
   def step(context):
       context.shared_resource = acquire()

   # environment.py
   def after_feature(context, feature):
       from behave_kit import teardown_feature
       teardown_feature(context)
