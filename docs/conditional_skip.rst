Conditional Skip
================

Skip steps based on environment, OS, or missing dependencies — without
writing manual ``if/else`` guards in every step.

Decorators
----------

behave-kit provides four skip decorators that raise ``unittest.SkipTest``
when the condition is not met, causing Behave to mark the step as skipped
rather than failed.

skip_if_env
~~~~~~~~~~~

Skip a step when the current environment matches a given name:

.. code-block:: python

   from behave_kit import skip_if_env

   @skip_if_env("production")
   @when("I run the staging-only step")
   def step(context):
       # This step is skipped when context.config.env == "production"
       ...

You can also skip on multiple environments by stacking decorators:

.. code-block:: python

   @skip_if_env("production")
   @skip_if_env("ci")
   @when("I run the local-only step")
   def step(context):
       ...

skip_on_os
~~~~~~~~~~

Skip a step on specific operating systems:

.. code-block:: python

   from behave_kit import skip_on_os

   @skip_on_os("windows")
   @when("I run the unix-only step")
   def step(context):
       ...

   @skip_on_os("linux")
   @when("I run the windows-only step")
   def step(context):
       ...

skip_if_missing
~~~~~~~~~~~~~~~

Skip a step when a Python module is not installed:

.. code-block:: python

   from behave_kit import skip_if_missing

   @skip_if_missing("selenium")
   @when("I use selenium webdriver")
   def step(context):
       from selenium import webdriver
       ...

   @skip_if_missing("requests")
   @when("I make an HTTP request")
   def step(context):
       import requests
       ...

skip_if_no_browser
~~~~~~~~~~~~~~~~~~

Skip a step when no browser is available (checks for Selenium):

.. code-block:: python

   from behave_kit import skip_if_no_browser

   @skip_if_no_browser
   @when("I open the browser")
   def step(context):
       from selenium import webdriver
       context.browser = webdriver.Chrome()
       ...

API reference
-------------

.. autofunction:: behave_kit.skip.decorators.skip_if_env

.. autofunction:: behave_kit.skip.decorators.skip_on_os

.. autofunction:: behave_kit.skip.decorators.skip_if_missing

.. autofunction:: behave_kit.skip.decorators.skip_if_no_browser

Conditions
----------

The condition functions used by the decorators are also available standalone:

.. autofunction:: behave_kit.skip.conditions.is_env

.. autofunction:: behave_kit.skip.conditions.is_os

.. autofunction:: behave_kit.skip.conditions.is_missing

.. autofunction:: behave_kit.skip.conditions.is_no_browser

Examples
--------

Environment-based skip
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # environment.py
   from behave_kit import setup

   def before_all(context):
       setup(context, env="staging")

   # steps/api_steps.py
   from behave_kit import skip_if_env

   @skip_if_env("production")
   @when("I reset the database")
   def step(context):
       context.db.reset()

   @skip_if_env("staging")
   @when("I run the production smoke test")
   def step(context):
       ...

Feature-level skip
~~~~~~~~~~~~~~~~~~

Apply the decorator to every step in a feature by using a shared step
function:

.. code-block:: python

   from behave_kit import skip_if_env

   @skip_if_env("production")
   @given("the test database is ready")
   def step(context):
       context.db = create_test_db()

Conditional steps with @when_if
--------------------------------

For more flexible conditional execution, use `@when_if` which runs a step
only when a condition function returns ``True``:

.. code-block:: python

   from behave_kit import when_if

   @when_if(lambda ctx: ctx.config.env == "staging")
   @when("I run the staging-only step")
   def step(context):
       ...

   @when_if(lambda ctx: hasattr(ctx, "browser"))
   @when("I take a screenshot")
   def step(context):
       context.browser.save_screenshot("screenshot.png")

API reference
~~~~~~~~~~~~~

.. autofunction:: behave_kit.steps.conditional.when_if
