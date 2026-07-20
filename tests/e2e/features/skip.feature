Feature: Conditional skip
  As a behave-kit developer
  I want to verify that skip_if_env works correctly
  So that steps are skipped on the right environment

  Scenario: Step is skipped on test environment
    When I run a step that skips on env "test"
    Then the step should be skipped

  Scenario: Step runs when env does not match
    When I run a step that skips on env "ci"
    Then the step should not be skipped
