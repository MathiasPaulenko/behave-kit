Feature: Fixtures by tags
  As a behave-kit developer
  I want to verify that fixtures are set up and torn down by tag
  So that fixture lifecycle is automatic

  @browser
  Scenario: Browser fixture is set up and torn down
    Given a browser fixture is registered
    When I run a scenario with the "browser" tag
    Then the browser fixture should be set up
    And the browser fixture should be torn down after the scenario
