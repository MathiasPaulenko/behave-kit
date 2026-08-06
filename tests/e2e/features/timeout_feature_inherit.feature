@timeout:10
Feature: Feature-level timeout inherits to scenarios
  As a behave-kit developer
  I want to verify that feature-level timeout tags inherit to scenarios
  So that all scenarios in a feature share the same timeout

  Scenario: Scenario inherits feature timeout and passes
    When a step sleeps for 3 seconds
    Then the scenario should pass without timeout

  @timeout:1
  Scenario: Scenario overrides feature timeout and fails
    When a step sleeps for 2 seconds
