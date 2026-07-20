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

   @scoped("driver")
   @when("I start the driver")
   def step(context):
       context.driver = start_driver()
   # context.driver is automatically deleted after the scenario

**Multiple scoped attributes:**

.. code-block:: python

   @scoped("browser")
   @scoped("session")
   @when("I start a browser session")
   def step(context):
       context.browser = start_browser()
       context.session = create_session()

**Feature-scoped attributes:**

.. code-block:: python

   from behave_kit import scoped, Scope

   @scoped("database", scope=Scope.FEATURE)
   @given("I have a database connection")
   def step(context):
       context.database = connect_to_database()
   # context.database is cleaned up after all scenarios in the feature

**Manual cleanup:**

.. code-block:: python

   from behave_kit import cleanup_scoped

   def after_scenario(context, scenario):
       cleanup_scoped(context)  # delete all scenario-scoped attributes

Why scoped attributes matter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Without `@scoped`, attributes set in one scenario survive into the next:

.. code-block:: python

   # Scenario 1
   @when("I create a temporary file")
   def step(context):
       context.temp_file = create_temp_file()

   # Scenario 2 (temp_file still exists from Scenario 1!)
   @then("no temp file should exist")
   def step(context):
       assert not hasattr(context, "temp_file")  # FAILS without @scoped

With `@scoped`:

.. code-block:: python

   @scoped("temp_file")
   @when("I create a temporary file")
   def step(context):
       context.temp_file = create_temp_file()
   # temp_file is deleted after Scenario 1, so Scenario 2 passes
