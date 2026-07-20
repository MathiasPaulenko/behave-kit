Quickstart
==========

behave-kit supports three adoption levels — pick the one that fits your team.

Level 1: Automatic wiring
-------------------------

Add two lines to your ``environment.py`` and every feature is wired
automatically:

.. code-block:: python

   from behave_kit import setup, teardown

   def before_all(context):
       setup(context, env="staging")

   def after_scenario(context, scenario):
       teardown(context)

That's it.  Soft assertions, context dump on failure, step suggestions,
fixtures, and scoped cleanup are all active.

Level 2: Cherry-pick
--------------------

Import only the utilities you need:

.. code-block:: python

   from behave_kit import assert_soft, env, load_data

   @then("the response should be valid")
   def step(context):
       assert_soft(context.response.status_code == 200)
       api_key = env("API_KEY", required=True)
       users = load_data("tests/data/users.csv")

No ``setup()`` call required — each utility works standalone.

Level 3: Namespace
------------------

Use the package as a namespace for clarity in large suites:

.. code-block:: python

   import behave_kit as bk

   @then("the response should be valid")
   def step(context):
       bk.assert_soft(context.response.status_code == 200)
       api_key = bk.env("API_KEY", required=True)

Examples
--------

Soft assertions
~~~~~~~~~~~~~~~

.. code-block:: python

   from behave_kit import use_soft_asserts, assert_soft

   @given("I have a soft assert collector active")
   def step(context):
       use_soft_asserts(context)

   @then("the response should be valid")
   def step(context):
       assert_soft(context.response.status_code == 200)
       assert_soft(context.response.body["count"] > 0)
       # Failures are accumulated, not raised immediately

TypedContext
~~~~~~~~~~~~

.. code-block:: python

   from behave_kit import TypedContext

   class MySchema:
       driver: str
       base_url: str

   @given("I have a typed context")
   def step(context):
       context.typed = TypedContext(context, MySchema)
       context.typed.setup(driver="chrome", base_url="https://test.com")

   @then('the driver should be "{driver}"')
   def step(context, driver):
       assert context.typed.driver == driver

Conditional skip
~~~~~~~~~~~~~~~~

.. code-block:: python

   from behave_kit import skip_if_env, skip_if_no_browser

   @when("I open the browser")
   @skip_if_no_browser
   def step(context):
       ...

   @when("I run the production-only step")
   @skip_if_env("production")
   def step(context):
       ...

Environment variables
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from behave_kit import env

   api_key = env("API_KEY", required=True)
   timeout = env("TIMEOUT", var_type=int, default=30)
   debug = env("DEBUG", var_type=bool, default=False)

Data loading
~~~~~~~~~~~~

.. code-block:: python

   from behave_kit import load_data

   users = load_data("tests/data/users.csv")      # list[dict]
   config = load_data("tests/data/config.json")   # dict
   sheet = load_data("tests/data/sheet.xlsx")     # list[dict] (requires [excel])

Fixtures
~~~~~~~~

.. code-block:: python

   from behave_kit import fixture

   @fixture("browser")
   def browser_fixture(context):
       def setup(ctx):
           ctx.browser = {"name": "chrome", "started": True}
       def teardown(ctx):
           ctx.browser = None
       return (setup, teardown)
