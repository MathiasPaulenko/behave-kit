Class-based steps
=================

Define Behave step implementations as methods on a class, with per-scenario
instances, lifecycle hooks, and per-step matcher selection.

Class-based steps are an alternative to Behave's function-based ``@given``,
``@when``, ``@then`` decorators.  Related steps live together on a class,
state is kept on ``self`` instead of ``context``, and standard Python
inheritance (subclassing, overriding, mixins) works as expected.

How it works
------------

1. Call :func:`behave_kit.step_impl_base` to create a fresh base class with
   its own local step registry.
2. Subclass it and decorate methods with ``@Base.given``, ``@Base.when``,
   ``@Base.then`` (or ``@Base.step``).
3. Call ``register()`` on the class to add the steps to Behave's global
   registry.
4. Wire ``teardown_steps(context)`` (or :func:`behave_kit.teardown`) in
   ``after_scenario`` so ``teardown()`` hooks run.

Basic example
--------------

.. code-block:: python

   from behave_kit import step_impl_base

   Base = step_impl_base()

   class AccountSteps(Base):
       @Base.given("I have a balance of {amount:d}")
       def set_balance(self, amount):
           self.balance = amount

       @Base.when("I deposit {amount:d}")
       def deposit(self, amount):
           self.balance += amount

       @Base.then("the balance should be {expected:d}")
       def check_balance(self, expected):
           assert self.balance == expected

       @property
       def balance(self):
           return getattr(self.context, "balance", 0)

       @balance.setter
       def balance(self, value):
           self.context.balance = value

   AccountSteps.register()

``self.context`` is bound automatically — no ``context`` parameter is needed
on step methods.  A fresh instance is created per scenario, so state on
``self`` is isolated between scenarios.

Lifecycle hooks
---------------

Define ``setup()`` and ``teardown()`` methods on the class to run code once
per scenario per class:

.. code-block:: python

   class DatabaseSteps(Base):
       def setup(self):
           self.connection = connect_to_test_db()

       def teardown(self):
           self.connection.close()

       @Base.given("a clean database")
       def clean_db(self):
           self.connection.execute("DELETE FROM users")

``setup()`` runs lazily — only when the first step of the class is called
in a scenario.  ``teardown()`` runs when ``teardown_steps(context)`` is
called (typically in ``after_scenario``).

Wiring teardown
~~~~~~~~~~~~~~~

**Automatic (via ``setup()`` / ``teardown()``):**

.. code-block:: python

   from behave_kit import setup, teardown

   def before_all(context):
       setup(context)

   def after_scenario(context, scenario):
       teardown(context)

**Manual:**

.. code-block:: python

   from behave_kit import teardown_steps

   def after_scenario(context, scenario):
       teardown_steps(context)

Subclassing and overriding
--------------------------

Subclass a step class to add, override, or extend steps.  Method overrides
are picked up automatically when the subclass is registered:

.. code-block:: python

   from some_library.steps import AccountSteps as Base

   class ExtendedAccountSteps(Base):
       def withdraw(self, amount):
           if amount > self.balance:
               raise ValueError("Insufficient funds")
           super().withdraw(amount)

       @Base.then("the balance should be positive")
       def check_positive(self):
           assert self.balance > 0

   # Register only the most-derived class.
   ExtendedAccountSteps.register()

Register only the most-derived class — its ``register()`` includes all
inherited steps with overrides applied.  Registering both parent and child
raises ``AmbiguousStep``.

Per-step matcher
----------------

Each step can use a different matcher without changing global state.  Pass
``matcher=`` to the decorator:

.. code-block:: python

   from behave.matchers import RegexMatcher

   class Steps(Base):
       @Base.then(
           r"the balance should be (less|greater) than (\d+)",
           matcher=RegexMatcher,
       )
       def compare(self, operator, amount):
           ...

Accepts a matcher class (e.g. ``RegexMatcher``, ``ParseMatcher``) or a
name string (``"parse"``, ``"re"``, ``"cfparse"``).

A default matcher for all steps in a base can be set via
``step_impl_base(default_matcher="re")``.

Idempotent registration
-----------------------

``register()`` is idempotent — calling it twice on the same class is a
no-op.  ``clear()`` removes previously registered steps from Behave's
global registry:

.. code-block:: python

   AccountSteps.register()
   AccountSteps.register()  # no-op
   AccountSteps.clear()     # removes the steps

Independent libraries
---------------------

Each call to ``step_impl_base()`` creates an isolated local registry, so
independent step libraries can coexist without interfering with each
other:

.. code-block:: python

   BaseA = step_impl_base()
   BaseB = step_impl_base()

   class StepsA(BaseA): ...
   class StepsB(BaseB): ...

   StepsA.register()
   StepsB.register()  # no conflict — separate registries

Limitations
-----------

- Async step methods (``async def``) are not supported.  Use the
  function-based ``@given`` / ``@when`` / ``@then`` decorators for async
  steps.
- ``__init__`` must not require arguments (use default values for any
  configuration).

API reference
-------------

.. autofunction:: behave_kit.steps.classes.step_impl_base

.. autofunction:: behave_kit.steps.classes.teardown_steps
