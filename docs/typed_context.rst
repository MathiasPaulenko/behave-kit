TypedContext
============

Schema-validated proxy over the Behave context with IDE autocompletion and
mypy support.

The problem
-----------

In raw Behave, context attributes are dynamically set:

.. code-block:: python

   @given("I have a browser")
   def step(context):
       context.driver = "chrome"
       context.base_url = "https://test.com"

   @then('the driver should be "{driver}"')
   def step(context, driver):
       assert context.driver == driver  # no autocompletion, no type checking

This works but has drawbacks:

- No IDE autocompletion for ``context.driver``
- No mypy type checking
- Typos in attribute names are silently ignored
- No schema enforcement — any attribute can be set

The solution
------------

`TypedContext` wraps the Behave context with a schema class that declares
which attributes are allowed and their types:

.. code-block:: python

   from behave_kit import TypedContext

   class MySchema:
       driver: str
       base_url: str

   ctx = TypedContext(context, MySchema)
   ctx.setup(driver="chrome", base_url="https://test.com")
   print(ctx.driver)  # IDE autocompletion works, mypy validates the type

Accessing an undeclared attribute raises a `ScopeError`:

.. code-block:: python

   ctx.undeclared_attr  # raises ScopeError

API reference
-------------

.. autoclass:: behave_kit.context.typed.TypedContext
   :members:

.. autofunction:: behave_kit._core.errors.ScopeError

Examples
--------

Basic usage
~~~~~~~~~~~

.. code-block:: python

   from behave_kit import TypedContext

   class UserSchema:
       name: str
       email: str
       age: int

   @given("I have a user with name {name} and email {email}")
   def step(context, name, email):
       ctx = TypedContext(context, UserSchema)
       ctx.setup(name=name, email=email, age=30)

   @then("the user name should be {name}")
   def step(context, name):
       ctx = TypedContext(context, UserSchema)
       assert ctx.name == name

Rejecting undeclared attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   @when('I try to access "{attr}" from the typed context')
   def step(context, attr):
       ctx = TypedContext(context, UserSchema)
       try:
           getattr(ctx, attr)
           context._scope_error = None
       except ScopeError as exc:
           context._scope_error = exc

   @then("it should raise a ScopeError")
   def step(context):
       assert context._scope_error is not None

Setting attributes via setup()
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The `setup()` method validates that all keys are declared in the schema:

.. code-block:: python

   ctx = TypedContext(context, UserSchema)
   ctx.setup(name="Alice", email="alice@example.com", age=30)  # OK
   ctx.setup(name="Alice", unknown="value")  # raises ScopeError

Partial setup
~~~~~~~~~~~~~

You can set only some attributes — the rest remain unset:

.. code-block:: python

   ctx = TypedContext(context, UserSchema)
   ctx.setup(name="Alice")
   # ctx.email and ctx.age are not set yet
   ctx.setup(email="alice@example.com")
   # now ctx.name and ctx.email are set, ctx.age is still unset

Integration with hooks
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from behave_kit import TypedContext

   class AppSchema:
       base_url: str
       api_key: str
       timeout: int

   def before_all(context):
       context.typed = TypedContext(context, AppSchema)
       context.typed.setup(
           base_url="https://api.example.com",
           api_key="secret",
           timeout=30,
       )

   @when("I make an API request")
   def step(context):
       url = context.typed.base_url  # autocompletion + type safety
       key = context.typed.api_key
       timeout = context.typed.timeout
