Feature: Class-based steps
  As a behave-kit developer
  I want to define Behave steps as methods on a class
  So that related steps stay grouped and share state via self

  Scenario: Class-based steps share state via self
    Given a class-based account with a balance of 100
    When I deposit 42 into the class-based account
    Then the class-based balance should be 142

  Scenario: Class-based steps setup hook runs once per scenario
    Given a class-based account with a balance of 50
    Then the class-based account setup hook should have run

  Scenario: Subclass override is used at run time
    Given an extended class-based account with a balance of 50
    When I withdraw 100 from the extended class-based account
    Then the withdrawal should be rejected with "Insufficient funds"

  Scenario: Per-step regex matcher works
    Given a class-based account with a balance of 100
    When I deposit 10 into the class-based account
    Then the class-based balance should be less than 1000
    And the class-based balance should be greater than or equal to 1

  Scenario: Teardown hook runs after the scenario
    Given a class-based account with a balance of 100
    When I deposit 1 into the class-based account
    Then the class-based account teardown hook should not have run yet

  Scenario: Multiple class-based step classes coexist in one scenario
    Given a class-based account with a balance of 100
    And a class-based cart has an item priced 30
    When I deposit 10 into the class-based account
    And I add the class-based cart item to the order
    Then the class-based order total should be 140

  Scenario: Class-based steps coexist with function-based steps
    Given a class-based account with a balance of 100
    And a function-based marker step has run
    When I deposit 5 into the class-based account
    Then the class-based balance should be 105
    And the function-based marker should be visible

  Scenario: Teardown runs between scenarios so state does not leak
    Given a class-based account with a balance of 100
    When I deposit 1 into the class-based account
    Then the class-based balance should be 101

  Scenario: State from the previous scenario is reset
    Given a class-based account with a balance of 200
    Then the class-based balance should be 200

  Scenario: Subclass extends parent via super
    Given an extended class-based account with a balance of 50
    When I withdraw 20 from the extended class-based account
    Then the class-based balance should be 30

  Scenario: Default matcher on the base class is applied
    Given a class-based account with a balance of 100
    Then the class-based balance should be exactly 100

  Scenario: Independent step libraries coexist
    Given a class-based account with a balance of 100
    And an independent library step has run
    Then the class-based balance should be 100

