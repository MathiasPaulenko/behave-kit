"""Class-based step implementations with per-scenario instances.

This module provides an alternative to Behave's function-based step
decorators (`@given`, `@when`, `@then`) that lets you organise step
implementations as methods on a class.  Each scenario gets a fresh
instance with the Behave ``context`` exposed as ``self.context``, so
state can be kept on ``self`` instead of polluting ``context``.

Features:

* Step definitions live on a class as methods — group related steps together.
* Subclassing and method overriding work as usual Python inheritance.
* A per-step matcher can be selected without changing global state.
* ``self.context`` is bound automatically — no ``context`` parameter needed.
* ``setup()`` / ``teardown()`` hooks run once per scenario per class.
* ``register()`` is idempotent; ``clear()`` removes previously registered steps.

Usage::

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

Wire the teardown hook in ``environment.py`` so ``teardown()`` methods run::

    from behave_kit import setup, teardown

    def before_all(context):
        setup(context)

    def after_scenario(context, scenario):
        teardown(context)
"""

from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from behave_kit._core.errors import StepError
from behave_kit._core.logging import get_logger
from behave_kit._core.types import Context

logger = get_logger("steps.classes")

_INSTANCES_KEY = "_behave_kit_step_instances"
_KEYWORDS: tuple[str, ...] = ("given", "when", "then", "step")


@dataclass
class _StepEntry:
    """A step definition recorded in a local registry."""

    keyword: str
    pattern: str
    func_name: str
    matcher: Any  # None | str | Matcher subclass


@dataclass
class _RegistrationRecord:
    """Tracks the matchers a class has added to Behave's global registry."""

    matchers: list[Any] = field(default_factory=list)


# Per-class registration records — powers ``register()`` idempotency and ``clear()``.
_registration_records: dict[type, _RegistrationRecord] = {}


def _resolve_matcher_class(matcher: Any) -> type | None:
    """Return a Matcher subclass from ``matcher`` (``None`` | ``str`` | class)."""
    if matcher is None:
        return None
    if isinstance(matcher, type):
        return matcher
    if isinstance(matcher, str):
        from behave.matchers import StepMatcherFactory

        mapping: dict[str, type] = StepMatcherFactory.make_step_matcher_class_mapping()
        if matcher not in mapping:
            raise StepError(
                f"Unknown step matcher '{matcher}'",
                suggestion=f"Available matchers: {', '.join(sorted(mapping))}",
            )
        return mapping[matcher]
    raise StepError(
        "matcher must be None, a matcher name, or a Matcher subclass",
        suggestion=(
            f"Got {type(matcher).__name__}; use one of: None, 'parse', 're', 'cfparse', "
            "or a Matcher class"
        ),
    )


def _build_matcher(entry: _StepEntry, func: Callable[..., Any]) -> Any:
    """Construct a step matcher for ``func`` according to ``entry``.

    When ``entry.matcher`` is ``None``, defers to Behave's
    ``add_step_definition`` path (caller responsibility) and returns
    ``None``.  Otherwise builds the matcher directly using the resolved
    matcher class — this avoids mutating Behave's global current-matcher
    state and supports custom matcher classes that aren't in the
    default name mapping.

    The matcher is validated by calling ``compile()`` (mirroring
    Behave's ``is_good_step_definition``), so malformed patterns
    fail at registration time with a clear error instead of being
    silently added and failing at match time.
    """
    matcher_class = _resolve_matcher_class(entry.matcher)
    if matcher_class is None:
        return None
    matcher_obj = matcher_class(func, entry.pattern, step_type=entry.keyword)
    # Validate the pattern early — Behave's add_step_definition does this
    # via is_good_step_definition().  Without it, a malformed regex would
    # be silently added and only fail at match time with a confusing error.
    try:
        matcher_obj.compile()
    except Exception as error:  # noqa: BLE001
        raise StepError(
            f"Invalid step pattern for {entry.keyword} step '{entry.pattern}': {error}",
            suggestion=(
                "Check the pattern syntax for the chosen matcher "
                "(e.g. RegexMatcher requires valid regex, ParseMatcher uses {name:type} syntax)"
            ),
        ) from error
    return matcher_obj


def _add_matcher_to_registry(entry: _StepEntry, matcher_obj: Any) -> Any:
    """Append ``matcher_obj`` to Behave's global registry with dedup/ambiguity checks.

    Mirrors the essential validation of
    :meth:`behave.step_registry.StepRegistry.add_step_definition`:
    skips exact duplicates and raises ``AmbiguousStep`` on conflicting
    patterns.  Returns the matcher if it was added, ``None`` if deduped.
    """
    from behave.runner import the_step_registry
    from behave.step_registry import AmbiguousStep
    from behave.textutil import text as _text

    step_list = the_step_registry.steps[entry.keyword]
    pattern = _text(entry.pattern)
    for existing in step_list:
        if existing is matcher_obj:
            return None  # exact same object — already registered
        if existing.pattern == matcher_obj.pattern and matcher_obj.location == existing.location:
            return None  # same step definition — dedup
        if existing.matches(pattern):
            raise AmbiguousStep(
                f"{matcher_obj.describe()} has already been defined in\n"
                f"  existing step {existing.describe(existing.SCHEMA_AT_LOCATION)}"
            )
    step_list.append(matcher_obj)
    return matcher_obj


def _make_step_wrapper(cls: type, func_name: str) -> Callable[..., Any]:
    """Wrap a method so it runs on a per-scenario instance with ``context`` bound."""
    method = getattr(cls, func_name, None)
    if method is None:
        raise StepError(
            f"Step method '{func_name}' is not defined on {cls.__name__}",
            suggestion="Ensure the method is defined on the class or one of its bases",
        )
    if inspect.iscoroutinefunction(method):
        raise StepError(
            f"Async step method '{func_name}' is not supported by step_impl_base",
            suggestion="Use the function-based @given/@when/@then decorators for async steps",
        )

    @functools.wraps(method)
    def wrapper(context: Context, *args: Any, **kwargs: Any) -> Any:
        """Bind a per-scenario instance and call the step method on it."""
        instances: dict[type, Any] | None = getattr(context, _INSTANCES_KEY, None)
        if instances is None:
            instances = {}
            setattr(context, _INSTANCES_KEY, instances)
        instance = instances.get(cls)
        if instance is None:
            instance = cls()
            instance.context = context
            # Cache the instance BEFORE calling setup() so that:
            # 1. Subsequent steps don't re-create and re-fail if setup() raises.
            # 2. teardown_steps() can call teardown() for resource cleanup
            #    even when setup() failed.
            instances[cls] = instance
            setup_fn = getattr(instance, "setup", None)
            if callable(setup_fn):
                setup_fn()
        bound = getattr(instance, func_name)
        return bound(*args, **kwargs)

    return wrapper


def teardown_steps(context: Context) -> None:
    """Call ``teardown()`` on every live step-instance for ``context`` and clear them.

    Safe to call when no class-based steps have run (no-op).  Wired
    automatically by :func:`behave_kit.setup` / :func:`behave_kit.teardown`.

    Iterates over a snapshot of the instances dict so that a
    ``teardown()`` method that triggers additional step execution
    (which could add new instances) does not cause
    ``RuntimeError: dictionary changed size during iteration``.
    """
    instances = getattr(context, _INSTANCES_KEY, None)
    if not instances:
        return
    for instance in list(instances.values()):
        teardown_fn = getattr(instance, "teardown", None)
        if callable(teardown_fn):
            try:
                teardown_fn()
            except Exception:
                logger.exception("teardown() failed for %r", type(instance).__name__)
    instances.clear()


def step_impl_base(default_matcher: Any = None) -> type:
    """Return a new base class for class-based step implementations.

    Each call creates an isolated local step registry, so independent
    step libraries can coexist without interfering with each other.
    Subclasses share the registry of the base they derive from, which
    is what enables extension via subclassing and method overriding.

    Args:
        default_matcher: Default matcher for steps that don't specify one.
            Accepts ``None`` (Behave's current default), a string name
            (``"parse"``, ``"re"``, ``"cfparse"``, ``"simplified"``,
            ``"cucumber"``), or a Matcher subclass.

    Returns:
        A base class with ``given``, ``when``, ``then``, ``step``
        decorator factories and ``register()`` / ``clear()`` methods.

    Raises:
        StepError: If ``default_matcher`` is not a valid matcher reference.
    """
    local_registry: list[_StepEntry] = []
    default_matcher_class = _resolve_matcher_class(default_matcher)

    def _make_decorator(keyword: str) -> Callable[..., Callable[..., Any]]:
        def decorator(
            pattern: str,
            *,
            matcher: Any = None,
        ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
            """Record ``func`` as a ``keyword`` step matching ``pattern``.

            Args:
                pattern: Step text pattern (uses Behave's current matcher syntax).
                matcher: Optional per-step matcher (``None``, name, or class).
                    Overrides the base's ``default_matcher`` for this step.
            """
            resolved = matcher if matcher is not None else default_matcher_class

            def wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
                local_registry.append(_StepEntry(keyword, pattern, func.__name__, resolved))
                return func

            return wrapper

        return decorator

    decorators = {kw: _make_decorator(kw) for kw in _KEYWORDS}

    class _StepImplBase:
        """Base class for class-based Behave step implementations.

        Subclass this and decorate methods with ``@Base.given``,
        ``@Base.when``, ``@Base.then`` (or ``@Base.step``).  Call
        ``register()`` on the class to add the steps to Behave's global
        registry.  ``self.context`` is bound to the Behave context
        automatically before any step method runs.
        """

        # Type hint for IDEs/mypy — set per-scenario before any step runs.
        context: Context

        # Step decorators.  Exposed as static methods so they don't bind
        # to instances (they're meant to be used at class-definition time
        # via ``Base.given(...)``).
        given = staticmethod(decorators["given"])
        when = staticmethod(decorators["when"])
        then = staticmethod(decorators["then"])
        step = staticmethod(decorators["step"])
        Given = staticmethod(decorators["given"])
        When = staticmethod(decorators["when"])
        Then = staticmethod(decorators["then"])
        Step = staticmethod(decorators["step"])

        def setup(self) -> None:
            """Hook called once when the instance is created for a scenario.

            Override in subclasses to perform per-scenario initialisation.
            The default implementation does nothing.
            """

        def teardown(self) -> None:
            """Hook called after the scenario ends (via :func:`teardown_steps`).

            Override in subclasses to perform per-scenario cleanup.
            The default implementation does nothing.
            """

        @classmethod
        def register(cls) -> None:
            """Add this class's step definitions to Behave's global registry.

            Each entry in the local registry is resolved via the MRO of
            ``cls``, so overrides in subclasses are picked up.  Idempotent:
            calling ``register()`` twice on the same class is a no-op.

            Raises:
                StepError: If a step method is missing or async.
                AmbiguousStep: If a step pattern conflicts with an existing one.
            """
            if cls in _registration_records:
                return  # already registered — idempotent

            from behave.runner import the_step_registry

            # Record the class BEFORE the loop so that ``clear()`` can
            # clean up any matchers that were added before a failure.
            # Without this, a partial registration on AmbiguousStep
            # would orphan matchers in the global registry.
            record = _RegistrationRecord()
            _registration_records[cls] = record
            try:
                for entry in local_registry:
                    if not hasattr(cls, entry.func_name):
                        # The class doesn't implement this step — skip it.
                        # This lets users register a subclass that only
                        # partially overrides a library without errors.
                        logger.debug(
                            "Skipping %s '%s': %s has no method '%s'",
                            entry.keyword,
                            entry.pattern,
                            cls.__name__,
                            entry.func_name,
                        )
                        continue

                    wrapper = _make_step_wrapper(cls, entry.func_name)
                    matcher_obj = _build_matcher(entry, wrapper)
                    if matcher_obj is None:
                        # No specific matcher — use Behave's default path so
                        # the current matcher (e.g. set via use_step_matcher)
                        # is respected and built-in validation runs.
                        before = len(the_step_registry.steps[entry.keyword])
                        the_step_registry.add_step_definition(entry.keyword, entry.pattern, wrapper)
                        added = the_step_registry.steps[entry.keyword][before:]
                        record.matchers.extend(added)
                    else:
                        added = _add_matcher_to_registry(entry, matcher_obj)
                        if added is not None:
                            record.matchers.append(added)
            except Exception:
                # On failure, remove the record and any matchers that
                # were already added so the class can be re-registered
                # cleanly after the conflict is resolved.
                for matcher_obj in record.matchers:
                    for step_list in the_step_registry.steps.values():
                        while matcher_obj in step_list:
                            step_list.remove(matcher_obj)
                del _registration_records[cls]
                raise

        @classmethod
        def clear(cls) -> None:
            """Remove previously registered step matchers from Behave's global registry.

            No-op if ``register()`` was never called for ``cls``.
            """
            from behave.runner import the_step_registry

            record = _registration_records.pop(cls, None)
            if record is None:
                return
            for matcher_obj in record.matchers:
                for step_list in the_step_registry.steps.values():
                    while matcher_obj in step_list:
                        step_list.remove(matcher_obj)

    return _StepImplBase
