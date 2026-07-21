Feature: Continue after failed step
  As a behave-kit developer
  I want to verify that continue_after_failed changes Behave's stop-on-failure behaviour
  So that scenarios can keep running remaining steps after a failure

  Scenario: continue_after_failed is enabled globally
    Given continue_after_failed is set to true
    Then the Scenario class should have continue_after_failed_step set to true
    And continue_after_failed is restored to false

  Scenario: continue_on_failure context manager enables temporarily
    Given the Scenario class has continue_after_failed_step set to false
    When I enter a continue_on_failure block
    Then the Scenario class should have continue_after_failed_step set to true
    And after exiting the block it should be restored to false

  Scenario: continue_on_failure restores on exception
    Given the Scenario class has continue_after_failed_step set to false
    When I enter a continue_on_failure block that raises ValueError
    Then the Scenario class should have continue_after_failed_step set to false
