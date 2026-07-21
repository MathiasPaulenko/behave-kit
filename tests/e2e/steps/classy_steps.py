"""E2E step implementations using class-based steps (behave_kit.step_impl_base)."""

from __future__ import annotations

from behave import given, then  # type: ignore[import-not-found]
from behave.matchers import RegexMatcher

from behave_kit import step_impl_base

# --- Class-based step library ---


AccountBase = step_impl_base()


class AccountSteps(AccountBase):
    """Class-based steps for a bank account, with state on ``self``."""

    @AccountBase.given("a class-based account with a balance of {amount:d}")
    def set_balance(self, amount: int) -> None:
        self.balance = amount

    @AccountBase.when("I deposit {amount:d} into the class-based account")
    def deposit(self, amount: int) -> None:
        self.balance += amount

    @AccountBase.then("the class-based balance should be {expected:d}")
    def check_balance(self, expected: int) -> None:
        assert self.balance == expected, f"Expected {expected}, got {self.balance}"

    @AccountBase.then("the class-based account setup hook should have run")
    def check_setup_ran(self) -> None:
        assert getattr(self.context, "account_setup_ran", False), "Setup hook did not run"

    @AccountBase.then("the class-based account teardown hook should not have run yet")
    def check_teardown_not_yet(self) -> None:
        assert not getattr(self.context, "account_teardown_ran", False), (
            "Teardown hook ran too early"
        )

    # Uses the default matcher (Parse) — verifies default_matcher=None path.
    @AccountBase.then("the class-based balance should be exactly {expected:d}")
    def check_balance_exact(self, expected: int) -> None:
        assert self.balance == expected, f"Expected exactly {expected}, got {self.balance}"

    @property
    def balance(self) -> int:
        return getattr(self.context, "classy_balance", 0)

    @balance.setter
    def balance(self, value: int) -> None:
        self.context.classy_balance = value

    def setup(self) -> None:
        self.context.account_setup_ran = True

    def teardown(self) -> None:
        self.context.account_teardown_ran = True


class ExtendedAccountSteps(AccountSteps):
    """Subclass that overrides withdraw to check sufficient funds."""

    @AccountBase.when("I withdraw {amount:d} from the extended class-based account")
    def withdraw(self, amount: int) -> None:
        if amount > self.balance:
            self.context.withdrawal_error = "Insufficient funds"
            return
        self.balance -= amount

    @AccountBase.then('the withdrawal should be rejected with "{message}"')
    def check_rejection(self, message: str) -> None:
        actual = getattr(self.context, "withdrawal_error", None)
        assert actual == message, f"Expected rejection {message!r}, got {actual!r}"

    @AccountBase.given("an extended class-based account with a balance of {amount:d}")
    def set_balance_extended(self, amount: int) -> None:
        self.balance = amount

    @AccountBase.then(
        r"the class-based balance should be (less|greater) than (or equal to )*(\d+)",
        matcher=RegexMatcher,
    )
    def compare_balance(self, operator: str, or_equals: str, amount: str) -> None:
        value = int(amount)
        if operator == "less":
            if or_equals:
                assert self.balance <= value
            else:
                assert self.balance < value
        elif or_equals:
            assert self.balance >= value
        else:
            assert self.balance > value


# A second class-based library using the SAME base — exercises multi-class
# coexistence within one scenario (each class gets its own instance).
class CartSteps(AccountBase):
    """Class-based steps for a shopping cart, sharing the account base."""

    @AccountBase.given("a class-based cart has an item priced {price:d}")
    def add_item(self, price: int) -> None:
        self.context.cart_item_price = price

    @AccountBase.when("I add the class-based cart item to the order")
    def add_to_order(self) -> None:
        # Read the account balance from context (set by AccountSteps.balance setter).
        account_balance = getattr(self.context, "classy_balance", 0)
        self.context.order_total = getattr(self.context, "order_total", 0)
        self.context.order_total += self.context.cart_item_price + account_balance

    @AccountBase.then("the class-based order total should be {expected:d}")
    def check_order_total(self, expected: int) -> None:
        actual = getattr(self.context, "order_total", 0)
        assert actual == expected, f"Expected order total {expected}, got {actual}"


# An independent step library using a SEPARATE base — verifies that two
# step_impl_base() calls produce isolated registries that coexist.
IndependentBase = step_impl_base()


class IndependentLibrarySteps(IndependentBase):
    @IndependentBase.given("an independent library step has run")
    def step_one(self) -> None:
        self.context.independent_library_ran = True

    @IndependentBase.then("the independent library flag should be set")
    def check_flag(self) -> None:
        assert getattr(self.context, "independent_library_ran", False)


# Register the class-based steps into Behave's global registry.
# Only the most-derived class is registered so overrides take effect
# and all inherited steps are included without ambiguity.
ExtendedAccountSteps.register()
CartSteps.register()
IndependentLibrarySteps.register()


# --- Verification steps (function-based, to assert on class-based behavior) ---


@given("a class-based account is ready")
def step_classy_account_ready(context: object) -> None:
    # The class-based steps handle everything; this is just a marker.
    pass


@then("the class-based account teardown hook should have run")
def step_verify_teardown_ran(context: object) -> None:
    assert getattr(context, "account_teardown_ran", False), "Teardown hook did not run"


# --- Function-based steps to verify coexistence with class-based steps ---


@given("a function-based marker step has run")
def step_function_marker_run(context: object) -> None:
    context.function_marker_ran = True


@then("the function-based marker should be visible")
def step_function_marker_visible(context: object) -> None:
    assert getattr(context, "function_marker_ran", False), "Function marker did not run"
