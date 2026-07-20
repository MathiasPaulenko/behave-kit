Soft Assertions
===============

Collect multiple assertion failures and report them all at once, instead of
stopping at the first one.

This is one of the most valuable features of behave-kit: when a scenario
checks several conditions, you see **every** failure, not just the first.

How it works
------------

Soft assertions use `contextvars` to track an active `SoftAssertCollector`.
Each call to `assert_soft()` records a failure (if the condition is falsy)
without raising.  At the end of the scenario, `raise_if_failed()` raises an
`AssertionError` with a formatted report of every failure.

Activating soft asserts
~~~~~~~~~~~~~~~~~~~~~~~

**Automatic (via `setup()`):**

.. code-block:: python

   from behave_kit import setup

   def before_all(context):
       setup(context, env="staging")

Soft asserts are activated automatically and reset per scenario.

**Manual:**

.. code-block:: python

   from behave_kit import use_soft_asserts

   def before_scenario(context, scenario):
       use_soft_asserts(context)

**Context manager (for unit tests):**

.. code-block:: python

   from behave_kit import soft_asserts

   with soft_asserts() as collector:
       assert_soft(1 == 2, "one should equal two")
       assert_soft(3 == 3, "three should equal three")
   # AssertionError raised here with all failures

API reference
-------------

.. autofunction:: behave_kit.assertions.soft.assert_soft

.. autofunction:: behave_kit.assertions.soft.assert_soft_equals

.. autofunction:: behave_kit.assertions.soft.assert_soft_true

.. autofunction:: behave_kit.assertions.soft.assert_soft_is_none

.. autofunction:: behave_kit.assertions.soft.use_soft_asserts

.. autofunction:: behave_kit.assertions.soft.soft_asserts

.. autoclass:: behave_kit.assertions.soft.SoftAssertCollector
   :members:

.. autoclass:: behave_kit.assertions.reporter.SoftAssertReport
   :members:

.. autoclass:: behave_kit.assertions.reporter.SoftFailure
   :members:

Examples
--------

Basic usage
~~~~~~~~~~~

.. code-block:: python

   from behave_kit import assert_soft

   @then("the API response should be valid")
   def step(context):
       response = context.response
       assert_soft(response.status_code == 200, "status code should be 200")
       assert_soft("error" not in response.body, "body should not contain 'error'")
       assert_soft(response.body["count"] > 0, "count should be positive")
       # All failures collected, reported together at teardown

With equality checks
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from behave_kit import assert_soft_equals

   @then("the user profile should match")
   def step(context):
       assert_soft_equals(context.user["name"], "Alice", "name mismatch")
       assert_soft_equals(context.user["email"], "alice@example.com", "email mismatch")
       assert_soft_equals(context.user["age"], 30, "age mismatch")

Checking for None
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from behave_kit import assert_soft_is_none

   @then("no error should be present")
   def step(context):
       assert_soft_is_none(context.error, "error should be None")
       assert_soft_is_none(context.warning, "warning should be None")

Inspecting the report
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from behave_kit import use_soft_asserts, assert_soft

   @given("I have a soft assert collector active")
   def step(context):
       collector = use_soft_asserts(context)
       context.collector = collector

   @then("the soft assert collector should have {count:d} failures")
   def step(context, count):
       assert len(context.collector.failures) == count

Clearing failures
~~~~~~~~~~~~~~~~~

.. code-block:: python

   @then("I clear the soft assert failures")
   def step(context):
       context._behave_kit_soft._failures.clear()

Diff-based assertions
---------------------

In addition to soft asserts, behave-kit provides diff-based comparison
assertions that show **exactly which fields differ** instead of a bare
``AssertionError``.

assert_json_equals
~~~~~~~~~~~~~~~~~~

Deep-compare two objects and report every difference:

.. code-block:: python

   from behave_kit import assert_json_equals, CompareOptions

   @then("the response body should match the expected JSON")
   def step(context):
       expected = {"name": "Alice", "age": 30, "roles": ["admin", "user"]}
       assert_json_equals(context.response.body, expected)

With options:

.. code-block:: python

   from behave_kit import assert_json_equals, CompareOptions

   @then("the response should match ignoring timestamps")
   def step(context):
       opts = CompareOptions(ignore_keys=frozenset({"created_at", "updated_at"}))
       assert_json_equals(context.response.body, context.expected, options=opts)

Ignoring order in lists:

.. code-block:: python

   opts = CompareOptions(ignore_order=True)
   assert_json_equals(actual_list, expected_list, options=opts)

assert_dict_contains
~~~~~~~~~~~~~~~~~~~~

Assert that a dict contains every key/value pair from a subset:

.. code-block:: python

   from behave_kit import assert_dict_contains

   @then("the response should contain the expected fields")
   def step(context):
       assert_dict_contains(
           context.response.body,
           {"status": "ok", "count": 5},
       )

assert_list_ordered
~~~~~~~~~~~~~~~~~~~

Assert that a list is sorted:

.. code-block:: python

   from behave_kit import assert_list_ordered

   @then("the results should be sorted by name")
   def step(context):
       assert_list_ordered(context.results, key=lambda item: item["name"])

assert_table_equals
~~~~~~~~~~~~~~~~~~~

Compare two Behave data tables:

.. code-block:: python

   from behave_kit import assert_table_equals

   @then("the data table should match")
   def step(context):
       assert_table_equals(context.table, context.expected_table)

Deep comparison engine
~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: behave_kit.assertions._matchers.deep_compare

.. autoclass:: behave_kit.assertions._matchers.CompareOptions
   :members:

.. autoclass:: behave_kit.assertions._matchers.DiffResult
   :members:

.. autoclass:: behave_kit.assertions._matchers.Diff
   :members:

CompareOptions supports:

- ``ignore_keys`` — skip specific keys during comparison
- ``float_tolerance`` — tolerance for floating-point comparisons (default: 1e-9)
- ``ignore_order`` — treat lists as unordered sets
- ``datetime_tolerance`` — tolerance for datetime comparisons
- ``custom_matchers`` — per-type custom comparison functions

.. code-block:: python

   from behave_kit import CompareOptions, deep_compare
   from datetime import timedelta

   opts = CompareOptions(
       ignore_keys=frozenset({"id", "timestamp"}),
       float_tolerance=0.01,
       datetime_tolerance=timedelta(seconds=5),
       custom_matchers={
           MyModel: lambda actual, expected: actual.id == expected.id,
       },
   )
   result = deep_compare(actual_data, expected_data, opts)
   if not result.equal:
       for diff in result.diffs:
           print(f"  at {diff.path}: {diff.message}")
