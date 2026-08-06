Feature: Per-scenario timeout
  As a behave-kit developer
  I want to verify that per-scenario timeout works correctly
  So that scenarios exceeding their time limit fail with TimeoutError

  Scenario: Scenario within default timeout passes
    When a step completes instantly
    Then the scenario should pass without timeout

  @timeout:10
  Scenario: Scenario with tag override that passes
    When a step sleeps for 3 seconds
    Then the scenario should pass without timeout

  @timeout:1
  Scenario: Scenario exceeds tag timeout and fails
    When a step sleeps for 2 seconds

  Scenario: Scenario exceeds default timeout and fails
    When a step sleeps for 3 seconds

  @timeout:0
  Scenario: Tag timeout zero disables timeout
    When a step sleeps for 3 seconds
    Then the scenario should pass without timeout
