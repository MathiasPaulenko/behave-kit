Migration Guide
===============

From raw Behave to behave-kit
-----------------------------

behave-kit is designed as a drop-in enhancement — no breaking changes to your
existing Behave suite.  You can adopt features incrementally.

Step 1: Install
~~~~~~~~~~~~~~~

.. code-block:: bash

   pip install behave-kit

Step 2: Wire automatic features (optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add to ``environment.py``:

.. code-block:: python

   from behave_kit import setup, teardown

   def before_all(context):
       setup(context, env="staging")

   def after_scenario(context, scenario):
       teardown(context)

This enables:

- Soft assertion collector (reset per scenario)
- Context dump on failure
- Step suggestions for undefined steps
- Fixture manager
- Scoped attribute cleanup

Step 3: Replace raw asserts with soft asserts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before:

.. code-block:: python

   @then("the response should be valid")
   def step(context):
       assert context.response.status_code == 200
       assert context.response.body["count"] > 0

After:

.. code-block:: python

   from behave_kit import assert_soft

   @then("the response should be valid")
   def step(context):
       assert_soft(context.response.status_code == 200)
       assert_soft(context.response.body["count"] > 0)

Soft asserts collect all failures and report them together at teardown,
instead of stopping at the first one.

Step 4: Add typed context (optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before:

.. code-block:: python

   @given("I have a browser")
   def step(context):
       context.driver = "chrome"
       context.base_url = "https://test.com"

   @then('the driver should be "{driver}"')
   def step(context, driver):
       assert context.driver == driver  # no IDE autocompletion

After:

.. code-block:: python

   from behave_kit import TypedContext

   class MySchema:
       driver: str
       base_url: str

   @given("I have a browser")
   def step(context):
       ctx = TypedContext(context, MySchema)
       ctx.setup(driver="chrome", base_url="https://test.com")

   @then('the driver should be "{driver}"')
   def step(context, driver):
       ctx = TypedContext(context, MySchema)
       assert ctx.driver == driver  # IDE autocompletion + mypy validation

Step 5: Replace manual env reads
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before:

.. code-block:: python

   import os
   api_key = os.environ.get("API_KEY")
   if api_key is None:
       raise ValueError("API_KEY is not set")

After:

.. code-block:: python

   from behave_kit import env
   api_key = env("API_KEY", required=True)

Step 6: Add tag-based fixtures (optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before:

.. code-block:: python

   def before_scenario(context, scenario):
       if "browser" in scenario.tags:
           context.browser = start_browser()

   def after_scenario(context, scenario):
       if hasattr(context, "browser"):
           context.browser.quit()

After:

.. code-block:: python

   from behave_kit import fixture

   @fixture("browser")
   def browser_fixture(context):
       def setup(ctx):
           ctx.browser = start_browser()
       def teardown(ctx):
           ctx.browser.quit()
       return (setup, teardown)

   # In environment.py:
   from behave_kit.fixtures import FixtureManager
   fixtures = FixtureManager()

   def before_scenario(context, scenario):
       fixtures.setup_for_scenario(context, scenario)

   def after_scenario(context, scenario):
       fixtures.teardown_scenario(context)

Compatibility
~~~~~~~~~~~~~

- behave-kit works with Behave >= 1.2.6
- Python >= 3.11
- No monkey-patching — all features are opt-in
- Existing step definitions continue to work unchanged
