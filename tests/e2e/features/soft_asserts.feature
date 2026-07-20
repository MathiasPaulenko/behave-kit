Feature: Soft assertions
  As a behave-kit developer
  I want to verify that soft assertions work correctly
  So that assertions are accumulated without stopping execution

  Scenario: Soft assertions pass when conditions are true
    Given I have a soft assert collector active
    When I assert that "True" is soft-true
    And I assert that "True" is soft-true with message "should not fail"
    Then the soft assert collector should have 0 failures

  Scenario: Soft assertions accumulate failures
    Given I have a soft assert collector active
    When I assert that "False" is soft-true with message "first failure"
    And I assert that "False" is soft-true with message "second failure"
    Then the soft assert collector should have 2 failures
    And I clear the soft assert failures
