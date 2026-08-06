Per-scenario timeout
====================

Behave provides a global ``--timeout`` flag but no way to set a different
timeout per scenario.  ``behave-kit`` fills that gap with tag-based overrides
and platform-aware handlers.

Overview
--------

1. ``setup_timeout`` configures a default timeout on the context.
2. Tags ``@timeout:N`` override the timeout per scenario or feature.
3. On expiry the scenario fails with ``TimeoutError``.

Platform notes
~~~~~~~~~~~~~~

- **Unix** (Linux, macOS): uses ``signal.SIGALRM`` for immediate
  interruption of the main thread.
- **Windows**: ``signal.SIGALRM`` is unavailable, so a
  ``threading.Timer`` fallback is used.  This cannot interrupt
  CPU-bound code — the timeout is detected after the current step
  finishes.  I/O-bound code (``time.sleep``, socket reads, etc.) is
  interrupted promptly.

Usage
-----

Wire the timeout hooks in your ``environment.py``:

.. code-block:: python

   from behave_kit import setup_timeout
   from behave_kit.timeout import timeout_before_scenario, timeout_after_scenario

   def before_all(context):
       setup_timeout(context, default_timeout=30)

   def before_scenario(context, scenario):
       timeout_before_scenario(context, scenario)

   def after_scenario(context, scenario):
       timeout_after_scenario(context, scenario)

Tag-based overrides
-------------------

Override the default timeout per scenario or feature using ``@timeout:N``
tags:

.. code-block:: gherkin

   @timeout:10
   Scenario: Fast scenario with tag override
     When I do something quick

   @timeout:0
   Scenario: Disable timeout for this scenario
     When I do something slow

   @timeout:60
   Feature: Feature-level timeout inherits to all scenarios

Precedence rules:

- Scenario tags take precedence over feature tags.
- ``@timeout:0`` disables the timeout for that scenario.
- If no tag is present, the default timeout from ``setup_timeout`` is used.
- If no default is configured (``default_timeout=0``), no timeout is applied.

Custom tag name
~~~~~~~~~~~~~~~

Use a custom tag name instead of the default ``timeout``:

.. code-block:: python

   setup_timeout(context, default_timeout=30, timeout_tag="limit")

Tags would then be ``@limit:10``, ``@limit:0``, etc.

API reference
-------------

.. automodule:: behave_kit.timeout
   :members:
