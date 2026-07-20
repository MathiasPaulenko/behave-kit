Fixtures
========

Tag-based fixtures with automatic setup/teardown and dependency resolution.

Fixtures eliminate manual ``if "browser" in scenario.tags`` checks in
``before_scenario`` / ``after_scenario`` hooks.  Instead, you register a
fixture with a name and tag, and the `FixtureManager` handles the lifecycle
automatically.

How it works
------------

1. Register a fixture with ``@fixture("name")`` — the factory returns a
   ``(setup_fn, teardown_fn)`` tuple (or ``None``).
2. The `FixtureManager` reads scenario tags and runs the matching fixture's
   ``setup_fn`` before the scenario.
3. After the scenario, the manager runs each ``teardown_fn`` in reverse order.

Defining a fixture
------------------

.. code-block:: python

   from behave_kit import fixture

   @fixture("browser")
   def browser_fixture(context):
       def setup(ctx):
           ctx.browser = {"name": "chrome", "started": True}
       def teardown(ctx):
           ctx.browser = None
       return (setup, teardown)

The factory function receives ``context`` and returns a tuple of two
callables:

- **setup(ctx)** — called before the scenario, sets up resources on ``ctx``
- **teardown(ctx)** — called after the scenario, cleans up resources

Returning ``None`` means the fixture has no setup/teardown (useful for
conditional fixtures).

Fixture scopes
--------------

.. code-block:: python

   from behave_kit.fixtures.registry import fixture, Scope

   @fixture("browser", scope=Scope.SCENARIO)
   def browser_fixture(context):
       # Setup and teardown per scenario (default)
       ...

   @fixture("database", scope=Scope.FEATURE)
   def database_fixture(context):
       # Setup once per feature, teardown after all scenarios
       ...

Dependency resolution
---------------------

Fixtures can declare dependencies on other fixtures:

.. code-block:: python

   @fixture("database", requires="browser")
   def database_fixture(context):
       def setup(ctx):
           ctx.db = connect_to_database(ctx.browser)
       def teardown(ctx):
           ctx.db.close()
       return (setup, teardown)

When ``database`` is requested, ``browser`` is set up first automatically.

API reference
-------------

.. autofunction:: behave_kit.fixtures.registry.fixture

.. autoclass:: behave_kit.fixtures.manager.FixtureManager
   :members:

.. autoclass:: behave_kit.fixtures.registry.Scope
   :members:

Examples
--------

Browser fixture
~~~~~~~~~~~~~~~

.. code-block:: python

   from behave_kit import fixture

   @fixture("browser")
   def browser_fixture(context):
       def setup(ctx):
           from selenium import webdriver
           ctx.browser = webdriver.Chrome()
           ctx.browser.get("https://example.com")
       def teardown(ctx):
           if hasattr(ctx, "browser"):
               ctx.browser.quit()
               ctx.browser = None
       return (setup, teardown)

Database fixture
~~~~~~~~~~~~~~~~

.. code-block:: python

   @fixture("database")
   def database_fixture(context):
       def setup(ctx):
           import sqlite3
           ctx.db = sqlite3.connect(":memory:")
           ctx.db.execute("CREATE TABLE users (name TEXT, email TEXT)")
       def teardown(ctx):
           if hasattr(ctx, "db"):
               ctx.db.close()
       return (setup, teardown)

API client fixture
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   @fixture("api_client")
   def api_client_fixture(context):
       def setup(ctx):
           import requests
           ctx.session = requests.Session()
           ctx.session.headers["Authorization"] = f"Bearer {ctx.api_key}"
       def teardown(ctx):
           if hasattr(ctx, "session"):
               ctx.session.close()
       return (setup, teardown)

Using fixtures with tags
~~~~~~~~~~~~~~~~~~~~~~~~

In your feature file:

.. code-block:: gherkin

   Feature: API tests

   @browser @api_client
   Scenario: Login via browser
     Given I navigate to the login page
     When I enter credentials
     Then I should be logged in

   @database
   Scenario: User CRUD
     Given I have a clean database
     When I create a user
     Then the user should exist in the database

Wiring the FixtureManager
~~~~~~~~~~~~~~~~~~~~~~~~~

**Automatic (via `setup()`):**

.. code-block:: python

   from behave_kit import setup

   def before_all(context):
       setup(context, env="staging")

   def before_scenario(context, scenario):
       manager = context._behave_kit_fixtures
       manager.setup_for_scenario(context, scenario)

   def after_scenario(context, scenario):
       manager = context._behave_kit_fixtures
       manager.teardown_scenario(context)

**Manual:**

.. code-block:: python

   from behave_kit.fixtures import FixtureManager

   fixtures = FixtureManager()

   def before_scenario(context, scenario):
       fixtures.setup_for_scenario(context, scenario)

   def after_scenario(context, scenario):
       fixtures.teardown_scenario(context)

Conditional fixtures
~~~~~~~~~~~~~~~~~~~~

Return ``None`` from the factory to skip setup/teardown:

.. code-block:: python

   @fixture("optional_browser")
   def optional_browser_fixture(context):
       if not hasattr(context, "browser_enabled"):
           return None
       def setup(ctx):
           ctx.browser = start_browser()
       def teardown(ctx):
           ctx.browser.quit()
       return (setup, teardown)
