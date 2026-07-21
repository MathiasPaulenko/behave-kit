Continue After Failed
====================

Control whether scenarios keep executing remaining steps after a step fails.

By default, Behave stops a scenario at the first failing step.  This is
useful for fast failure feedback, but it hides downstream problems that
would only surface after the failing step.  ``continue_after_failed``
flips the default so the full scenario runs and every failure is
reported — ideal for comprehensive test reports and CI diagnostics.

How it works
------------

The feature sets the class-level attribute
``Scenario.continue_after_failed_step`` which Behave checks before
aborting a scenario on step failure.  When set to ``True``, Behave
records the failure and continues with the next step.

Global toggle
-------------

.. autofunction:: behave_kit.continue_after_failed.continue_after_failed
   :no-index:

Examples
~~~~~~~~

.. code-block:: python

   from behave_kit import continue_after_failed

   # Enable globally — every scenario continues after a failed step.
   continue_after_failed(True)

   # Disable (restore Behave's default behaviour).
   continue_after_failed(False)

The setting applies to all scenarios that run while it is enabled.

Temporary toggle with continue_on_failure
-----------------------------------------

.. autofunction:: behave_kit.continue_after_failed.continue_on_failure
   :no-index:

Use it as a context manager to scope the change to a block of code:

.. code-block:: python

   from behave_kit import continue_on_failure

   with continue_on_failure():
       # Any scenario that runs inside this block will continue
       # after failed steps.
       run_feature("features/smoke.feature")

   # Outside the block, the previous setting is restored, even if
   # an exception was raised inside the ``with`` block.

Wiring through setup()
----------------------

Pass ``continue_after_failed=True`` to :func:`behave_kit.setup` to enable
it as part of the automatic wiring:

.. code-block:: python

   from behave_kit import setup

   def before_all(context):
       setup(context, continue_after_failed=True)

When wired through ``setup()``, :func:`behave_kit.teardown` resets
``Scenario.continue_after_failed_step`` to ``False`` at the end of the
run so the setting does not leak between test sessions.

Interaction with soft assertions
--------------------------------

``continue_after_failed`` and soft assertions are complementary:

- **Soft assertions** collect multiple assertion failures within a
  *single step* and report them together.
- **Continue after failed** lets the *scenario* keep running after a
  step fails, so you see failures across multiple steps.

Combined, they give you the most complete picture of what is broken in
a scenario.

Validation
----------

``continue_after_failed()`` validates that ``enabled`` is a boolean,
preventing silent falsy values like ``None`` or ``0`` from being
interpreted as ``False``:

.. code-block:: python

   from behave_kit import continue_after_failed
   from behave_kit._core.errors import BehaveKitError

   try:
       continue_after_failed(None)  # type: ignore[arg-type]
   except BehaveKitError:
       # Raises: "enabled must be a boolean, got NoneType"
       pass
