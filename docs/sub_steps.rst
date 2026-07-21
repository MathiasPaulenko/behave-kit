Sub-step Execution
==================

Execute Gherkin sub-steps from within a step with Scenario Outline
variable substitution and guaranteed state isolation.

Behave's ``context.execute_steps()`` lets you compose steps from other
steps, but it has two rough edges:

- ``context.table`` and ``context.text`` are mutated by the sub-steps
  and not restored, leaking state into the parent step.
- Scenario Outline placeholders (``<name>``) are not substituted, so
  sub-steps can't reference the current outline row's values.

:func:`behave_kit.run_steps` wraps ``execute_steps`` to fix both.

run_steps
---------

.. autofunction:: behave_kit.context.substeps.run_steps
   :no-index:

Basic usage
~~~~~~~~~~~

.. code-block:: python

   from behave_kit import run_steps

   @when("I complete the checkout flow")
   def step_impl(context):
       run_steps(context, '''
           Given I have items in my cart
           When I enter shipping info
           Then I should see the order confirmation
       ''')

The sub-steps are executed in order.  If any sub-step fails, Behave
raises an ``AssertionError`` describing which step failed, and the
exception propagates out of ``run_steps``.

Scenario Outline substitution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When the calling scenario is part of a Scenario Outline,
``run_steps`` substitutes ``<placeholder>`` patterns with the values
from ``context.active_outline``:

.. code-block:: gherkin

   Scenario Outline: Checkout in <city>
     When I complete the checkout flow for "<city>"
     Then the shipping address should be in "<city>"

     Examples:
       | city   |
       | Berlin |
       | Paris  |

.. code-block:: python

   @when('I complete the checkout flow for "{city}"')
   def step_impl(context, city):
       run_steps(context, '''
           Given I have items in my cart
           When I enter shipping info for "<city>"
           Then I should see the order confirmation
       ''')

The ``<city>`` placeholder in the sub-step text is replaced with the
current outline row's value (e.g. ``Berlin``) before the sub-steps are
executed.

State isolation
---------------

``run_steps`` saves and restores ``context.table`` and ``context.text``
around the sub-step execution, so the parent step's values are
preserved:

.. code-block:: python

   @when("I run a composite step")
   def step_impl(context):
       # context.table is set by the parent step.
       original_table = context.table

       run_steps(context, '''
           Given a sub-step that uses a table
       ''')
       # The sub-step's table (if any) does not leak out.

       assert context.table is original_table

Validation
----------

``run_steps`` validates its inputs before delegating to Behave:

- ``steps`` must be a non-empty string (after stripping whitespace).
  Empty or whitespace-only input raises ``AssertionError``.
- ``context.active_outline`` must be a ``dict`` when present.  A list
  or string raises ``AssertionError`` with a clear message.
- ``context.execute_steps`` must be callable.  If it isn't (e.g.
  ``run_steps`` is called outside a Behave context), ``SubStepError``
  is raised.

SubStepError
------------

.. autoexception:: behave_kit.context.substeps.SubStepError
   :members:
   :no-index:

Raised when sub-step execution fails or ``run_steps`` is used outside
a feature context.

Example error:

.. code-block:: text

   behave_kit.context.substeps.SubStepError: run_steps() requires a
   Behave context with execute_steps(); called outside a feature.
