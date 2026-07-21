Utilities
=========

General-purpose utilities for polling, dict navigation, time assertions, and
temporary workspaces.

wait_until — polling with timeout
----------------------------------

.. autofunction:: behave_kit.wait.wait_until

Poll a condition until it becomes truthy or the timeout elapses.  Common in
E2E and integration tests where a resource (API, database, browser) is not
immediately available after an action.

Examples
~~~~~~~~

.. code-block:: python

   from behave_kit import wait_until

   @then("the API should be healthy")
   def step(context):
       wait_until(
           lambda: context.client.get("/health").status_code == 200,
           timeout=10,
           interval=0.5,
       )

Custom timeout message:

.. code-block:: python

   wait_until(
       lambda: context.db.is_ready(),
       timeout=30,
       message="Database did not become ready in time",
   )

The condition callable can return any truthy value, including array-like
objects (NumPy arrays are supported via scalar-bool coercion).

get_path — dot-notation dict navigation
-----------------------------------------

.. autofunction:: behave_kit.utils.get_path

Navigate nested dicts and lists using dot notation.  Supports list indices
and optional defaults.

Examples
~~~~~~~~

.. code-block:: python

   from behave_kit import get_path

   data = {
       "user": {
           "name": "Alice",
           "address": {"city": "Berlin"},
       },
       "users": [
           {"name": "Alice"},
           {"name": "Bob"},
       ],
   }

   get_path(data, "user.name")                # "Alice"
   get_path(data, "user.address.city")        # "Berlin"
   get_path(data, "users.0.name")             # "Alice"
   get_path(data, "users.1.name")             # "Bob"
   get_path(data, "user.phone", default="")   # "" (missing key, returns default)

When a key or index is missing and no default is provided, a
``BehaveKitError`` is raised with a descriptive message:

.. code-block:: python

   get_path(data, "user.missing")  # raises BehaveKitError: Key 'missing' not found

Time assertions — assert_under and @timed
------------------------------------------

.. autofunction:: behave_kit.timing.assert_under

.. autofunction:: behave_kit.timing.timed

.. autoclass:: behave_kit.timing.TimeoutExceededError
   :members:

``assert_under`` verifies that a callable completes within a deadline.
``@timed`` is a decorator that wraps a Behave step function with the same
check.

Examples
~~~~~~~~

.. code-block:: python

   from behave_kit import assert_under, timed

   # Direct usage
   result = assert_under(2.0, lambda: client.get("/health"))
   assert result.status_code == 200

   # As a step decorator
   @timed(1.5)
   @when("I fetch the data quickly")
   def step(context):
       context.data = fetch_data()

If the callable takes longer than the allowed time, a
``TimeoutExceededError`` (subclass of ``BehaveKitError``) is raised:

.. code-block:: python

   from behave_kit import assert_under, TimeoutExceededError

   try:
       assert_under(0.5, lambda: slow_operation())
   except TimeoutExceededError as exc:
       print(f"Too slow: {exc}")

temp_workspace — isolated temporary directory
----------------------------------------------

.. autofunction:: behave_kit.workspace.temp_workspace

Create a temporary directory, change the CWD into it, and restore the
original CWD on exit.  The directory is removed automatically.

Examples
~~~~~~~~

.. code-block:: python

   from behave_kit import temp_workspace

   @when("I create a temporary workspace")
   def step(context):
       with temp_workspace() as tmp:
           config_path = tmp / "config.json"
           config_path.write_text('{"debug": true}')
           context.config_dir = tmp
       # CWD is restored and the directory is cleaned up

The CWD is restored even if an exception is raised inside the block:

.. code-block:: python

   with temp_workspace() as tmp:
       raise ValueError("oops")
   # Original CWD is restored
