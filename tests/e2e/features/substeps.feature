Feature: Sub-step execution with isolation
  As a behave-kit developer
  I want to verify that run_steps executes sub-steps with state isolation
  So that table/text are preserved and outline variables are substituted

  Scenario: run_steps delegates to execute_steps
    Given a feature context is active
    When I run steps "Given a sub-step marker is set" via run_steps
    Then the execute_steps call should contain "Given a sub-step marker is set"

  Scenario: run_steps restores table after execution
    Given a feature context is active with table "original_table"
    When I run steps "Given a sub-step marker is set" via run_steps
    Then the context table should be "original_table"

  Scenario: run_steps restores text after execution
    Given a feature context is active with text "original text"
    When I run steps "Given a sub-step marker is set" via run_steps
    Then the context text should be "original text"

  Scenario: run_steps substitutes outline variables
    Given a feature context is active with outline user "admin"
    When I run steps "Given I log in as <user>" via run_steps
    Then the execute_steps call should contain "Given I log in as admin"

  Scenario: run_steps restores table even on sub-step failure
    Given a feature context is active with table "protected_table" and failing execute
    When I run steps "Given a failing sub-step" via run_steps
    Then the context table should be "protected_table"
    And a sub-step error should have been caught

  Scenario: run_steps outside feature raises SubStepError
    Given no feature context is active
    When I try to run steps "Given something" via run_steps
    Then a SubStepError should be raised with message "outside of a feature"

  Scenario: run_steps with non-string input raises SubStepError
    Given a feature context is active
    When I try to run steps with non-string input via run_steps
    Then a SubStepError should be raised with message "must be a string"
