Step Utilities
==============

Custom parameter types, conditional steps, and "did you mean?" suggestions
for undefined steps.

Custom parameter types
----------------------

Register converters for custom step parameters:

.. autofunction:: behave_kit.steps.parameters.parameter_type

.. autofunction:: behave_kit.steps.parameters.convert

.. autofunction:: behave_kit.steps.parameters.register_builtin_types

Built-in types
~~~~~~~~~~~~~~

behave-kit ships converters for common types.  Call `register_builtin_types()`
once to register them all:

.. code-block:: python

   from behave_kit import register_builtin_types

   def before_all(context):
       register_builtin_types()

Registered types are usable both via ``convert()`` and as ``{name:Type}``
placeholders in Behave step patterns (parse/cfparse matchers).

Available built-in types:

- ``int`` — integer conversion
- ``float`` — float conversion
- ``date`` — ISO date (``YYYY-MM-DD``)
- ``datetime`` — ISO datetime
- ``decimal`` — `Decimal` for exact numeric comparisons
- ``email`` — validated email address
- ``url`` — validated HTTP/HTTPS URL

Custom parameter type example
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from behave_kit import parameter_type, convert
   from dataclasses import dataclass

   @dataclass
   class User:
       name: str
       email: str

   @parameter_type("User", r'[\w.]+@[\w.]+')
   def parse_user(text: str) -> User:
       name, domain = text.split("@")
       return User(name=name, email=text)

   @when('I log in as "{user:User}"')
   def step(context, user):
       # user is a User instance, not a raw string
       assert isinstance(user, User)
       context.current_user = user

Using convert() directly
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from behave_kit import convert

   email = convert("email", "alice@example.com")  # validated string
   port = convert("int", "8080")                   # 8080 as int
   url = convert("url", "https://example.com")     # validated URL

Conditional steps with @when_if
-------------------------------

Run a step only when a condition function returns ``True``:

.. autofunction:: behave_kit.steps.conditional.when_if

Examples
~~~~~~~~

.. code-block:: python

   from behave_kit import when_if
   from behave_kit.skip.conditions import is_env

   @when("I run the staging-only step")
   @when_if(lambda ctx: is_env(ctx, "staging"))
   def step(context):
       ...

   @when("I take a screenshot")
   @when_if(lambda ctx: hasattr(ctx, "browser"))
   def step(context):
       context.browser.save_screenshot("debug.png")

   @when("I reset the test database")
   @when_if(lambda ctx: not is_env(ctx, "production"))
   def step(context):
       context.db.reset()

When the condition is ``False``, the step is silently skipped (Behave marks
it as skipped, not failed).

Data-driven steps with @data_driven
------------------------------------

Run a step once per row of a data file (CSV, JSON, YAML, Excel).  Column
names are sanitized to valid Python identifiers and injected as keyword
arguments.  ``@data_driven`` must be placed *inside* (below) the Behave
step decorator so Behave registers the wrapped function:

.. autofunction:: behave_kit.steps.data_driven.data_driven

Examples
~~~~~~~~

.. code-block:: python

   from behave_kit import data_driven

   @when("I login with the test credentials")
   @data_driven("tests/data/users.csv")
   def step(context, username, password):
       login(username, password)
   # Runs once per row in users.csv

Given ``tests/data/users.csv``:

.. code-block:: text

   username,password
   alice,secret
   bob,pass123

The step is called twice with ``username="alice", password="secret"`` and
``username="bob", password="pass123"``.

Column name sanitization
~~~~~~~~~~~~~~~~~~~~~~~~

Column names with hyphens or spaces are converted to valid Python
identifiers:

.. code-block:: text

   user-name,pass word
   alice,secret

The step receives ``user_name`` and ``pass_word`` as keyword arguments.

Using JSON or YAML
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   @when("I process each item")
   @data_driven("tests/data/items.json")
   def step(context, id, name):
       process(id, name)

The file must contain a list of dictionaries (or a single dict that will be
wrapped in a list).

Step suggestions
----------------

When a step is undefined, behave-kit suggests the closest registered step
patterns using `difflib`:

.. autofunction:: behave_kit.steps.suggestions.setup_suggestions

.. autofunction:: behave_kit.steps.suggestions.suggest_for_undefined

Wiring suggestions
~~~~~~~~~~~~~~~~~~

Behave hooks cannot be injected — the returned ``after_step`` hook must be
called explicitly.  ``setup()`` attaches it to ``context.kit_suggestions``:

**Automatic (via `setup()`):**

.. code-block:: python

   from behave_kit import setup

   def before_all(context):
       setup(context, env="staging")

   def after_step(context, step):
       context.kit_suggestions(context, step)

**Manual:**

.. code-block:: python

   from behave_kit import setup_suggestions

   def before_all(context):
       context._suggest = setup_suggestions(context)

   def after_step(context, step):
       context._suggest(context, step)

Example output
~~~~~~~~~~~~~~

When a step is undefined, you'll see a log message like:

.. code-block:: text

   INFO: Step 'I clikc the button' has not been defined. Did you mean: 'I click the button'?

This helps developers quickly identify typos in step definitions without
searching through all registered steps.
